import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from curses import newpad
import os
from django.core.serializers.json import DjangoJSONEncoder
from .models import *
from django.db import transaction
from main.models import Feature, UseCaseSpecification
from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Pengguna, Session, GUI, Usecase, UserStory, UserStoryScenario, UseCaseSpecification, Sequence, ClassDiagram, ActivityDiagram, Page, ImportedTable, ImportedRelationship
from django.utils import timezone
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from .parsers.sql_parser import parse_sql_file
from .utils import save_parsed_sql_to_db
from django.views.decorators.csrf import csrf_exempt
import base64, requests, urllib.parse, binascii, json, subprocess
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponse
from .forms import RegisterForm 
from main.generators.sequence_generator import generate_sequence_plantuml, build_sequence_plantuml
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import GUI, Page, Element, Usecase
from django.core.files.base import ContentFile  
from .models import GUI, UseCaseSpecification, BasicPath, AlternativePath, ExceptionPath
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def home(request):
    if 'user_id' not in request.session:
        return redirect('main:login')

    user_id = request.session['user_id']
    pengguna = get_object_or_404(Pengguna, id_user=user_id)

    projects = Project.objects.filter(pengguna=pengguna)
    return render(request, 'main/home.html', {'projects': projects})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')  
        password = request.POST.get('password')
        try:
            pengguna = Pengguna.objects.get(email_user=email)
            if pengguna.check_password(password):
                request.session.flush()
                request.session['user_id'] = pengguna.id_user
                session_id = 'S' + str(Session.objects.count() + 1).zfill(4)
                Session.objects.create(
                    id_session=session_id,
                    pengguna=pengguna,
                    login_time=timezone.now(),
                    is_active=True
                )
            
                messages.success(request, 'Login successful!')
                return redirect('main:home')
            else:
                messages.error(request, 'Invalid email or password')
        except Pengguna.DoesNotExist:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'main/login.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                pengguna = form.save()
                if 'user_id' in request.session:
                    del request.session['user_id']
                request.session.flush()
                messages.success(request, 'Registration successful! Please log in.')
                return redirect('main:login')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
                print(f"Error saving user: {e}")
        else:
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_name = form.fields[field].label or field
                        messages.error(request, f"{field_name}: {error}")
    else:
        form = RegisterForm()
    context = {
        'form': form,
        'title': 'Create Account'
    }
    return render(request, 'main/register.html', context)


