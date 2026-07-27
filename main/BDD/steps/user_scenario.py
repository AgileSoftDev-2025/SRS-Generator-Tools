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

@given('user berada di form User Scenario')
def step_impl(context): pass
@when('user menambah langkah "{cond}" dengan aksi "{act}"')
def step_impl(context, cond, act): pass
@then('langkah skenario tersimpan untuk fitur tersebut')
def step_impl(context): pass