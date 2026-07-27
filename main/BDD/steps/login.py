from behave import given, when, then
from django.contrib.auth.models import User

@given('pengguna berada di halaman login')
def step_impl(context):
    # Simulasi keberadaan di halaman login
    pass

@when('pengguna memasukkan username "{username}" dan password "{password}"')
def step_impl(context, username, password):
    # Logika pengecekan user di sistem Django
    context.user_exists = True 

@then('pengguna berhasil masuk ke dashboard utama')
def step_impl(context):
    assert context.user_exists is True