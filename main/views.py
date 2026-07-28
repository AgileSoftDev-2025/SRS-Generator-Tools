import json
import base64
import requests
import urllib.parse
import subprocess
import binascii

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.contrib import messages

from .models import (
    Project, Pengguna, Session, GUI, Usecase,
    UserStory, UserStoryScenario, UseCaseSpecification,
    BasicPath, AlternativePath, ExceptionPath,
    Sequence, ClassDiagram, ActivityDiagram,
    Page, Element, ImportedTable, ImportedRelationship,
    TestScenario, TestStep, Feature
)
from .forms import RegisterForm
from .parsers.sql_parser import parse_sql_file
from .utils import save_parsed_sql_to_db
from main.generators.sequence_generator import build_sequence_plantuml
from main.generators.class_diagram_generator import generate_class_diagram


# ============================================================
# HELPERS: PROJECT ISOLATION
# ============================================================

GUEST_USER_ID = 'U0001'
GUEST_USER_NAME = 'Guest'
GUEST_USER_EMAIL = 'guest@local.app'


def get_or_create_guest_user():
    """Buat atau ambil satu Default Guest User untuk semua project tanpa login."""
    user, _ = Pengguna.objects.get_or_create(
        id_user=GUEST_USER_ID,
        defaults={
            'nama_user': GUEST_USER_NAME,
            'email_user': GUEST_USER_EMAIL,
            'password': 'not-used',
        }
    )
    return user


def get_active_project(request):
    """
    Ambil project yang sedang aktif dari session.
    Mengembalikan None jika tidak ada project aktif — tidak ada fallback global.
    View yang memerlukan project aktif wajib memeriksa nilai None dan redirect ke home.
    """
    project_id = request.session.get('active_project_id')
    if project_id:
        project = Project.objects.filter(id_project=project_id).first()
        if project:
            return project
    # SENGAJA tidak ada fallback Project.objects.last() — mencegah kebocoran data antar project
    return None


def set_active_project(request, project):
    """
    Simpan project yang sedang aktif ke session.
    Membersihkan semua state session project sebelumnya agar tidak ada kebocoran data.
    """
    old_project_id = request.session.get('active_project_id')
    if old_project_id and old_project_id != project.id_project:
        # Hapus session data yang terikat project lama
        old_key = f'all_use_case_data_{old_project_id}'
        request.session.pop(old_key, None)

    request.session['active_project_id'] = project.id_project


# ============================================================
# HOME & PROJECT MANAGEMENT
# ============================================================

def home(request):
    """
    Dashboard utama. Tidak perlu login.
    Menampilkan semua project milik guest user dari DB (bukan localStorage).
    """
    pengguna = get_or_create_guest_user()
    projects = Project.objects.filter(pengguna=pengguna).order_by('-tanggal_akses_terakhir')
    active_project = get_active_project(request)

    # FIX-01: Kirim projects sebagai JSON ke template agar frontend
    # render dari DB, bukan dari localStorage yang stale
    projects_data = []
    for p in projects:
        projects_data.append({
            'id': p.id_project,
            'name': p.nama_project,
            'description': p.deskripsi or '',
            'created_at': p.tanggal_project_dibuat.isoformat() if p.tanggal_project_dibuat else '',
        })

    return render(request, 'main/home.html', {
        'projects': projects,
        'active_project': active_project,
        'projects_json': json.dumps(projects_data),
    })


