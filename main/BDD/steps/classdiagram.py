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
@given('user mengunggah file .sql ke sistem')
def step_impl(context): pass
@when('SQL Parser membaca tabel dan relasi')
def step_impl(context): pass
@then('Class Diagram berhasil divisualisasikan')
def step_impl(context): pass