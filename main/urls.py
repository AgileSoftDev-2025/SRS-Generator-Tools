from django.urls import path
from . import views

app_name = 'main' 

urlpatterns = [
    path('', views.login_view, name='login'),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user-story/', views.user_story, name='user_story'),
    path('use-case/', views.use_case, name='use_case'),
    path('scenario/', views.user_scenario, name='user_scenario'),
    path('use-case-diagram/', views.use_case_diagram, name='use_case_diagram'),
    path('use-case-spec/', views.use_case_spec, name='use_case_spec'),
    path('activity-diagram/', views.activity_diagram, name='activity_diagram'),
    path('sequence-diagram/', views.sequence_diagram, name='sequence_diagram'),
    path('class-diagram/', views.class_diagram, name='class_diagram'),
    path('generate-srs/', views.generate_srs, name='generate_srs'),
    path('project/new/', views.project_new, name='project_new'),
    path('project/<id_project>/', views.project_detail, name='project_detail'),
]