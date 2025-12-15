import os
from main.models import Feature, UseCaseSpecification
from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Pengguna, Session, GUI, Usecase, UserStory, UserStoryScenario, UseCaseSpecification, Sequence, ClassDiagram, ActivityDiagram
from django.utils import timezone
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from .parsers.sql_parser import parse_sql_file
from .utils import save_parsed_sql_to_db
from django.views.decorators.csrf import csrf_exempt
import base64
import requests
import urllib.parse
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponse
import json
from .forms import RegisterForm 
from main.generators.sequence_generator import generate_sequence_plantuml
import subprocess
from django.conf import settings

def home(request):
    projects = Project.objects.all() 
    return render(request, 'main/home.html', {'projects': projects})
    if 'user_id' not in request.session:
        return redirect('main:login')
    user_id = request.session['user_id']
    pengguna = get_object_or_404(Pengguna, id_user=user_id)
    projects = Project.objects.all()  # ambil semua project
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
    
def use_case(request):
    return render(request, 'main/use_case.html')

def user_scenario(request):
    return render(request, 'main/user_scenario.html')

def use_case_diagram(request):
    return render(request, 'main/use_case_diagram.html')

def input_informasi_tambahan(request):
    return render(request, 'main/input_informasi_tambahan.html')

def use_case_spec(request):
    return render(request, 'main/use_case_spec.html')

def save_use_case_spec(request, feature_id):
    if request.method == "POST":
        # Ambil data dari form
        summary = request.POST.get("summary")
        priority = request.POST.get("priority")
        status = request.POST.get("status")
        
        # Ambil feature terkait
        feature = get_object_or_404(Feature, id=feature_id)
        
        # Simpan data ke UseCaseSpecification (buat baru atau update)
        use_case, created = UseCaseSpecification.objects.update_or_create(
            feature=feature,  # hubungan foreign key
            defaults={
                'summary': summary,
                'priority': priority,
                'status': status
            }
        )
        
        # Redirect kembali ke halaman input
        return redirect("input_informasi_tambahan")
    else:
        # Jika bukan POST, redirect ke halaman input
        return redirect("input_informasi_tambahan")

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

    plantuml_code = generate_sequence_plantuml(userstory_id)

    file_path = os.path.join(settings.MEDIA_ROOT, f"sequence_{userstory_id}.puml")
    with open(file_path, "w") as f:
        f.write(plantuml_code)

    subprocess.run(["plantuml", file_path])

    png_path = file_path.replace(".puml", ".png")
    with open(png_path, "rb") as img:
        return HttpResponse(img.read(), content_type="image/png")
    
def get_sequence_features(request):
    features = UseCaseSpecification.objects.select_related(
        'usecase__gui'
    ).all()

    data = []
    for f in features:
        data.append({
            "id": f.id_usecasespecification,
            "title": f.summary_description,
            "gui": f.usecase.gui.nama_atribut
        })

    return JsonResponse(data, safe=False)

def generate_sequence_diagram_by_feature(request, feature_id):
    usecase_spec = get_object_or_404(
        UseCaseSpecification,
        id_usecasespecification=feature_id
    )

    basic_paths = usecase_spec.basic_paths.order_by("step_number")
    alt_paths = usecase_spec.alternative_paths.all()
    exc_paths = usecase_spec.exception_paths.all()

    gui = usecase_spec.usecase.gui
    pages = Page.objects.filter(gui=gui).prefetch_related("elements")

    tables = ImportedTable.objects.all()
    relationships = ImportedRelationship.objects.all()

    plantuml = build_sequence_plantuml(
        usecase_spec,
        basic_paths,
        alt_paths,
        exc_paths,
        pages,
        tables,
        relationships
    )

    return JsonResponse({"plantuml": plantuml})

def sequence_feature_list(request):
    features = UseCaseSpecification.objects.select_related(
        'usecase__gui'
    )

    data = []
    for f in features:
        data.append({
            "id": f.id_usecasespecification,
            "title": f.summary_description,
            "gui": f.usecase.gui.nama_atribut,
        })

    return JsonResponse(data, safe=False)

def build_sequence_plantuml(
    usecase_spec,
    basic_paths,
    alt_paths,
    exc_paths,
    pages,
    tables,
    relationships
):
    lines = []
    lines.append("@startuml")
    lines.append("actor User")
    lines.append("boundary UI")
    lines.append("control Controller")
    lines.append("database DB")
    lines.append("")

    lines.append(f"User -> UI : {usecase_spec.summary_description}")
    lines.append("UI -> Controller : request")

    # BASIC PATH
    for step in basic_paths:
        lines.append(f"Controller -> Controller : Step {step.step_number} - {step.description}")

    # GUI interaction
    for page in pages:
        lines.append(f"Controller -> UI : Open page {page.name}")
        for el in page.elements.all():
            lines.append(f"User -> UI : Input {el.name} ({el.input_type})")

    # SQL interaction
    for table in tables:
        lines.append(f"Controller -> DB : access {table.name}")

    lines.append("DB --> Controller : result")
    lines.append("Controller --> UI : response")

    # ALTERNATIVE PATH
    if alt_paths.exists():
        lines.append("alt Alternative Flow")
        for alt in alt_paths:
            lines.append(
                f"Controller -> Controller : Alt Step from {alt.related_basic_step} - {alt.description}"
            )
        lines.append("end")

    # EXCEPTION PATH
    if exc_paths.exists():
        lines.append("alt Exception Flow")
        for exc in exc_paths:
            lines.append(
                f"Controller -> Controller : Exception at {exc.related_basic_step} - {exc.description}"
            )
        lines.append("end")

    lines.append("@enduml")
    return "\n".join(lines) 

def class_diagram(request):
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

def generate_srs(request):
    return render(request, 'main/generate_srs.html')

def project_new(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        desc = request.POST.get('description')
        
        pengguna = Pengguna.objects.first()
        if pengguna is None:
            # bikin dummy user sementara biar ga error
            pengguna = Pengguna.objects.create(
                id_user="U001",
                nama_user="dummyuser",
                email_user="dummy@example.com"
            )

        # Buat ID otomatis sederhana (opsional)
        new_id = str(Project.objects.count() + 1).zfill(5)

        Project.objects.create(
            id_project=new_id,
            nama_project=name,
            deskripsi=desc,
            pengguna=pengguna,
            tanggal_project_dibuat=timezone.now(),
            tanggal_akses_terakhir=timezone.now(),
        
        )
        return redirect('main:home') # setelah berhasil tambah project

    return render(request, 'main/home.html') 

def project_detail(request, id_project):
    # Ambil data project berdasarkan id
    project = get_object_or_404(Project, id_project=project)
    
    # Kirim data ke template HTML
    return render(request, 'main/project_detail.html', {'project': project})

def save_use_case(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Simpan ke session
            request.session['use_case_data'] = data
            return JsonResponse({
                'status': 'success',
                'message': 'Use case data saved successfully'
            })
        except Exception as e:
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
    use_case_data = request.session.get('use_case_data', None)
    
    context = {
        'page_title': 'Generated Activity Diagram',
        'use_case_data': json.dumps(use_case_data) if use_case_data else 'null'
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
    
def user_scenario(request):
    return render(request, 'main/user_scenario.html')