from django.shortcuts import render
from django.http import JsonResponse
import json
from .plantuml_service import generate_use_case_diagram, get_plantuml_url

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