def project_new(request):
    """Buat project baru, langsung set sebagai active project, dan redirect ke workflow."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        desc = request.POST.get('description', '').strip()

        if not name:
            return redirect('main:home')

        pengguna = get_or_create_guest_user()

        with transaction.atomic():
            project = Project.objects.create(
                nama_project=name,
                deskripsi=desc,
                pengguna=pengguna,
                tanggal_project_dibuat=timezone.now(),
                tanggal_akses_terakhir=timezone.now(),
            )

            # PHASE 1 FIX: Auto-buat GUI default agar use_case_diagram
            # selalu punya scope data yang terisolasi untuk project ini.
            # Tanpa ini, GUI.objects.filter(project=project).first() → None
            # dan sistem bisa bocor ke data orphan project lama.
            gui_id = f"G{project.id_project}"
            GUI.objects.create(
                id_gui=gui_id,
                project=project,
                nama_atribut=name,
            )

        # Set session SETELAH transaction commit agar konsisten
        set_active_project(request, project)

        # Redirect langsung ke workflow, bukan ke home
        return redirect('main:use_case_diagram')

    return redirect('main:home')


def project_detail(request, id_project):
    """
    Buka project tertentu. Otomatis set project ini sebagai aktif di session,
    sehingga semua halaman berikutnya menampilkan data project ini.
    """
    project = get_object_or_404(Project, id_project=id_project)

    # Update waktu akses terakhir
    project.tanggal_akses_terakhir = timezone.now()
    project.save(update_fields=['tanggal_akses_terakhir'])

    # Set sebagai active project di session
    set_active_project(request, project)

    return redirect('main:use_case_diagram')


# ============================================================
# STEP 1: USE CASE DIAGRAM
# ============================================================

def use_case_diagram(request):
    project = get_active_project(request)
    if not project:
        # RC-01 fix: paksa user ke dashboard untuk memilih project
        return redirect('main:home')

    # Ambil data UserStory project aktif untuk di-load di frontend
    actors_data = []
    gui = GUI.objects.filter(project=project).first()
    if gui:
        stories = UserStory.objects.filter(gui=gui)
        actors_map = {}
        for story in stories:
            if story.input_sebagai not in actors_map:
                actors_map[story.input_sebagai] = []

            feat = {"what": story.input_fitur}
            if story.input_tujuan:
                feat["why"] = story.input_tujuan
            actors_map[story.input_sebagai].append(feat)

        for actor_name, features in actors_map.items():
            actors_data.append({
                "name": actor_name,
                "features": features
            })

    context = {
        'actors_json': json.dumps(actors_data)
    }
    return render(request, 'main/use_case_diagram.html', context)


@csrf_exempt
@require_http_methods(["POST", "GET"])
@transaction.atomic
def save_actors_and_features(request):
    """
    Simpan Actor & Feature untuk project yang sedang aktif.
    Hanya menghapus data project aktif, bukan semua data.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project = get_active_project(request)

            if not project:
                return JsonResponse({'status': 'error', 'message': 'Tidak ada project aktif. Buka project dari dashboard terlebih dahulu.'}, status=400)

            # Ambil atau buat GUI untuk project ini
            gui, _ = GUI.objects.get_or_create(
                project=project,
                defaults={
                    'id_gui': f"G{project.id_project}",
                    'nama_atribut': project.nama_project
                }
            )

            # Bersihkan data LAMA hanya untuk project aktif ini
            UserStory.objects.filter(gui=gui).delete()

            feature_map = {}

            for actor in data:
                actor_name = actor.get('name')
                features = actor.get('features', [])

                for feat in features:
                    feature_name = feat.get('what')
                    feature_purpose = feat.get('why')

                    # Simpan User Story — RC-03 fix: isi field project langsung
                    UserStory.objects.create(
                        project=project,
                        input_sebagai=actor_name,
                        input_fitur=feature_name,
                        input_tujuan=feature_purpose,
                        gui=gui,
                    )

                    # Kumpulkan fitur unik
                    if feature_name not in feature_map:
                        feature_map[feature_name] = {'actors': [], 'purpose': feature_purpose}

                    if actor_name not in feature_map[feature_name]['actors']:
                        feature_map[feature_name]['actors'].append(actor_name)

            # Preservasi UseCaseSpecification yang sudah ada agar detail spec & paths tidak terhapus saat re-save fitur
            current_feature_names = set(feature_map.keys())
            UseCaseSpecification.objects.filter(project=project).exclude(feature_name__in=current_feature_names).delete()

            saved_count = 0
            for feat_name, info in feature_map.items():
                actors_str = ", ".join(info['actors'])
                purpose_text = f" so that {info['purpose']}" if info['purpose'] else ""
                default_summary = f"Users ({actors_str}) want to {feat_name}{purpose_text}"

                spec = UseCaseSpecification.objects.filter(project=project, feature_name=feat_name).first()
                if spec:
                    spec.gui = gui
                    if not spec.summary_description:
                        spec.summary_description = default_summary
                    spec.save()
                else:
                    UseCaseSpecification.objects.create(
                        project=project,
                        gui=gui,
                        feature_name=feat_name,
                        summary_description=default_summary,
                        priority="Must Have",
                        status="Active"
                    )
                saved_count += 1

            return JsonResponse({
                'status': 'success',
                'message': f'Berhasil! {saved_count} fitur unik disimpan.'
            })

        except Exception as e:
            print(f"❌ Error Save: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=400)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def generate_usecase_diagram(request):
    """Generate diagram use case untuk project aktif."""
    try:
        project = get_active_project(request)
        if not project:
            return JsonResponse({'status': 'error', 'message': 'Tidak ada project aktif. Buka project dari dashboard terlebih dahulu.'}, status=400)

        # RC-02 fix: selalu scope ke project aktif, tidak ada fallback GUI.objects.last()
        current_gui = GUI.objects.filter(project=project).first()

        if not current_gui:
            return JsonResponse({'status': 'error', 'message': 'GUI not found. Pastikan sudah memilih project aktif.'}, status=404)

        stories = UserStory.objects.filter(gui=current_gui)
        if not stories.exists():
            return JsonResponse({'status': 'error', 'message': 'Belum ada User Story! Input dulu.'}, status=400)

        plantuml = ["@startuml", "left to right direction", "skinparam packageStyle rectangle"]
        defined_actors = set()

        for story in stories:
            actor_clean = story.input_sebagai.replace(" ", "_")
            if actor_clean not in defined_actors:
                plantuml.append(f'actor "{story.input_sebagai}" as {actor_clean}')
                defined_actors.add(actor_clean)
            plantuml.append(f'{actor_clean} --> ({story.input_fitur})')

        plantuml.append("@enduml")
        final_code = "\n".join(plantuml)

        encoded_code = urllib.parse.quote(final_code)
        plantuml_url = f"http://www.plantuml.com/plantuml/png/{encoded_code}"
        response = requests.get(plantuml_url, timeout=15)

        if response.status_code == 200:
            diagram, _ = Usecase.objects.update_or_create(
                gui=current_gui,
                defaults={'plantuml_code': final_code}
            )
            file_name = f"usecase_{current_gui.id_gui}.png"
            if diagram.hasil_usecase:
                diagram.hasil_usecase.delete(save=False)
            diagram.hasil_usecase.save(file_name, ContentFile(response.content), save=True)

            return JsonResponse({
                'status': 'success',
                'message': 'Diagram berhasil digenerate!',
                'image_url': diagram.hasil_usecase.url
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Gagal konek ke PlantUML'}, status=500)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============================================================
# STEP 2: USER STORY
# ============================================================

def user_story(request):
    project = get_active_project(request)
    if not project:
        # RC-01 fix: paksa user ke dashboard untuk memilih project
        return redirect('main:home')

    usecases_data = []
    plantuml_code = ""
    gui = GUI.objects.filter(project=project).first()
    if gui:
        stories = UserStory.objects.filter(gui=gui)
        for story in stories:
            usecases_data.append({
                "actor": story.input_sebagai,
                "feature": story.input_fitur,
                "purpose": story.input_tujuan or ""
            })

        diagram = Usecase.objects.filter(gui=gui).first()
        if diagram and diagram.plantuml_code:
            plantuml_code = diagram.plantuml_code

    context = {
        'usecases_json': json.dumps(usecases_data),
        'plantuml_code': plantuml_code
    }
    return render(request, 'main/user_story.html', context)


def get_latest_userstory(request):
    """API: Ambil ID UserStory terbaru untuk project aktif."""
    try:
        project = get_active_project(request)
        if not project:
            return JsonResponse({"status": "error", "message": "Tidak ada project aktif."})
        # RC-02 fix: scope ke project aktif, tidak ada fallback global
        gui = GUI.objects.filter(project=project).first()
        if not gui:
            return JsonResponse({"status": "error", "message": "No User Story found"})
        us = UserStory.objects.filter(gui=gui).latest("id_userstory")
        return JsonResponse({"status": "success", "userstory_id": us.id_userstory})
    except Exception:
        return JsonResponse({"status": "error", "message": "No User Story found"})


# ============================================================
# STEP 3: INPUT INFORMASI TAMBAHAN (Use Case Spec)
# ============================================================

def input_informasi_tambahan(request):
    """
    Tampilkan form Use Case Spec untuk project aktif.
    Jika project baru, specs akan kosong.
    """
    project = get_active_project(request)

    if project:
        specs = UseCaseSpecification.objects.filter(project=project).prefetch_related(
            'basic_paths', 'alternative_paths', 'exception_paths'
        )
        if not specs.exists():
            # Inisialisasi otomatis jika belum ada UseCaseSpecification tetapi UserStory sudah dibuat
            gui = GUI.objects.filter(project=project).first()
            if gui:
                stories = UserStory.objects.filter(gui=gui)
                feature_map = {}
                for story in stories:
                    feat_name = story.input_fitur
                    feat_purpose = story.input_tujuan
                    actor_name = story.input_sebagai
                    if feat_name not in feature_map:
                        feature_map[feat_name] = {'actors': [], 'purpose': feat_purpose}
                    if actor_name not in feature_map[feat_name]['actors']:
                        feature_map[feat_name]['actors'].append(actor_name)

                for feat_name, info in feature_map.items():
                    actors_str = ", ".join(info['actors'])
                    purpose_text = f" so that {info['purpose']}" if info['purpose'] else ""
                    UseCaseSpecification.objects.create(
                        project=project,
                        gui=gui,
                        feature_name=feat_name,
                        summary_description=f"Users ({actors_str}) want to {feat_name}{purpose_text}",
                        priority="Must Have",
                        status="Active"
                    )
                specs = UseCaseSpecification.objects.filter(project=project).prefetch_related(
                    'basic_paths', 'alternative_paths', 'exception_paths'
                )
    else:
        specs = UseCaseSpecification.objects.none()

    use_cases_list = []
    for spec in specs:
        def get_paths(path_manager):
            return [{'actor': p.actor_action or '', 'system': p.system_response or ''} for p in path_manager.all().order_by('step_number')]

        use_cases_list.append({
            'id': spec.id,
            'name': spec.feature_name,
            'summary': spec.summary_description or "",
            'priority': spec.priority,
            'status': spec.status,
            'precondition': spec.input_precondition or "",
            'postcondition': spec.input_postcondition or "",
            'basicPath': get_paths(spec.basic_paths),
            'alternativePath': get_paths(spec.alternative_paths),
            'exceptionPath': get_paths(spec.exception_paths),
            'actors': []
        })

    context = {'use_cases_json': json.dumps(use_cases_list)}
    return render(request, 'main/input_informasi_tambahan.html', context)


@csrf_exempt
def save_usecase_spec(request):
    """Simpan Use Case Spec ke database, terikat ke project aktif."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project = get_active_project(request)
            if not project:
                return JsonResponse({'status': 'error', 'message': 'Tidak ada project aktif. Buka project dari dashboard terlebih dahulu.'}, status=400)

            saved_count = 0
            for key, item in data.items():
                spec, _ = UseCaseSpecification.objects.update_or_create(
                    feature_name=item.get('featureName', 'No Name'),
                    project=project,
                    defaults={
                        'summary_description': item.get('summary', ''),
                        'priority': item.get('priority', 'Must Have'),
                        'status': item.get('status', 'Active'),
                        'input_precondition': item.get('precondition', ''),
                        'input_postcondition': item.get('postcondition', ''),
                    }
                )

                spec.basic_paths.all().delete()
                spec.alternative_paths.all().delete()
                spec.exception_paths.all().delete()

                for index, path in enumerate(item.get('basicPath', []), start=1):
                    if path.get('actor') or path.get('system'):
                        BasicPath.objects.create(usecase_spec=spec, step_number=index, actor_action=path.get('actor', ''), system_response=path.get('system', ''))

                for index, path in enumerate(item.get('alternativePath', []), start=1):
                    if path.get('actor') or path.get('system'):
                        AlternativePath.objects.create(usecase_spec=spec, step_number=index, actor_action=path.get('actor', ''), system_response=path.get('system', ''))

                for index, path in enumerate(item.get('exceptionPath', []), start=1):
                    if path.get('actor') or path.get('system'):
                        ExceptionPath.objects.create(usecase_spec=spec, step_number=index, actor_action=path.get('actor', ''), system_response=path.get('system', ''))

                saved_count += 1

            return JsonResponse({'status': 'success', 'message': f'Berhasil simpan {saved_count} fitur!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# Alias untuk kompatibilitas URL lama
def save_usecase_spec_to_db(request):
    return save_usecase_spec(request)


# ============================================================
# STEP 4: USE CASE SPEC (View Only)
# ============================================================

def use_case_spec(request):
    """Tampilkan Use Case Spec untuk project aktif (read-only view)."""
    project = get_active_project(request)

    if project:
        specs = UseCaseSpecification.objects.filter(project=project).prefetch_related(
            'basic_paths', 'alternative_paths', 'exception_paths'
        )
    else:
        specs = UseCaseSpecification.objects.none()

    use_cases_data = []
    for spec in specs:
        use_cases_data.append({
            'featureName': spec.feature_name,
            'summary': spec.summary_description or '',
            'priority': spec.priority,
            'status': spec.status,
            'precondition': spec.input_precondition or '',
            'postcondition': spec.input_postcondition or '',
            'basicPath': [{'actor': bp.actor_action or '', 'system': bp.system_response or ''} for bp in spec.basic_paths.all().order_by('step_number')],
            'alternativePath': [{'actor': ap.actor_action or '', 'system': ap.system_response or ''} for ap in spec.alternative_paths.all().order_by('step_number')],
            'exceptionPath': [{'actor': ep.actor_action or '', 'system': ep.system_response or ''} for ep in spec.exception_paths.all().order_by('step_number')],
        })

    context = {'all_features': json.dumps(use_cases_data)}
    return render(request, 'main/use_case_spec.html', context)


# ============================================================
# STEP 5: ACTIVITY DIAGRAM
# ============================================================

def activity_diagram(request):
    project = get_active_project(request)
    if not project:
        return redirect('main:home')

    # RC-04 fix: session key di-scope per project
    session_key = f'all_use_case_data_{project.id_project}'
    all_features = request.session.get(session_key, [])

    # Selalu load dari DB project aktif sebagai sumber kebenaran utama
    all_features = []
    specs = UseCaseSpecification.objects.filter(project=project).prefetch_related(
        'basic_paths', 'alternative_paths', 'exception_paths'
    )
    for spec in specs:
        all_features.append({
            'featureName': spec.feature_name,
            'summary': spec.summary_description or '',
            'precondition': spec.input_precondition or '',
            'postcondition': spec.input_postcondition or '',
            'basicPath': [{'actor': p.actor_action or '', 'system': p.system_response or ''} for p in spec.basic_paths.all().order_by('step_number')],
            'alternativePath': [{'actor': p.actor_action or '', 'system': p.system_response or ''} for p in spec.alternative_paths.all().order_by('step_number')],
            'exceptionPath': [{'actor': p.actor_action or '', 'system': p.system_response or ''} for p in spec.exception_paths.all().order_by('step_number')],
        })

    context = {
        'page_title': 'Activity Diagram',
        'all_features': json.dumps(all_features) if all_features else '[]'
    }
    return render(request, 'main/activity_diagram.html', context)
@csrf_exempt
def save_activity_diagram(request):
    """API: Simpan kode PlantUML dan image URL Activity Diagram untuk Use Case Spec tertentu."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            feature_name = data.get('feature_name')
            plantuml_code = data.get('plantuml')
            image_url = data.get('image_url')
            project = get_active_project(request)

            if not project:
                return JsonResponse({'status': 'error', 'message': 'Tidak ada project aktif.'}, status=400)

            spec = UseCaseSpecification.objects.filter(project=project, feature_name=feature_name).first()
            if not spec:
                return JsonResponse({'status': 'error', 'message': f'Use Case Specification untuk {feature_name} tidak ditemukan.'}, status=404)

            diagram, created = ActivityDiagram.objects.update_or_create(
                use_case_spec=spec,
                defaults={
                    'plantuml_code': plantuml_code,
                    'diagram_image_url': image_url,
                }
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Activity Diagram berhasil disimpan ke database.',
                'created': created
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def save_use_case(request):
    """Simpan use case data ke session untuk activity diagram, di-scope per project."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project = get_active_project(request)
            if not project:
                return JsonResponse({'status': 'error', 'message': 'Tidak ada project aktif.'}, status=400)
            # RC-04 fix: gunakan key yang unik per project
            session_key = f'all_use_case_data_{project.id_project}'
            all_features = request.session.get(session_key, [])
            feature_name = data.get('featureName')
            existing_index = next((i for i, f in enumerate(all_features) if f['featureName'] == feature_name), None)
            if existing_index is not None:
                all_features[existing_index] = data
            else:
                all_features.append(data)
            request.session[session_key] = all_features
            request.session.modified = True
            return JsonResponse({'status': 'success', 'total_features': len(all_features)})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def download_plantuml(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            plantuml_code = data.get('plantuml', '')
            response = HttpResponse(plantuml_code, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="activity_diagram.puml"'
            return response
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


# ============================================================
# STEP 6: SEQUENCE DIAGRAM
# ============================================================

def sequence_diagram(request):
    project = get_active_project(request)

    if project:
        tables = ImportedTable.objects.filter(project=project)
        pages = Page.objects.filter(gui__project=project).values_list('name', flat=True)
    else:
        tables = ImportedTable.objects.none()
        pages = Page.objects.none()

    sql_tables = [t.name for t in tables]
    gui_pages = list(set(pages))

    return render(request, 'main/sequence_diagram.html', {
        'sql_tables_json': json.dumps(sql_tables),
        'gui_pages_json': json.dumps(gui_pages)
    })


def sequence_feature_list(request):
    """API: Daftar fitur Use Case Spec untuk project aktif."""
    try:
        project = get_active_project(request)

        if project:
            specs = UseCaseSpecification.objects.filter(project=project).order_by('-id')
        else:
            specs = UseCaseSpecification.objects.none()

        data = []
        for spec in specs:
            gui_name = spec.gui.nama_atribut if spec.gui else "No GUI"
            data.append({
                "id": spec.id,
                "title": spec.feature_name,
                "gui": gui_name
            })

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def generate_sequence_diagram_by_feature(request, feature_id):
    """Generate sequence diagram untuk satu fitur Use Case Spec."""
    usecase_spec = get_object_or_404(UseCaseSpecification, pk=feature_id)

    body = {}
    if request.method == 'POST':
        try:
            body = json.loads(request.body or '{}')
        except Exception:
            body = {}

    selected_entities = body.get('selected_entities', [])
    actor_boundary_method = body.get('actor_boundary_method', 'requestAction()')
    boundary_ctrl_method = body.get('boundary_controller_method', 'processRequest()')
    boundary_name = body.get('boundary_name', 'System UI')
    ctrl_entity_methods = body.get('ctrl_entity_methods', {})

    basic_paths = usecase_spec.basic_paths.order_by('step_number')
    alt_paths = usecase_spec.alternative_paths.order_by('step_number')
    exc_paths = usecase_spec.exception_paths.order_by('step_number')

    lines = [
        '@startuml', 'autonumber', 'skinparam style strictuml',
        'skinparam responseMessageBelowArrow true',
        '<style>',
        'participant {',
        '  Padding 20',
        '}',
        '</style>',
        f'title {usecase_spec.feature_name}', ''
    ]

    boundary_alias = 'Boundary'
    ctrl_alias = 'Controller'
    lines.append('actor "User" as U')
    lines.append(f'boundary "{boundary_name}" as {boundary_alias}')
    lines.append(f'control "{usecase_spec.feature_name}Controller" as {ctrl_alias}')
    for ent in selected_entities:
        alias = f'E_{ent.replace(" ", "_")}'
        lines.append(f'entity "{ent}" as {alias}')
    lines.append('')

    def write_flow(paths, group_name):
        if not paths.exists():
            return
        lines.append(f'group {group_name}')
        for step in paths:
            if step.actor_action:
                action = step.actor_action.replace('"', "'")
                lines.append(f'U -> {boundary_alias}: {actor_boundary_method} // {action}')
            if step.system_response:
                resp = step.system_response.replace('"', "'")
                lines.append(f'{boundary_alias} -> {ctrl_alias}: {boundary_ctrl_method}')
                lines.append(f'activate {ctrl_alias}')
                for ent in selected_entities:
                    alias = f'E_{ent.replace(" ", "_")}'
                    method = ctrl_entity_methods.get(ent, 'query()')
                    lines.append(f'{ctrl_alias} -> {alias}: {method}')
                    lines.append(f'activate {alias}')
                    lines.append(f'{alias} --> {ctrl_alias}: result')
                    lines.append(f'deactivate {alias}')
                lines.append(f'{ctrl_alias} --> {boundary_alias}: response // {resp}')
                lines.append(f'deactivate {ctrl_alias}')
                lines.append(f'{boundary_alias} --> U: display result')
                lines.append('')
        lines.append('end')
        lines.append('')

    write_flow(basic_paths, 'Basic Flow')
    write_flow(alt_paths, 'Alternative Flow')
    write_flow(exc_paths, 'Exception Flow')
    lines.append('@enduml')

    plantuml_code = '\n'.join(lines)

    # Save sequence diagram config to session for Class Diagram Rule Engine
    if 'sequence_configs' not in request.session:
        request.session['sequence_configs'] = {}
    request.session['sequence_configs'][str(feature_id)] = {
        'feature_id': feature_id,
        'feature_name': usecase_spec.feature_name,
        'selected_entities': selected_entities,
        'actor_boundary_method': actor_boundary_method,
        'boundary_controller_method': boundary_ctrl_method,
        'boundary_name': boundary_name,
        'ctrl_entity_methods': ctrl_entity_methods
    }
    request.session.modified = True

    try:
        resp = requests.post('https://kroki.io/plantuml/png', data=plantuml_code, timeout=20)
        if resp.status_code == 200 and 'image' in resp.headers.get('Content-Type', ''):
            image_b64 = base64.b64encode(resp.content).decode('utf-8')
            return JsonResponse({'status': 'success', 'plantuml': plantuml_code, 'image_base64': image_b64})
        return JsonResponse({'status': 'error', 'message': f'Kroki error {resp.status_code}'}, status=500)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============================================================
# STEP 7: CLASS DIAGRAM
# ============================================================

def class_diagram(request):
    project = get_active_project(request)

    if request.method == "GET":
        if project:
            tables_qs = ImportedTable.objects.filter(project=project)
            rels_qs = ImportedRelationship.objects.filter(table__project=project)
        else:
            tables_qs = ImportedTable.objects.none()
            rels_qs = ImportedRelationship.objects.none()

        tables_data = []
        for table in tables_qs:
            columns = [{"name": c.name, "type": c.data_type} for c in table.columns.all()]
            tables_data.append({"name": table.name, "columns": columns})

        relationships_data = []
        for rel in rels_qs:
            relationships_data.append({
                "table": rel.table.name,
                "column": rel.column_name,
                "ref_table": rel.ref_table.name,
                "ref_column": rel.ref_column_name
            })

        sql_data = {"tables": tables_data, "relationships": relationships_data}
        return render(request, "main/class_diagram.html", {"sql_data_json": json.dumps(sql_data)})

    if request.method == "POST":
        body = json.loads(request.body)
        data = body.get("data")
        if not data:
            return JsonResponse({"status": "error", "message": "No data provided"})

        tables = data.get("tables", [])
        relationships = data.get("relationships", [])

        uml = ["@startuml"]
        uml.append("!theme plain")
        uml.append("skinparam classAttributeIconSize 0")
        uml.append("skinparam class {")
        uml.append("    BackgroundColor White")
        uml.append("    BorderColor #374151")
        uml.append("    ArrowColor #6B7280")
        uml.append("    FontSize 13")
        uml.append("}")
        uml.append("")

        for table in tables:
            # Convert snake_case table name to PascalCase class name
            class_name = ''.join(word.capitalize() for word in table['name'].split('_'))
            uml.append(f"class {class_name} {{")
            # Attributes use private visibility (-) per UML standard
            for col in table.get("columns", []):
                col_name = col.get('name', '')
                col_type = col.get('type', 'String')
                uml.append(f"  - {col_name} : {col_type}")
            uml.append("  --")
            # Methods use public visibility (+) per UML standard
            uml.append(f"  + get{class_name}ById(id : int) : {class_name}")
            uml.append(f"  + getAll{class_name}() : List")
            uml.append(f"  + save() : void")
            uml.append(f"  + delete() : void")
            uml.append("}")
            uml.append("")

        # UML Association relationships (not ERD Crow's Foot notation)
        for rel in relationships:
            from_table = rel.get('table', rel.get('from_table', ''))
            to_table = rel.get('ref_table', rel.get('to_table', ''))
            if from_table and to_table:
                from_cls = ''.join(w.capitalize() for w in from_table.split('_'))
                to_cls = ''.join(w.capitalize() for w in to_table.split('_'))
                uml.append(f"{from_cls} --> {to_cls} : association")

        uml.append("@enduml")

        plantuml_code = "\n".join(uml)
        encoded = urllib.parse.quote(plantuml_code)
        plantuml_png_url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        response = requests.get(plantuml_png_url)

        if response.status_code != 200:
            return JsonResponse({"status": "error", "message": "Failed to generate image"})

        png_base64 = base64.b64encode(response.content).decode('utf-8')
        return render(request, "main/class_diagram.html", {"uml_image": png_base64, "uml_code": plantuml_code})

    return JsonResponse({"status": "error", "message": "Invalid method"})


@csrf_exempt
def generate_class_diagram_api(request):
    """
    API: Generate professional UML 2.x Class Diagram using 7-step OOAD pipeline.
    Priority: Sequence Diagram > Activity > Use Case Spec > User Story > SQL Schema.
    Entity methods are domain behaviors only — CRUD strictly forbidden.
    """
    if request.method not in ('GET', 'POST'):
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    project = get_active_project(request)

    seq_configs = None
    if request.method == 'POST' and request.body:
        try:
            body = json.loads(request.body.decode('utf-8') or '{}')
            seq_configs = body.get('seq_configs')
        except Exception:
            pass

    if not seq_configs:
        sess_configs = request.session.get('sequence_configs', {})
        if isinstance(sess_configs, dict):
            seq_configs = list(sess_configs.values())
        elif isinstance(sess_configs, list):
            seq_configs = sess_configs

    try:
        result = generate_class_diagram(project, seq_configs=seq_configs)
        return JsonResponse({
            'status': 'success',
            'diagrams': {
                'basic':    result['basic'],
                'detailed': result['detailed'],
                'methods':  result['methods'],
                'complete': result['complete'],
            },
            'metadata':   result['metadata'],
            'validation': result.get('validation', {}),
        })
    except Exception as e:
        import traceback
        print('Class Diagram Generator Error:', traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



def import_sql(request):
    project = get_active_project(request)

    if request.method == 'POST':
        file = request.FILES.get('sql_file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        parsed_data = parse_sql_file(file)
        return JsonResponse({'message': 'File parsed successfully', 'data': parsed_data})

    active_gui = GUI.objects.filter(project=project).first() if project else GUI.objects.last()
    return render(request, 'main/import_sql.html', {'gui': active_gui})


def parse_sql(request):
    if request.method == "POST" and request.FILES.get('file'):
        sql_file = request.FILES['file']
        sql_content = sql_file.read().decode('utf-8', errors='ignore')
        try:
            result = parse_sql_file(sql_content)
            project = get_active_project(request)
            save_parsed_sql_to_db(result, project=project)
            return JsonResponse({"status": "success", "data": result})
        except Exception as e:
            import traceback
            print("🔥 SQL Parse Error:", traceback.format_exc())
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "No file uploaded"})


def save_parsed_sql(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            parsed_data = body.get("data")
            if not parsed_data:
                return JsonResponse({"status": "error", "message": "No data received"})
            project = get_active_project(request)
            save_parsed_sql_to_db(parsed_data, project=project)
            return JsonResponse({"status": "success", "message": "Data SQL berhasil disimpan"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request method"})


# ============================================================
# GENERATE SRS (Output Akhir)
# ============================================================

def generate_srs(request):
    project = get_active_project(request)

    if not project:
        return HttpResponse("Silakan pilih atau buat project dari dashboard terlebih dahulu.")

    # Ambil data berdasarkan project aktif
    stories_qs = UserStory.objects.filter(gui__project=project).prefetch_related('scenarios')
    actors_unique = stories_qs.values_list('input_sebagai', flat=True).distinct()

    uc_obj = Usecase.objects.filter(gui__project=project).last()
    uc_url = uc_obj.hasil_usecase.url if uc_obj and uc_obj.hasil_usecase else None

    specs_qs = UseCaseSpecification.objects.filter(project=project).prefetch_related('basic_paths', 'activity_diagram')

    gui_pages = Page.objects.filter(gui__project=project).prefetch_related('elements')

    sequences_qs = Sequence.objects.filter(userstory__gui__project=project)

    cd_obj = ClassDiagram.objects.filter(userstory__gui__project=project).last()
    tables_qs = ImportedTable.objects.filter(project=project).prefetch_related('columns')

    context = {
        'project': project,
        'actors': actors_unique,
        'stories': stories_qs,
        'uc_url': uc_url,
        'specs': specs_qs,
        'gui_pages': gui_pages,
        'sequences': sequences_qs,
        'class_url': cd_obj.hasil_classdiagram.url if cd_obj else "",
        'tables': tables_qs,
        'today': timezone.now(),
    }
    return render(request, 'main/generate_srs.html', context)


# ============================================================
# USER SCENARIO & TEST
# ============================================================

def use_case(request):
    return render(request, 'main/use_case.html')


def user_scenario(request, gui_id):
    gui = get_object_or_404(GUI, id_gui=gui_id)
    project = get_active_project(request)

    if project:
        specs = UseCaseSpecification.objects.filter(project=project).prefetch_related('scenarios__steps')
    else:
        specs = UseCaseSpecification.objects.filter(gui=gui).prefetch_related('scenarios__steps')

    gui_data = {'pages': [], 'elements': []}
    for p in Page.objects.filter(gui=gui):
        gui_data['pages'].append({'id': p.id, 'name': p.name})
    for el in Element.objects.filter(page__gui=gui):
        gui_data['elements'].append({
            'id': el.id, 'name': el.name,
            'type': el.input_type.lower() if el.input_type else "text",
            'page': el.page.name
        })

    saved_scenarios = {}
    for spec in specs:
        saved_scenarios[str(spec.id)] = {'Normal': [], 'Alternative': [], 'Exception': []}
        for scenario in spec.scenarios.all():
            steps_data = [{'condition': s.condition, 'activity': s.action_type, 'target_id': s.target_id, 'target_text': s.target_text} for s in scenario.steps.all().order_by('step_number')]
            scen_type = scenario.scenario_type
            if scen_type == 'Positive':
                scen_type = 'Normal'
            elif scen_type == 'Negative':
                scen_type = 'Exception'
            if scen_type in saved_scenarios[str(spec.id)]:
                saved_scenarios[str(spec.id)][scen_type] = steps_data

    return render(request, 'main/user_scenario.html', {
        'specs': specs,
        'gui_data_json': json.dumps(gui_data),
        'saved_scenarios_json': json.dumps(saved_scenarios),
        'gui': gui,
    })


@csrf_exempt
def save_scenarios_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            saved_count = 0
            for item in data:
                spec_id = item.get('spec_id')
                scen_type = item.get('type')
                steps = item.get('steps', [])
                try:
                    spec = UseCaseSpecification.objects.get(pk=int(spec_id))
                except UseCaseSpecification.DoesNotExist:
                    continue
                TestScenario.objects.filter(use_case=spec, scenario_type=scen_type).delete()
                scenario = TestScenario.objects.create(use_case=spec, scenario_type=scen_type)
                for idx, step in enumerate(steps, start=1):
                    TestStep.objects.create(scenario=scenario, step_number=idx, condition=step.get('condition', 'Given'), action_type=step.get('activity', ''), target_id=step.get('target_id', ''), target_text=step.get('target_text', ''))
                saved_count += 1
            return JsonResponse({'status': 'success', 'message': f'{saved_count} scenarios saved'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def scenario_result(request, gui_id):
    project = get_active_project(request)
    if not project:
        return redirect('main:home')

    # RC-02 fix: scope GUI ke project aktif, tidak ada fallback GUI.objects.first()
    gui_obj = get_object_or_404(GUI, id_gui=gui_id, project=project) if gui_id else GUI.objects.filter(project=project).first()

    # RC-02 fix: selalu filter ke project aktif, tidak ada .all() global
    specs = UseCaseSpecification.objects.filter(project=project).prefetch_related('scenarios__steps')

    return render(request, 'main/scenario_result.html', {'specs': specs, 'gui': gui_obj})


# ============================================================
# INPUT GUI (Form Elements)
# ============================================================

def input_gui(request, gui_id=None):
    project = get_active_project(request)
    gui = None

    if gui_id:
        gui = GUI.objects.filter(id_gui=gui_id).first()

    if not gui:
        # Ambil GUI dari project aktif
        if project:
            gui = GUI.objects.filter(project=project).first()
        else:
            gui = GUI.objects.first()

    if not gui:
        # Buat GUI baru untuk project aktif
        if not project:
            pengguna = get_or_create_guest_user()
            project = Project.objects.create(
                nama_project="Default Project",
                pengguna=pengguna,
            )
            set_active_project(request, project)

        gui = GUI.objects.create(
            project=project,
            id_gui=f"G{project.id_project}",
            nama_atribut=project.nama_project
        )
        
    pages_data = []
    if gui:
        pages = Page.objects.filter(gui=gui).prefetch_related('elements')
        for p in pages:
            elements_data = []
            for el in p.elements.all():
                elements_data.append({
                    "name": el.name,
                    "type": el.element_type
                })
            pages_data.append({
                "name": p.name,
                "elements": elements_data
            })

    return render(request, 'main/input_gui.html', {
        'gui': gui,
        'pages_json': json.dumps(pages_data)
    })


def save_gui(request, gui_id):
    try:
        gui = get_object_or_404(GUI, id_gui=gui_id)
        data = json.loads(request.body)
        with transaction.atomic():
            gui.pages.all().delete()
            for page_idx, page_data in enumerate(data, start=1):
                page = Page.objects.create(gui=gui, name=page_data.get('name') or f'Page {page_idx}', order=page_idx)
                for elem_idx, elem_data in enumerate(page_data.get('elements', []), start=1):
                    elem_name = elem_data.get('name')
                    elem_type = elem_data.get('type')
                    if not elem_name or not elem_type:
                        continue
                    Element.objects.create(page=page, name=elem_name, input_type=elem_type.lower(), element_type=elem_type.lower(), order=elem_idx)
        return JsonResponse({'status': 'success', 'message': 'Data saved successfully'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============================================================
# MISC / UTILITY
# ============================================================

def reset_usecase_data(request):
    """Reset hanya data project aktif."""
    project = get_active_project(request)
    if project:
        UseCaseSpecification.objects.filter(project=project).delete()
    return redirect('main:input_informasi_tambahan')


def generatesrs(request):
    return render(request, 'main/generatesrs.html')


def save_userstory(request):
    if request.method == "POST":
        actor = request.POST.get("input_sebagai")
        fitur = request.POST.get("input_fitur")
        gui_id = request.POST.get("gui_id")
        userstory = UserStory(input_sebagai=actor, input_fitur=fitur, gui_id=gui_id)
        userstory.save()
        return redirect("halaman_sukses")


def create_plantuml_from_usecase(data):
    plantuml = "@startuml\n"
    plantuml += f"title Activity Diagram - {data.get('featureName', 'Use Case')}\n\n"
    plantuml += "start\n"
    precondition = data.get('precondition', '').strip()
    if precondition:
        plantuml += f":{precondition};\n"
    basic_path = data.get('basicPath', [])
    if basic_path:
        plantuml += 'partition "Basic Flow" {\n'
        for step in basic_path:
            if step.get('actor', '').strip():
                plantuml += f"    :{step['actor']};\n"
            if step.get('system', '').strip():
                plantuml += f"    :{step['system']};\n"
        plantuml += "}\n\n"
    for flow_name, flow_key in [("Alternative Flow", "alternativePath"), ("Exception Flow", "exceptionPath")]:
        path = data.get(flow_key, [])
        if any(s.get('actor', '').strip() or s.get('system', '').strip() for s in path):
            plantuml += f'partition "{flow_name}" {{\n'
            for step in path:
                if step.get('actor', '').strip():
                    plantuml += f"    :{step['actor']};\n"
                if step.get('system', '').strip():
                    plantuml += f"    :{step['system']};\n"
            plantuml += "}\n\n"
    postcondition = data.get('postcondition', '').strip()
    if postcondition:
        plantuml += f":{postcondition};\n"
    plantuml += "stop\n@enduml"
    return plantuml