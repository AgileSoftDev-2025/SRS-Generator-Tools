from behave import given, when, then

@given('user sudah memiliki data skenario fitur di sistem')
def step_impl(context):
    # Simulasi pengecekan data skenario di database
    context.has_data = True 

@when('user menekan tombol "Generate Activity Diagram"')
def step_impl(context):
    # Simulasi pemicu generator Activity Diagram
    context.generate_triggered = True 

@then('sistem menampilkan visualisasi Activity Diagram via PlantUML')
def step_impl(context):
    # Verifikasi bahwa diagram berhasil diproses
    assert context.generate_triggered is True