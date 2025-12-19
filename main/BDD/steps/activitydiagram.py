# Import utama untuk Behave
from behave import given, when, then

# Import untuk simulasi browser/request di Django
from django.test import Client

# Import Model agar bisa cek data masuk ke database atau tidak
from main.models import (
    Project, UserStory, Usecase, UseCaseSpecification, 
    Sequence, ClassDiagram, Page, Element, ImportedTable
)

# Inisialisasi client untuk testing
client = Client()

@given('data Basic Path sudah terisi lengkap')
def step_impl(context): pass
@when('user mengklik Generate Activity Diagram')
def step_impl(context): pass
@then('file diagram .puml berhasil dibuat')
def step_impl(context): pass