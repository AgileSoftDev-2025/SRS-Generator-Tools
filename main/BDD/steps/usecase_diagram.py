
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
@given('sudah terdapat data User Story di sistem')
def step_impl(context): pass
@when('user menekan tombol Generate Use Case')
def step_impl(context): pass
@then('sistem menampilkan gambar diagram via PlantUML')
def step_impl(context): pass