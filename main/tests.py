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


class UseCaseSpecificationAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.pengguna = Pengguna.objects.create(
            id_user="U002",
            nama_user="Spec Test User",
            email_user="spectest@example.com",
            password="hashed_password"
        )
        self.project = Project.objects.create(
            nama_project="Spec Test Project",
            deskripsi="Spec Test Description",
            pengguna=self.pengguna
        )
        session = self.client.session
        session['active_project_id'] = self.project.id_project
        session.save()

    def test_save_and_load_usecase_spec(self):
        save_url = reverse('main:save_usecase_spec')
        payload = {
            "feature_1": {
                "featureName": "Login System",
                "summary": "User logs into application",
                "priority": "Must Have",
                "status": "Active",
                "precondition": "User has active account",
                "postcondition": "User lands on dashboard",
                "basicPath": [{"actor": "User enters credentials", "system": "System validates credentials"}],
                "alternativePath": [{"actor": "User clicks Forgot Password", "system": "System displays reset page"}],
                "exceptionPath": [{"actor": "User enters wrong password 3 times", "system": "System locks account"}]
            }
        }
        response = self.client.post(save_url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        # Assert data exists in database
        spec = UseCaseSpecification.objects.get(project=self.project, feature_name="Login System")
        self.assertEqual(spec.input_precondition, "User has active account")
        self.assertEqual(spec.input_postcondition, "User lands on dashboard")
        self.assertEqual(spec.basic_paths.count(), 1)
        self.assertEqual(spec.basic_paths.first().actor_action, "User enters credentials")
        self.assertEqual(spec.alternative_paths.count(), 1)
        self.assertEqual(spec.exception_paths.count(), 1)

    def test_preserve_specs_on_save_actors_and_features(self):
        # 1. Save spec details first
        save_url = reverse('main:save_usecase_spec')
        payload = {
            "feature_1": {
                "featureName": "Login System",
                "summary": "User logs into application",
                "priority": "Must Have",
                "status": "Active",
                "precondition": "User has active account",
                "postcondition": "User lands on dashboard",
                "basicPath": [{"actor": "User enters credentials", "system": "System validates credentials"}]
            }
        }
        self.client.post(save_url, data=json.dumps(payload), content_type="application/json")

        # 2. Re-save actors & features in Step 1
        save_actors_url = reverse('main:save_actors_and_features')
        actors_payload = [
            {
                "name": "Admin",
                "features": [{"what": "Login System", "why": "access portal"}]
            }
        ]
        res = self.client.post(save_actors_url, data=json.dumps(actors_payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)

        # 3. Assert existing spec pre/postcondition and basic_paths were NOT erased
        spec = UseCaseSpecification.objects.get(project=self.project, feature_name="Login System")
        self.assertEqual(spec.input_precondition, "User has active account")
        self.assertEqual(spec.input_postcondition, "User lands on dashboard")
        self.assertEqual(spec.basic_paths.count(), 1)
        self.assertEqual(spec.basic_paths.first().actor_action, "User enters credentials")

    def test_save_and_load_input_gui(self):
        gui_id = f"G{self.project.id_project}"
        save_gui_url = reverse('main:save_gui', kwargs={'gui_id': gui_id})
        payload = [
            {
                "name": "Halaman Login",
                "elements": [
                    {"name": "Email Field", "type": "text"},
                    {"name": "Submit Button", "type": "button"}
                ]
            }
        ]
        res = self.client.post(save_gui_url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)

        # GET input_gui page and verify pages_json contains the saved data
        input_gui_url = reverse('main:input_gui')
        response = self.client.get(input_gui_url)
        self.assertEqual(response.status_code, 200)
        pages_json = response.context['pages_json']
        parsed_pages = json.loads(pages_json)
        self.assertEqual(len(parsed_pages), 1)
        self.assertEqual(parsed_pages[0]['name'], "Halaman Login")
        self.assertEqual(len(parsed_pages[0]['elements']), 2)

    def test_save_and_load_user_scenario(self):
        spec = UseCaseSpecification.objects.create(
            project=self.project,
            feature_name="Payment Feature",
            summary_description="User pays order"
        )
        save_scen_url = reverse('main:save_scenarios_api')
        payload = [
            {
                "spec_id": spec.id,
                "type": "Normal",
                "steps": [
                    {"condition": "Given", "activity": "page", "target_id": "1", "target_text": "[Page] Halaman Payment"},
                    {"condition": "When", "activity": "click", "target_id": "2", "target_text": "[button] Pay Now"}
                ]
            }
        ]
        res = self.client.post(save_scen_url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)

        # GET user_scenario page and verify saved_scenarios_json
        gui_id = f"G{self.project.id_project}"
        user_scen_url = reverse('main:user_scenario', kwargs={'gui_id': gui_id})
        response = self.client.get(user_scen_url)
        self.assertEqual(response.status_code, 200)
        saved_scenarios_json = response.context['saved_scenarios_json']
        parsed_saved = json.loads(saved_scenarios_json)
        self.assertIn(str(spec.id), parsed_saved)
        self.assertEqual(len(parsed_saved[str(spec.id)]['Normal']), 2)


