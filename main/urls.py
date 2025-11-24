from django.urls import path
from . import views

app_name = 'main' 

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user-story/', views.user_story, name='user_story'),
    path('use-case/', views.use_case, name='use_case'),
    path('scenario/', views.user_scenario, name='user_scenario'),
    path('use-case-diagram/', views.use_case_diagram, name='use_case_diagram'),
    path('input_informasi_tambahan/', views.input_informasi_tambahan, name='input_informasi_tambahan'),
    #path('input_informasi_tambahan/use_case_spec.html', views.use_case_spec, name='use_case_spec'),
    path('save_use_case_spec/<int:feature_id>/', views.save_use_case_spec, name='save_use_case_spec'),
    path('use_case_spec/', views.use_case_spec, name='use_case_spec'),
    path('api/save-use-case/', views.save_use_case, name='save_use_case'),
    path('activity-diagram/', views.activity_diagram, name='activity_diagram'),
    path('input-gui/', views.input_gui, name='input_gui'),
    path('import-sql/', views.import_sql, name='import_sql'),
    #path('import-sql/class_diagram.html', views.class_diagram, name='class_diagram'),
    path('parse-sql/', views.parse_sql, name='parse_sql'),
    path('save-parsed-sql/', views.save_parsed_sql, name='save_parsed_sql'),
    path('sequence-diagram/', views.sequence_diagram, name='sequence_diagram'),
    path('class-diagram/', views.class_diagram, name='class_diagram'),
    path('generate-srs/', views.generate_srs, name='generate_srs'),
    path('project/new/', views.project_new, name='project_new'),
    path('project/<id_project>/', views.project_detail, name='project_detail'),
    path('api/generate-plantuml/', views.generate_plantuml, name='generate_plantuml'),
    path('api/download-plantuml/', views.download_plantuml, name='download_plantuml'),
]