from django.test import TestCase, Client
from django.urls import reverse
from main.models import Project, UseCaseSpecification, ActivityDiagram, Pengguna
import json

class ActivityDiagramAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create a Pengguna user
        self.pengguna = Pengguna.objects.create(
            id_user="U001",
            nama_user="Test User",
            email_user="test@example.com",
            password="hashed_password_here"
        )
        
        # Setup dummy active project in session
        self.project = Project.objects.create(
            nama_project="Test Project",
            deskripsi="Test Description",
            pengguna=self.pengguna
        )
        
        # Force project into session
        session = self.client.session
        session['active_project_id'] = self.project.id_project
        session.save()
        
        # Create UseCaseSpecification
        self.spec = UseCaseSpecification.objects.create(
            project=self.project,
            feature_name="LoginFitur",
            summary_description="User wants to login",
            priority="Must Have",
            status="Active",
            input_precondition="User is on page",
            input_postcondition="User is logged in"
        )

    def test_save_activity_diagram_success(self):
        url = reverse('main:save_activity_diagram')
        payload = {
            "feature_name": "LoginFitur",
            "plantuml": "@startuml\ntitle LoginFitur\n|System|\nstart\nstop\n@enduml",
            "image_url": "https://www.plantuml.com/plantuml/png/test"
        }
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        
        # Assert database record exists
        diagram = ActivityDiagram.objects.get(use_case_spec=self.spec)
        self.assertEqual(diagram.plantuml_code, payload["plantuml"])
        self.assertEqual(diagram.diagram_image_url, payload["image_url"])

    def test_save_activity_diagram_missing_spec(self):
        url = reverse('main:save_activity_diagram')
        payload = {
            "feature_name": "NonExistentFeature",
            "plantuml": "@startuml\nstart\nstop\n@enduml",
            "image_url": "https://www.plantuml.com/plantuml/png/test"
        }
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
