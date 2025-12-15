from main.models import (
    UserStory,
    UserStoryScenario,
    Page,
    ImportedTable
)

def generate_sequence_plantuml(userstory_id):

    userstory = UserStory.objects.get(pk=userstory_id)
    scenarios = UserStoryScenario.objects.filter(userstory=userstory)

    pages = Page.objects.filter(gui=userstory.gui).order_by("order")
    tables = ImportedTable.objects.all()

    uml = "@startuml\n"
    uml += "actor User\n"
    uml += "control Controller\n\n"

    # Add boundary objects from GUI Pages
    for page in pages:
        uml += f"boundary {page.name.replace(' ', '_')}\n"

    # Add database entities from SQL import
    for table in tables:
        uml += f"database {table.name}\n"

    uml += "\n"

    # ===== GENERATE MESSAGES FROM SCENARIO =====
    current_boundary = pages.first().name.replace(" ", "_") if pages.exists() else "Boundary"

    for s in scenarios:
        # Actor Action (GIVEN/WHEN)
        if s.input_given.strip():
            uml += f"User -> {current_boundary} : {s.input_given}\n"

        if s.input_when.strip():
            uml += f"User -> {current_boundary} : {s.input_when}\n"

        if s.input_and.strip():
            uml += f"User -> {current_boundary} : {s.input_and}\n"

        # System Action (THEN)
        if s.input_then.strip():
            uml += f"{current_boundary} -> Controller : {s.input_then}\n"

            # Detect SQL operation → send to entity
            lowered = s.input_then.lower()
            if any(k in lowered for k in ["insert", "update", "delete", "select", "check", "save"]):
                for table in tables:
                    uml += f"Controller -> {table.name} : {s.input_then}\n"
                    uml += f"{table.name} --> Controller : result\n"

    uml += "\n@enduml"
    return uml
