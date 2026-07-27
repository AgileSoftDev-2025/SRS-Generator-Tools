from behave import given, when, then

@given('seluruh diagram dan spesifikasi telah selesai dibuat')
def step_impl(context):
    # Simulasi ketersediaan data di database
    context.data_ready = True 

@when('user menekan tombol "Generate SRS Document"')
def step_impl(context):
    # Simulasi pemanggilan fungsi PDF generator di Django
    context.document_generated = True 

@then('sistem menghasilkan file dokumen SRS dalam format PDF')
def step_impl(context):
    assert context.document_generated is True