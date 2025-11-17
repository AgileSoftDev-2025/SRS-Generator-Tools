<<<<<<< HEAD
from django.shortcuts import render
from django.http import JsonResponse
import json
from .plantuml_service import generate_use_case_diagram, get_plantuml_url

def home(request):
    return render(request, 'main/home.html')
=======
from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Pengguna, Session, GUI, Usecase, UserStory, UserStoryScenario, UseCaseSpecification, Sequence, ClassDiagram, ActivityDiagram
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse

def home(request):
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
>>>>>>> 84646cbce0a25968c7738040c5448171e88711d2

def user_story(request):
    return render(request, 'main/user_story.html')

def use_case(request):
    return render(request, 'main/use_case.html')

def user_scenario(request):
    return render(request, 'main/user_scenario.html')

def use_case_diagram(request):
    return render(request, 'main/use_case_diagram.html')

def use_case_spec(request):
    return render(request, 'main/use_case_spec.html')

def activity_diagram(request):
    return render(request, 'main/activity_diagram.html')

def import_sql(request):   
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


def sequence_diagram(request):
    return render(request, 'main/sequence_diagram.html')

def class_diagram(request):
    return render(request, 'main/class_diagram.html')

def generate_srs(request):
    return render(request, 'main/generate_srs.html')

<<<<<<< HEAD
# New API endpoint for generating use case diagram
def generate_use_case_diagram_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            actors_data = data.get('actors', [])
            
            # Generate PlantUML code
            plantuml_code = generate_use_case_diagram(actors_data)
            
            # Get PlantUML URL
            diagram_url = get_plantuml_url(plantuml_code)
            
            return JsonResponse({
                'success': True,
                'diagram_url': diagram_url,
                'plantuml_code': plantuml_code
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
=======
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

def project_detail(request, id):
    # Ambil data project berdasarkan id
    project = get_object_or_404(Project, id_project=id_project)
    
    # Kirim data ke template HTML
    return render(request, 'main/project_detail.html', {'project': project})
>>>>>>> 84646cbce0a25968c7738040c5448171e88711d2
