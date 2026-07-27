
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
@given('user memilih salah satu fitur')
def step_impl(context): pass
@when('user mengisi Precondition "{text}"')
def step_impl(context, text): pass
@then('spesifikasi use case berhasil diperbarui')
def step_impl(context): pass