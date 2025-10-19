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