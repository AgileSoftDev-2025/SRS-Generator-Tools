from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')
def user_story(request):
    return render(request, 'main/user_story.html')

def use_case(request):
    return render(request, 'main/use_case.html')

def user_scenario(request):
    return render(request, 'main/user_scenario.html')

def use_case_diagram(request):
    return render(request, 'main/use_case_diagram.html')
    
def activity_diagram(request):
    return render(request, 'main/activity_diagram.html')

def sequence_diagram(request):
    return render(request, 'main/sequence_diagram.html')

def class_diagram(request):
    return render(request, 'main/class_diagram.html')

def generate_srs(request):
    return render(request, 'main/generate_srs.html')

def input_informasi_tambahan(equest):
    return render(request='main/input_informasi_tambahan.html')
def input_informasi_tambahan(request):
    # Contoh data dummy untuk fitur
    features = [
        {
            'id': 1,
            'name': 'Login System',
            'description': 'Allows users to log in securely.',
            'priority': 'High',
            'status': 'Active'
        },
        {
            'id': 2,
            'name': 'User Registration',
            'description': 'Enables new users to sign up.',
            'priority': 'Medium',
            'status': 'Active'
        },
        {
            'id': 3,
            'name': 'Password Reset',
            'description': 'Lets users reset their forgotten passwords.',
            'priority': 'Low',
            'status': 'Inactive'
        }
    ]

    context = {'features': features}
    return render(request, 'main/input_informasi_tambahan.html', context)

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
    
def previous_page(request):
    # logic halaman sebelumnya
    return render(request, 'main/halaman_sebelumnya.html')