def logout_view(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        
        # Update session menjadi tidak aktif
        Session.objects.filter(
            pengguna__id_user=user_id,
            is_active=True
        ).update(
            logout_time=timezone.now(),
            is_active=False
        )
        del request.session['user_id']
    
    messages.success(request, 'You have been logged out')
    return redirect('main:login')

def user_story(request):
    return render(request, 'main/user_story.html')

def generatesrs(request):
    return render(request, 'main/generatesrs.html')

def save_userstory(request):
    if request.method == "POST":
        actor = request.POST.get("input_sebagai")
        fitur = request.POST.get("input_fitur")
        gui_id = request.POST.get("gui_id")

        userstory = UserStory(
            input_sebagai=actor,
            input_fitur=fitur,
            gui_id=gui_id
        )
        userstory.save()
        return redirect("halaman_sukses")

@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def save_actors_and_features(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # ==========================================
            # 1. BERSIHKAN DATA LAMA (RESET)
            # ==========================================
            UserStory.objects.all().delete()
            UseCaseSpecification.objects.all().delete()
            
            saved_count = 0
            
            # ==========================================
            # 2. SIAPKAN PENAMPUNG (GROUPING)
            # ==========================================
            # Ini kuncinya: Kita kumpulkan dulu fiturnya biar nggak duplikat di Spec
            feature_map = {} 

            # ==========================================
            # 3. LOOPING DATA INPUT
            # ==========================================
            for actor in data:
                actor_name = actor.get('name')
                features = actor.get('features', [])
                
                for feat in features:
                    feature_name = feat.get('what')
                    feature_purpose = feat.get('why')
                    
                    # ---------------------------------------------------
                    # A. SIMPAN USER STORY (Untuk Garis Panah Diagram)
                    # ---------------------------------------------------
                    # Tetap disimpan satu-per-satu meskipun fiturnya sama.
                    # Contoh: 
                    # Row 1: Babi -> Makan
                    # Row 2: Customer -> Makan
                    UserStory.objects.create(
                        input_sebagai=actor_name,
                        input_fitur=feature_name,
                        input_tujuan=feature_purpose,
                    )

                    # ---------------------------------------------------
                    # B. KUMPULKAN DATA SPEC (Untuk Oval & Dokumen)
                    # ---------------------------------------------------
                    # Jangan simpan ke DB dulu, masukkan ke map biar unik.
                    if feature_name not in feature_map:
                        feature_map[feature_name] = {
                            'actors': [], 
                            'purpose': feature_purpose
                        }
                    
                    # Catat aktornya siapa aja yang pakai fitur ini
                    if actor_name not in feature_map[feature_name]['actors']:
                        feature_map[feature_name]['actors'].append(actor_name)

            # ==========================================
            # 4. SIMPAN USE CASE SPECIFICATION (FINAL)
            # ==========================================
            # Sekarang baru kita simpan ke DB UseCaseSpecification (dijamin unik per fitur)
            for feat_name, info in feature_map.items():
                # Gabungkan aktor jadi teks cantik: "Babi, Customer"
                actors_str = ", ".join(info['actors'])
                
                UseCaseSpecification.objects.create(
                    feature_name=feat_name,
                    # Summary otomatis jadi pintar: "Users (Babi, Customer) want to..."
                    summary_description=f"Users ({actors_str}) want to {feat_name} so that {info['purpose']}",
                    priority="Must Have",
                    status="Active"
                )
                saved_count += 1

            return JsonResponse({
                'status': 'success', 
                'message': f'Berhasil! {saved_count} fitur unik disimpan & User Story tercatat.'
            })

        except Exception as e:
            print(f"❌ Error Save: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=400)

def use_case(request):
    return render(request, 'main/use_case.html')

def user_scenario(request):
    gui = GUI.objects.last() 
    specs = UseCaseSpecification.objects.prefetch_related(
        'scenarios__steps'  # ← PENTING: Harus pakai 'scenarios' bukan 'testscenario_set'
    ).all()
    
    gui_data = {'pages': [], 'elements': []}

    if gui:
        pages = Page.objects.filter(gui=gui)
        for p in pages:
            gui_data['pages'].append({'id': p.id, 'name': p.name})
        
        elements = Element.objects.filter(page__gui=gui)
        for el in elements:
            gui_data['elements'].append({
                'id': el.id, 
                'name': el.name, 
                'type': el.input_type.lower() if el.input_type else "text", 
                'page': el.page.name
            })

    # SIAPKAN DATA SCENARIO YANG SUDAH TERSIMPAN
    saved_scenarios = {}
    for spec in specs:
        saved_scenarios[str(spec.id)] = {  # ← PENTING: Ubah jadi string
            'Positive': [],
            'Negative': []
        }
        for scenario in spec.scenarios.all():
            steps_data = []
            for step in scenario.steps.all().order_by('step_number'):
                steps_data.append({
                    'condition': step.condition,
                    'activity': step.action_type,
                    'target_id': step.target_id or '',
                    'target_text': step.target_text or ''
                })
            saved_scenarios[str(spec.id)][scenario.scenario_type] = steps_data
    
    # DEBUG: Print di terminal untuk cek data
    print("=" * 60)
    print("🔍 USER SCENARIO DEBUG")
    print(f"Total Specs: {specs.count()}")
    print(f"Saved Scenarios: {saved_scenarios}")
    print("=" * 60)

    return render(request, 'main/user_scenario.html', {
        'specs': specs,
        'gui_data_json': json.dumps(gui_data),
        'saved_scenarios_json': json.dumps(saved_scenarios)
    })

@csrf_exempt
def save_scenarios_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("=" * 60)
            print("🔵 DATA DITERIMA:", data)
            print("=" * 60)
            
            saved_count = 0
            
            for item in data:
                spec_id = item.get('spec_id')
                scen_type = item.get('type')
                steps = item.get('steps', [])
                
                print(f"🔵 Processing Spec ID: {spec_id}, Type: {scen_type}")
                
                # ⚠️ PENTING: Pastikan spec_id adalah INTEGER, bukan string
                try:
                    spec = UseCaseSpecification.objects.get(pk=int(spec_id))
                except UseCaseSpecification.DoesNotExist:
                    print(f"❌ Spec dengan ID {spec_id} tidak ditemukan!")
                    continue
                
                # Hapus scenario lama dengan type yang sama
                deleted_count = TestScenario.objects.filter(
                    use_case=spec, 
                    scenario_type=scen_type
                ).delete()
                print(f"🗑️ Deleted {deleted_count[0]} old scenarios")
                
                # Buat scenario baru
                scenario = TestScenario.objects.create(
                    use_case=spec,
                    scenario_type=scen_type
                )
                print(f"✅ Created Scenario ID: {scenario.id}")
                
                # Simpan steps
                for idx, step in enumerate(steps, start=1):
                    test_step = TestStep.objects.create(
                        scenario=scenario,
                        step_number=idx,
                        condition=step.get('condition', 'Given'),
                        action_type=step.get('activity', ''),
                        target_id=step.get('target_id'),
                        target_text=step.get('target_text', '')
                    )
                    print(f"  ✅ Step {idx}: {test_step.condition} - {test_step.action_type}")
                
                saved_count += 1
            
            print("=" * 60)
            print(f"🎉 TOTAL SAVED: {saved_count} scenarios")
            print("=" * 60)
            
            return JsonResponse({
                'status': 'success',
                'message': f'{saved_count} scenarios saved',
                'count': saved_count
            })
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {e}")
            return JsonResponse({
                'status': 'error', 
                'message': f'Invalid JSON: {str(e)}'
            }, status=400)
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Method not allowed'
    }, status=405)

def use_case_diagram(request):
    return render(request, 'main/use_case_diagram.html')

@csrf_exempt
@require_http_methods(["POST", "GET"])
def generate_usecase_diagram(request):
    try:
        # 1. Ambil GUI terakhir (Project Aktif)
        current_gui = GUI.objects.last()
        if not current_gui:
            return JsonResponse({'status': 'error', 'message': 'GUI not found'}, status=404)

        # 2. Ambil User Stories (Bahan Bakunya)
        stories = UserStory.objects.filter(gui=current_gui)
        if not stories.exists():
            return JsonResponse({'status': 'error', 'message': 'Belum ada User Story! Input dulu.'}, status=400)

        # 3. --- RAKIT KODE PLANTUML ---
        plantuml = []
        plantuml.append("@startuml")
        plantuml.append("left to right direction")
        plantuml.append("skinparam packageStyle rectangle")
        
        defined_actors = set()
        
        for story in stories:
            # Bersihin nama (ganti spasi jadi underscore)
            actor_clean = story.input_sebagai.replace(" ", "_")
            feature_clean = story.input_fitur
            
            # Definisi Actor
            if actor_clean not in defined_actors:
                plantuml.append(f"actor \"{story.input_sebagai}\" as {actor_clean}")
                defined_actors.add(actor_clean)
            
            # Relasi
            plantuml.append(f"{actor_clean} --> ({feature_clean})")
            
        plantuml.append("@enduml")
        final_code = "\n".join(plantuml)

        # 4. --- MINTA GAMBAR KE PLANTUML SERVER ---
        encoded_code = urllib.parse.quote(final_code)
        plantuml_url = f"http://www.plantuml.com/plantuml/png/{encoded_code}"
        
        response = requests.get(plantuml_url)
        
        if response.status_code == 200:
            # 5. --- SIMPAN KE DATABASE ---
            # Cari atau Buat row baru di tabel Usecase
            diagram, created = Usecase.objects.update_or_create(
                gui=current_gui,
                defaults={
                    'plantuml_code': final_code  # Simpan Resep
                }
            )

            # Simpan File Gambar
            file_name = f"usecase_{current_gui.id_gui}.png"
            
            # Hapus file lama kalau ada (biar rapi)
            if diagram.hasil_usecase:
                diagram.hasil_usecase.delete(save=False)
            
            # Simpan file baru
            diagram.hasil_usecase.save(file_name, ContentFile(response.content), save=True)

            return JsonResponse({
                'status': 'success',
                'message': 'Diagram berhasil digenerate!',
                'image_url': diagram.hasil_usecase.url
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Gagal konek ke PlantUML'}, status=500)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def input_informasi_tambahan(request):
    specs = UseCaseSpecification.objects.all().prefetch_related(
        'basic_paths', 'alternative_paths', 'exception_paths'
    )

    use_cases_list = []
    for spec in specs:
        # Helper kecil buat format path
        def get_paths(path_manager):
            return [{'actor': p.actor_action, 'system': p.system_response} for p in path_manager.all()]

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
            'exceptionPath': get_paths(spec.exception_paths)
        })

    context = {
        # Kita pakai json.dumps biar datanya siap pakai
        'use_cases_json': json.dumps(use_cases_list)
    }
    return render(request, 'main/input_informasi_tambahan.html', context)

def use_case_spec(request):
    # 1. Ambil data Use Case Spec dari DATABASE
    specs = UseCaseSpecification.objects.all().prefetch_related(
        'basic_paths', 'alternative_paths', 'exception_paths'
    )

    # ✅ TAMBAHAN: Format data untuk dikirim ke template
    all_features = []
    for spec in specs:
        feature_data = {
            'featureName': spec.feature_name,
            'summary': spec.summary_description,
            'priority': spec.priority,
            'status': spec.status,
            'precondition': spec.input_precondition,
            'postcondition': spec.input_postcondition,
            'basicPath': [
                {
                    'actor': bp.actor_action,
                    'system': bp.system_response
                } for bp in spec.basic_paths.all().order_by('step_number')
            ],
            'alternativePath': [
                {
                    'actor': ap.actor_action,
                    'system': ap.system_response
                } for ap in spec.alternative_paths.all().order_by('step_number')
            ],
            'exceptionPath': [
                {
                    'actor': ep.actor_action,
                    'system': ep.system_response
                } for ep in spec.exception_paths.all().order_by('step_number')
            ]
        }
        all_features.append(feature_data)

    # 2. LOGIKA PINTAR: GET OR CREATE
    current_user = Pengguna.objects.first()
    if not current_user:
        current_user = Pengguna.objects.create(
            id_user="U001", nama_user="Admin", email_user="admin@oneuml.com", password="123"
        )

    current_project, _ = Project.objects.get_or_create(
        id_project="P001",
        defaults={
            'nama_project': "Project Skripsi",
            'deskripsi': "Auto Generated",
            'pengguna': current_user
        }
    )

    current_gui, _ = GUI.objects.get_or_create(
        id_gui="G001",
        defaults={
            'project': current_project,
            'nama_atribut': "Home Screen"
        }
    )

    # 3. ✅ Kirim data ke HTML (PENTING!)
    context = {
        'specs': specs,
        'gui': current_gui,
        'all_features': json.dumps(all_features)  # ✅ TAMBAHKAN INI!
    }
    return render(request, 'main/use_case_spec.html', context)

@csrf_exempt
def save_usecase_spec(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Kita perlu hapus data lama dulu biar gak duplikat (Opsional, tapi aman)
            # UseCaseSpecification.objects.all().delete() 
            
            saved_count = 0

            # Loop setiap fitur yang dikirim dari Frontend
            for key, item in data.items():
                
                # 1. SIMPAN BAPAKNYA (UseCaseSpecification)
                spec = UseCaseSpecification.objects.create(
                    feature_name=item.get('featureName', 'No Name'),
                    summary_description=item.get('summary', ''),
                    priority=item.get('priority', 'Must Have'),
                    status=item.get('status', 'Active'),
                    input_precondition=item.get('precondition', ''),
                    input_postcondition=item.get('postcondition', ''),
                    # gui=current_gui (Kalau mau disambungin ke GUI, buka komen ini)
                )

                # 2. SIMPAN ANAK PERTAMA: Basic Path
                # Ambil list 'basicPath' dari JSON
                basic_paths = item.get('basicPath', []) 
                for index, path in enumerate(basic_paths, start=1):
                    BasicPath.objects.create(
                        usecase_spec=spec,       # <--- Sambungkan ke Bapaknya
                        step_number=index,       # Urutan langkah
                        actor_action=path.get('actor', ''),
                        system_response=path.get('system', '')
                    )

                # 3. SIMPAN ANAK KEDUA: Alternative Path
                alt_paths = item.get('alternativePath', [])
                for index, path in enumerate(alt_paths, start=1):
                    AlternativePath.objects.create(
                        usecase_spec=spec,
                        step_number=index,
                        actor_action=path.get('actor', ''),
                        system_response=path.get('system', '')
                    )

                # 4. SIMPAN ANAK KETIGA: Exception Path
                exc_paths = item.get('exceptionPath', [])
                for index, path in enumerate(exc_paths, start=1):
                    ExceptionPath.objects.create(
                        usecase_spec=spec,
                        step_number=index,
                        actor_action=path.get('actor', ''),
                        system_response=path.get('system', '')
                    )
                
                saved_count += 1

            return JsonResponse({'status': 'success', 'message': f'Berhasil simpan {saved_count} fitur!'})

        except Exception as e:
            print(f"❌ Error saat save: {e}") # Print error di terminal biar ketahuan
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def input_gui(request):
    return render(request, 'main/input_gui.html')

def get_latest_userstory(request):
    try:
        us = UserStory.objects.latest("id_userstory")
        return JsonResponse({
            "status": "success",
            "userstory_id": us.id_userstory
        })
    except:
        return JsonResponse({
            "status": "error",
            "message": "No User Story found"
        })


def import_sql(request):
    if request.method == 'POST':
        file = request.FILES.get('sql_file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        parsed_data = parse_sql_file(file)
        # nanti kita bisa tambahkan logika untuk save ke DB di sini
        return JsonResponse({'message': 'File parsed successfully', 'data': parsed_data})
    
    return render(request, 'main/import_sql.html')

def parse_sql(request):
    if request.method == "POST" and request.FILES.get('file'):
        sql_file = request.FILES['file']
        sql_content = sql_file.read().decode('utf-8', errors='ignore')

        try:
            from .parsers.sql_parser import parse_sql_file
            result = parse_sql_file(sql_content)
            return JsonResponse({"status": "success", "data": result})
        except Exception as e:
            import traceback
            print("🔥 SQL Parse Error:", traceback.format_exc())  # tampilkan di console
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "No file uploaded"})

def save_parsed_sql(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            parsed_data = body.get("data")

            if not parsed_data:
                return JsonResponse({"status": "error", "message": "No data received"})

            # Panggil fungsi utilitas penyimpanan
            save_parsed_sql_to_db(parsed_data)

            return JsonResponse({"status": "success", "message": "Data SQL berhasil disimpan ke database"})
        except Exception as e:
            import traceback
            print("🔥 Save SQL Error:", traceback.format_exc())
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request method"})

def sequence_diagram(request):
    return render(request, 'main/sequence_diagram.html')

def generate_sequence_diagram(request, userstory_id):
    try:
        # 1. Generate text kode PlantUML
        plantuml_code = generate_sequence_plantuml(userstory_id)
        
        # DEBUG: Cek kode di terminal
        print("=== PLANTUML CODE ===")
        print(plantuml_code)
        
        if not plantuml_code:
            return HttpResponse("Error: PlantUML Code is empty", status=400)

        # 2. GUNAKAN SERVER KROKI.IO (Alternatif Cepat & Stabil)
        # Kroki menerima kode mentah via POST, jadi tidak perlu ribet encode HEX/Base64
        kroki_url = "https://kroki.io/plantuml/png"
        
        # Kirim kode langsung sebagai body request
        response = requests.post(kroki_url, data=plantuml_code, timeout=10)
        
        if response.status_code == 200:
            # Sukses, kembalikan gambar PNG
            return HttpResponse(response.content, content_type="image/png")
        else:
            # Jika Kroki gagal, tampilkan pesan errornya
            return HttpResponse(f"Gagal generate (Kroki Error): {response.text}", status=500)

    except requests.exceptions.ConnectionError:
        return HttpResponse("Gagal koneksi internet. Pastikan laptop connect wifi.", status=500)
    except Exception as e:
        print(f"System Error: {str(e)}")
        return HttpResponse(f"System Error: {str(e)}", status=500)

def generate_sequence_diagram_by_feature(request, feature_id):
    # 1. Ambil Spesifikasi Fitur
    usecase_spec = get_object_or_404(UseCaseSpecification, pk=feature_id)
    
    target_gui = usecase_spec.gui

    # Validasi 1: Jika GUI yang terhubung ternyata kosong (tidak punya halaman)
    if target_gui and not Page.objects.filter(gui=target_gui).exists():
        print(f"DEBUG: GUI {target_gui.id_gui} terhubung tapi kosong. Mencari GUI lain yang valid...")
        target_gui = None #anggap tidak valid

    # Validasi 2: Jika belum nemu, cari dari relasi UseCase lama (Backward Compatibility)
    if not target_gui and hasattr(usecase_spec, 'usecase') and usecase_spec.usecase:
        candidate = usecase_spec.usecase.gui
        if candidate and Page.objects.filter(gui=candidate).exists():
            target_gui = candidate

    # Validasi 3 (FINAL & PALING PENTING): 
    # Cari GUI manapun di database yang MEMILIKI Pages (Input Elements).
    if not target_gui:
        # Filter GUI yang memiliki setidaknya 1 Page
        valid_gui = GUI.objects.filter(pages__isnull=False).distinct().first()
        
        if valid_gui:
            target_gui = valid_gui
            print(f"DEBUG: Menggunakan GUI Valid (G02/lainnya) -> {target_gui.id_gui}")
        else:
            # Jika benar-benar tidak ada satupun GUI yang punya halaman
            return JsonResponse({
                'status': 'error', 
                'message': 'Data GUI tidak lengkap. Anda sudah membuat Nama GUI, tapi belum mengisi Halaman (Pages) dan Elemen-nya. Silakan isi Input GUI.'
            }, status=400)
    
    # 2. Ambil Artefak Pages (Boundary) dari GUI yang Valid tadi
    pages = Page.objects.filter(gui=target_gui).prefetch_related("elements").order_by('order')
    
    # 3. Ambil Artefak SQL (Entity)
    tables = ImportedTable.objects.all()
    relationships = ImportedRelationship.objects.all()

    # 4. Generate PlantUML Code
    try:
        basic_paths = usecase_spec.basic_paths.order_by("step_number")
        alt_paths = usecase_spec.alternative_paths.all()
        exc_paths = usecase_spec.exception_paths.all()

        plantuml_code = build_sequence_plantuml(
            usecase_spec, basic_paths, alt_paths, exc_paths, pages, tables, relationships
        )
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Gagal logic generator: {str(e)}'}, status=500)

    # 5. Render Gambar via Kroki (Paling Stabil & Cepat)
    try:
        kroki_url = "https://kroki.io/plantuml/png"
        response = requests.post(kroki_url, data=plantuml_code, timeout=20)
        
        if response.status_code == 200:
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            return JsonResponse({
                'status': 'success',
                'plantuml': plantuml_code,
                'image_base64': image_base64
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Gagal render gambar: {response.status_code}'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"Connection Error: {str(e)}"}, status=500)

def sequence_feature_list(request):
    try:
        # Ambil semua data Use Case Spec
        specs = UseCaseSpecification.objects.all().order_by('-id')
        
        # DEBUG: Lihat di terminal apakah data terbaca
        print(f"=== DEBUG: Found {specs.count()} specs in Database ===")

        data = []
        for spec in specs:
            # LOGIKA AMAN UNTUK MENGAMBIL NAMA GUI
            gui_name = "No GUI connected"
            
            try:
                # Cek 1: Apakah field 'gui' terisi langsung?
                if spec.gui:
                    gui_name = spec.gui.nama_atribut
                
                # Cek 2: Fallback ke relasi lama (usecase -> gui)
                elif hasattr(spec, 'usecase') and spec.usecase and spec.usecase.gui:
                    gui_name = spec.usecase.gui.nama_atribut
                    
            except Exception as e:
                # Jika ada error saat ambil nama GUI, jangan stop program.
                # Cukup set jadi Error Text.
                print(f"Warning on Spec ID {spec.id}: {str(e)}")
                gui_name = "Error retrieving GUI"

            # Masukkan ke list
            data.append({
                "id": spec.id,                # Pastikan ini sesuai kolom ID di screenshot (id)
                "title": spec.feature_name,   # Sesuai kolom di screenshot
                "gui": gui_name
            })

        # DEBUG: Print data yang akan dikirim ke frontend
        # print(f"Sending Data: {data}") 
        
        return JsonResponse(data, safe=False)

    except Exception as e:
        # Jika error fatal, print di terminal
        print(f"CRITICAL ERROR in sequence_feature_list: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

def class_diagram(request):
    if request.method == "GET":
        return render(request, "main/class_diagram.html")
    
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"})

    body = json.loads(request.body)
    data = body.get("data")

    if not data:
        return JsonResponse({"status": "error", "message": "No data provided"})

    tables = data.get("tables", [])

    # ----------- Generate UML Code ----------- #
    uml = ["@startuml"]
    for table in tables:
        name = table["name"]
        uml.append(f"class {name} {{")
        for col in table["columns"]:
            uml.append(f"  {col['name']}: {col['type']}")
        uml.append("}")
    for table in tables:
        for fk in table.get("foreign_keys", []):
            uml.append(f"{table['name']} --> {fk['references']}")
    uml.append("@enduml")

    plantuml_code = "\n".join(uml)
    encoded = urllib.parse.quote(plantuml_code)

    # ----------- Request PNG from PlantUML server ----------- #
    plantuml_png_url = f"http://www.plantuml.com/plantuml/png/{encoded}"
    response = requests.get(plantuml_png_url)

    if response.status_code != 200:
        return JsonResponse({"status": "error", "message": "Failed to generate image"})

    # Convert PNG bytes -> base64 string
    png_bytes = response.content
    png_base64 = base64.b64encode(png_bytes).decode('utf-8')

    # ----------- Send to Template ----------- #
    return render(request, "main/class_diagram.html", {
        "uml_image": png_base64,
        "uml_code": plantuml_code
    })

def project_new(request):
    #validatelogin
    if 'user_id' not in request.session:
        return redirect('main:login')

    if request.method == 'POST':
        name = request.POST.get('name')
        desc = request.POST.get('description')

        # get user yang lagi login dari session
        user_id = request.session['user_id']
        pengguna = get_object_or_404(Pengguna, id_user=user_id)

        Project.objects.create(
            id_project=newpad,
            nama_project=name,
            deskripsi=desc,
            pengguna=pengguna,
            tanggal_project_dibuat=timezone.now(),
            tanggal_akses_terakhir=timezone.now(),
        )

        return redirect('main:home')

    return redirect('main:home')

def project_detail(request, id_project):
    # Ambil data project berdasarkan id
    project = get_object_or_404(Project, id_project=project)
    
    # Kirim data ke template HTML
    return render(request, 'main/project_detail.html', {'project': project})

def save_use_case(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            all_features = request.session.get('all_use_case_data', [])
            feature_name = data.get('featureName')
            existing_index = next((i for i, f in enumerate(all_features) if f['featureName'] == feature_name), None)
            if existing_index is not None:
                all_features[existing_index] = data
            else:
                all_features.append(data)
            request.session['all_use_case_data'] = all_features
            request.session.modified = True
            return JsonResponse({
                'status': 'success',
                'message': f'{len(all_features)} features saved successfully',
                'total_features': len(all_features)
            })
        except Exception as e:
            print(f"Error saving use case: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

def activity_diagram(request):
    """
    Halaman untuk menampilkan dan generate activity diagram
    """
    all_features = request.session.get('all_use_case_data', [])

    print(f"=== ACTIVITY DIAGRAM: {len(all_features)} FEATURES ===")
    
    context = {
        'page_title': 'Generated Activity Diagram',
        'all_features': json.dumps(all_features) if all_features else '[]'
    }
    return render(request, 'main/activity_diagram.html', context)

def create_plantuml_from_usecase(data):
    plantuml = "@startuml\n"
    plantuml += f"title Activity Diagram - {data.get('featureName', 'Use Case')}\n\n"
    
    # Start event
    plantuml += "start\n"
    
    # Pre-condition
    precondition = data.get('precondition', '').strip()
    if precondition:
        plantuml += f":{precondition};\n"
    plantuml += "\n"
    
    # Basic Path
    basic_path = data.get('basicPath', [])
    if basic_path:
        plantuml += 'partition "Basic Flow" {\n'
        for step in basic_path:
            actor_action = step.get('actor', '').strip()
            system_action = step.get('system', '').strip()  
            
            if actor_action:
                plantuml += f"    :{actor_action};\n"
            if system_action:
                plantuml += f"    :{system_action};\n"
        plantuml += "}\n\n"
    
    # Alternative Path
    alternative_path = data.get('alternativePath', [])
    has_alternative = any(step.get('actor', '').strip() or step.get('system', '').strip() 
                         for step in alternative_path)
    
    if has_alternative:
        plantuml += 'partition "Alternative Flow" {\n'
        for step in alternative_path:
            actor_action = step.get('actor', '').strip()
            system_action = step.get('system', '').strip()  
            
            if actor_action:
                plantuml += f"    :{actor_action};\n"
            if system_action:
                plantuml += f"    :{system_action};\n"
        plantuml += "}\n\n"
    
    # Exception Path
    exception_path = data.get('exceptionPath', [])
    has_exception = any(step.get('actor', '').strip() or step.get('system', '').strip() 
                       for step in exception_path)
    
    if has_exception:
        plantuml += 'partition "Exception Flow" {\n'
        for step in exception_path:
            actor_action = step.get('actor', '').strip()
            system_action = step.get('system', '').strip()  
            
            if actor_action:
                plantuml += f"    :{actor_action};\n"
            if system_action:
                plantuml += f"    :{system_action};\n"
        plantuml += "}\n\n"
    
    # Post-condition
    postcondition = data.get('postcondition', '').strip()
    if postcondition:
        plantuml += f":{postcondition};\n"
    
    # End event
    plantuml += "stop\n"
    plantuml += "@enduml"
    
    return plantuml

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
    

@require_http_methods(["POST"])
def save_gui(request, gui_id):
    try:
        # Ambil GUI berdasarkan ID
        gui = get_object_or_404(GUI, pk=gui_id)
        
        # Ambil data JSON dari request body
        data = json.loads(request.body)
        
        # 1. Hapus data lama (Pages & Elements) agar bersih sebelum simpan baru
        # Ini akan otomatis menghapus Elements karena on_delete=CASCADE
        gui.pages.all().delete()
        
        # 2. Loop setiap Halaman (Page) dari data JSON
        for page_idx, page_data in enumerate(data, start=1):
            # Buat Page baru
            page = Page.objects.create(
                gui=gui,
                name=page_data.get('name', f'Page {page_idx}'),
                order=page_idx
            )
            
            # 3. Loop setiap Elemen di dalam Halaman tersebut
            elements_list = page_data.get('elements', [])
            for elem_idx, elem_data in enumerate(elements_list, start=1):
                elem_name = elem_data.get('name')
                elem_type = elem_data.get('type')
                
                # Cek agar tidak menyimpan data kosong
                if elem_name and elem_type:
                    Element.objects.create(
                        page=page,
                        name=elem_name,
                        
                        # BAGIAN PENTING: Masukkan ke 'input_type' (sesuai models.py)
                        input_type=elem_type.lower(),
                        
                        # Kita isi juga element_type biar aman (opsional)
                        element_type=elem_type.lower(),
                        
                        order=elem_idx
                    )
        
        return JsonResponse({'status': 'success', 'message': 'Data saved successfully'})
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        print(f"Error saving GUI: {e}") # Cek terminal jika masih error
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def input_gui(request, gui_id=None, project_id=None):
    if gui_id is None:
        # --- LOGIKA PEMBUATAN PROJECT OTOMATIS (JIKA KOSONG) ---
        if not project_id:
            project = Project.objects.first()
            
            if not project:
                # 1. Cek User dulu (Project butuh Pengguna)
                pengguna = Pengguna.objects.first()
                if not pengguna:
                    # Buat user dummy jika tabel Pengguna kosong
                    pengguna = Pengguna.objects.create(
                        id_user="U01", 
                        nama_user="Admin Dev",
                        email_user="admin@dev.com",
                        password="password123"
                    )

                # 2. Buat Project (Perbaiki 'name' jadi 'nama_project' & isi field wajib lain)
                project = Project.objects.create(
                    id_project="P01",                # Wajib diisi manual (CharField PK)
                    nama_project="Default Project",  # Ganti 'name' jadi 'nama_project'
                    deskripsi="Auto generated",
                    pengguna=pengguna                # Wajib ada usernya
                )
            
            # Gunakan 'id_project' bukan 'id'
            project_id = project.id_project 

        # --- LOGIKA PEMBUATAN GUI BARU ---
        # Generate ID GUI manual (misal: G01, G02, dst)
        jumlah_gui = GUI.objects.count() + 1
        new_gui_id = f"G{str(jumlah_gui).zfill(2)}" # Hasil: G01, G02...

        gui = GUI.objects.create(
            id_gui=new_gui_id,          # Wajib diisi manual
            project_id=project_id,
            nama_atribut="GUI Default"  # Wajib diisi (lihat models.py)
        )
        
        # Redirect menggunakan id_gui yang baru dibuat
        return redirect('main:input_gui_with_id', gui_id=gui.id_gui)
    
    gui = get_object_or_404(GUI, pk=gui_id)
    return render(request, 'main/input_gui.html', {'gui': gui})

def reset_usecase_data(request):
    # Hapus semua data Use Case Specification
    UseCaseSpecification.objects.all().delete()
    return redirect('main:input_informasi_tambahan') # Atau redirect ke halaman input fitur

def scenario_result(request):
    # ✅ GANTI: testscenario_set__teststep_set → scenarios__steps
    specs = UseCaseSpecification.objects.prefetch_related(
        'scenarios__steps'  # ← Sesuaikan dengan related_name di models
    ).all()
    
    # DEBUG: Print untuk memastikan data ada
    print("=" * 60)
    print("🔍 SCENARIO RESULT DEBUG")
    print(f"Total Specs: {specs.count()}")
    for spec in specs:
        scenarios = spec.scenarios.all()  # ← Ganti jadi .scenarios
        print(f"\nSpec: {spec.feature_name} (ID: {spec.id})")
        print(f"  Scenarios: {scenarios.count()}")
        for scenario in scenarios:
            steps = scenario.steps.all()  # ← Ganti jadi .steps
            print(f"    - {scenario.scenario_type}: {steps.count()} steps")
    print("=" * 60)
    
    return render(request, 'main/scenario_result.html', {'specs': specs})

def generate_srs(request):
    # 1. Ambil Project Terakhir agar cover tidak 'Skripsi' terus
    project = Project.objects.last()
    if not project:
        return HttpResponse("Data Project belum ada di database.")

    # 2. Ambil ARTEFAK: Actor & Feature (Artifact 3 & 4)
    # Kita ambil SEMUA data tanpa filter ketat karena relasi GUI sering kosong
    stories_qs = UserStory.objects.all().prefetch_related('scenarios')
    actors_unique = stories_qs.values_list('input_sebagai', flat=True).distinct()

    # 3. Ambil ARTEFAK: Use Case Diagram (Artifact 4)
    uc_obj = Usecase.objects.all().last()
    uc_url = uc_obj.hasil_usecase.url if uc_obj and uc_obj.hasil_usecase else None

    # 4. Ambil ARTEFAK: Use Case Spec & Activity Diagram (Artifact 6 & 7)
    # Kita prefetch basic_paths dan activity_diagram agar tabel dan gambarnya muncul
    specs_qs = UseCaseSpecification.objects.all().prefetch_related('basic_paths', 'activity_diagram')

    # 5. Ambil ARTEFAK: Form GUI (Artifact 8)
    gui_pages = Page.objects.all().prefetch_related('elements')

    # 6. Ambil ARTEFAK: Sequence Diagram (Artifact 11)
    sequences_qs = Sequence.objects.all()

    # 7. Ambil ARTEFAK: Class Diagram & Data Dictionary (Artifact 12)
    cd_obj = ClassDiagram.objects.all().last()
    tables_qs = ImportedTable.objects.all().prefetch_related('columns')

    # 8. Masukkan ke Context (Pastikan NAMA VARIABEL SAMA dengan di HTML)
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