from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'main'

urlpatterns = [
    # ─── Dashboard (entry point tanpa login) ───
    path('', views.home, name='home'),

    # ─── Project Management ───
    path('project/new/', views.project_new, name='project_new'),
    path('project/<id_project>/', views.project_detail, name='project_detail'),

    # ─── Main Flow (urutan pengerjaan SRS) ───
    path('use-case-diagram/', views.use_case_diagram, name='use_case_diagram'),   # Step 1
    path('user-story/', views.user_story, name='user_story'),                     # Step 2
    path('input-informasi-tambahan/', views.input_informasi_tambahan, name='input_informasi_tambahan'),  # Step 3
    path('use-case-spec/', views.use_case_spec, name='use_case_spec'),            # Step 4
    path('activity-diagram/', views.activity_diagram, name='activity_diagram'),   # Step 5
    path('sequence-diagram/', views.sequence_diagram, name='sequence_diagram'),   # Step 6
    path('class-diagram/', views.class_diagram, name='class_diagram'),            # Step 7 (via SQL import)

    # ─── Import SQL ───
    path('import-sql/', views.import_sql, name='import_sql'),
    path('parse-sql/', views.parse_sql, name='parse_sql'),
    path('save-parsed-sql/', views.save_parsed_sql, name='save_parsed_sql'),

    # ─── GUI / Form Elements ───
    path('input_gui/', views.input_gui, name='input_gui'),
    path('project/<int:project_id>/input_gui/', views.input_gui, name='input_gui_for_project'),
    path('input_gui/<str:gui_id>/', views.input_gui, name='input_gui_with_id'),

    # ─── User Scenario ───
    path('use-case/', views.use_case, name='use_case'),
    path('user-scenario/<str:gui_id>/', views.user_scenario, name='user_scenario'),
    path('save_scenarios/', views.save_scenarios_api, name='save_scenarios_api'),
    path('scenario_result/<str:gui_id>/', views.scenario_result, name='scenario_result'),

    # ─── Final Output ───
    path('generate-srs/', views.generate_srs, name='generate_srs'),

    # ─── Utility ───
    path('reset-data/', views.reset_usecase_data, name='reset_usecase_data'),

    # ─── API Endpoints ───
    path('api/save-use-case/', views.save_use_case, name='save_use_case'),
    path('api/save_usecase_spec/', views.save_usecase_spec, name='save_usecase_spec'),
    path('api/save-use-case-spec/', views.save_usecase_spec, name='save_usecase_spec_alias'),
    path('api/save-activity-diagram/', views.save_activity_diagram, name='save_activity_diagram'),
    path('api/download-plantuml/', views.download_plantuml, name='download_plantuml'),
    path('api/get-latest-userstory/', views.get_latest_userstory, name='get_latest_userstory'),
    path('api/save_gui/<str:gui_id>/', views.save_gui, name='save_gui'),
    path('api/save-actors/', views.save_actors_and_features, name='save_actors_and_features'),
    path('api/generate-usecase/', views.generate_usecase_diagram, name='generate_usecase_diagram'),
    path('api/sequence/<str:feature_id>/generate/', views.generate_sequence_diagram_by_feature, name='generate_sequence_diagram_by_feature'),
    path('api/sequence/features/', views.sequence_feature_list, name='sequence_feature_list'),
    path('api/class-diagram/generate/', views.generate_class_diagram_api, name='generate_class_diagram_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)