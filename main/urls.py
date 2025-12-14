from django.urls import path, include
from . import views

app_name = 'main' 

urlpatterns = [
    # Authentication & Home
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),    
   
    # Project Management
    path('project/new/', views.project_new, name='project_new'),
    path('project/<id_project>/', views.project_detail, name='project_detail'),
    
    # Main Flow - SESUAI URUTAN APLIKASI
    path('use-case-diagram/', views.use_case_diagram, name='use_case_diagram'),  # Step 1
    path('user-story/', views.user_story, name='user_story'),                    # Step 2
    path('input-informasi-tambahan/', views.input_informasi_tambahan, name='input_informasi_tambahan'), # Step 3 - 🔥 DIPERBAIKI: gunakan HYPHEN
    path('use-case-spec/', views.use_case_spec, name='use_case_spec'),          # Step 4
    path('activity-diagram/', views.activity_diagram, name='activity_diagram'), # Step 5
    path('sequence-diagram/', views.sequence_diagram, name='sequence_diagram'),
    path('sequence/<int:userstory_id>/generate/', views.generate_sequence_diagram, name='generate_sequence_diagram'),

    
    # Alternative/Special Features
    path('use-case/', views.use_case, name='use_case'),
    path('user_scenario/', views.user_scenario, name='user_scenario'),
    
    # SQL Import & Class Diagram
    path('import-sql/', views.import_sql, name='import_sql'),
    path('parse-sql/', views.parse_sql, name='parse_sql'),
    path('save-parsed-sql/', views.save_parsed_sql, name='save_parsed_sql'),
    path('class-diagram/', views.class_diagram, name='class_diagram'),
    
    # Other Diagrams
    path('sequence-diagram/', views.sequence_diagram, name='sequence_diagram'),
    path('input_gui/', views.input_gui, name='input_gui'),
    
    # Final Output
    path('generate-srs/', views.generate_srs, name='generate_srs'),
    
    # API Endpoints
    path('api/save-use-case/', views.save_use_case, name='save_use_case'),
    path('save_use_case_spec/<int:feature_id>/', views.save_use_case_spec, name='save_use_case_spec'),
    path('api/download-plantuml/', views.download_plantuml, name='download_plantuml'),
    path("api/get-latest-userstory/", views.get_latest_userstory, name="get_latest_userstory"),
    path("sequence/<int:userstory_id>/generate/", views.generate_sequence_diagram, name="generate_sequence_diagram"),
]