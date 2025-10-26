
from django.contrib import admin
from . import views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('previous/', views.previous_page, name='previous_page'),
    path('input_informasi_tambahan/', views.input_informasi_tambahan, name='input_informasi_tambahan'),
    path('input_informasi_tambahan/use_case_spec.html', views.use_case_spec, name='use_case_spec'),
    path('save_use_case_spec/<int:feature_id>/', views.save_use_case_spec, name='save_use_case_spec'),
    path('use_case_spec/', views.use_case_spec, name='use_case_spec'),
]