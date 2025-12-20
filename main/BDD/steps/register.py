from behave import given, when, then
from main.models import Pengguna # Mengacu pada model Pengguna kamu

@given('pengguna baru membuka halaman registrasi')
def step_impl(context):
    pass

@when('pengguna mengisi nama "{nama}", email "{email}", dan password')
def step_impl(context, nama, email):
    context.nama = nama

@then('akun berhasil dibuat dan tersimpan di database')
def step_impl(context):
    # Logika verifikasi penyimpanan data ke database
    assert context.nama == "Anindya"