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

@given('user berada di halaman input User Story')
def step_impl(context): pass
@when('user memasukkan Actor "{actor}" dan Fitur "{feature}"')
def step_impl(context, actor, feature): pass
@then('data User Story berhasil tersimpan di database')
def step_impl(context): pass