from django.shortcuts import render
from .models import Project, Pengguna, Session, GUI, Usecase, UserStory, UserStoryScenario, UseCaseSpecification, Sequence, ClassDiagram, ActivityDiagram
from django.utils import timezone
from django.shortcuts import redirect
from django.shortcuts import render, redirect, get_object_or_404


def home(request):
    projects = Project.objects.all() 
    return render(request, 'main/home.html', {'projects': projects})
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

def sequence_diagram(request):
    return render(request, 'main/sequence_diagram.html')

def class_diagram(request):
    return render(request, 'main/class_diagram.html')

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
    project = get_object_or_404(Project, id_project=id_project)
    
    # Kirim data ke template HTML
    return render(request, 'main/project_detail.html', {'project': project})

