from main.models import UserStory, UserStoryScenario, Page, ImportedTable

def generate_sequence_plantuml(userstory_id):
    userstory = UserStory.objects.get(pk=userstory_id)
    scenarios = UserStoryScenario.objects.filter(userstory=userstory)
    
    # Ambil boundary dari GUI yang terhubung (jika ada)
    pages = Page.objects.filter(gui=userstory.gui).order_by("order") if userstory.gui else []
    tables = ImportedTable.objects.all()

    uml = ["@startuml", "actor User", "control System"]

    # Definisi Boundary (Halaman GUI)
    if pages:
        for page in pages:
            safe_name = page.name.replace(" ", "_")
            uml.append(f'boundary "{page.name}" as {safe_name}')
    else:
        uml.append('boundary "UI" as UI')

    # Definisi Database
    for table in tables:
        uml.append(f'database "{table.name}" as {table.name}')

    uml.append("")

    # Logic Simple User Story
    current_boundary = pages[0].name.replace(" ", "_") if pages else "UI"

    for s in scenarios:
        if s.input_given:
            uml.append(f'User -> {current_boundary}: {s.input_given}')
        if s.input_when:
            uml.append(f'User -> {current_boundary}: {s.input_when}')
        
        # Cek interaksi database sederhana
        action = s.input_then.lower()
        db_hit = False
        for table in tables:
            if table.name.lower() in action:
                uml.append(f'{current_boundary} -> {table.name}: {s.input_then}')
                uml.append(f'{table.name} --> {current_boundary}: result')
                db_hit = True
                break
        
        if not db_hit:
            uml.append(f'{current_boundary} --> User: {s.input_then}')

    uml.append("@enduml")
    return "\n".join(uml)

def build_sequence_plantuml(usecase_spec, basic_paths, alt_paths, exc_paths, pages, tables, relationships):
    lines = []
    lines.append("@startuml")
    lines.append("autonumber")
    lines.append("actor User")
    
    # 1. DEFINISI PARTICIPANT (GUI & DATABASE)
    boundary_map = {} 
    entity_map = {}

    # Boundary (Pages)
    if pages.exists():
        for page in pages:
            # Bersihkan nama page (hapus spasi, ubah ke alphanumeric)
            safe_name = "".join(x for x in page.name.title() if x.isalnum())
            if not safe_name: safe_name = f"Page{page.id}"
            
            lines.append(f'boundary "{page.name}" as {safe_name}')
            boundary_map[page.name.lower()] = safe_name
        
        # Set default active boundary
        active_boundary = list(boundary_map.values())[0]
    else:
        lines.append('boundary "System UI" as UI')
        boundary_map["ui"] = "UI"
        active_boundary = "UI"

    lines.append("control Controller")

    # Entity (SQL Tables)
    for table in tables:
        lines.append(f'database "{table.name}" as {table.name}')
        entity_map[table.name.lower()] = table.name

    lines.append("")
    lines.append(f"title Sequence Diagram: {usecase_spec.feature_name}")

    # 2. LOGIKA ALUR (BASIC PATH)
    lines.append(f"== Basic Flow ==")
    
    for step in basic_paths:
        # FIX: Gunakan actor_action & system_response (BUKAN description)
        actor_act = step.actor_action
        sys_resp = step.system_response

        # A. USER ACTION
        if actor_act:
            target = active_boundary
            act_lower = actor_act.lower()
            
            # Cek navigasi halaman
            for page_name_lower, page_alias in boundary_map.items():
                if page_name_lower in act_lower:
                    target = page_alias
                    active_boundary = page_alias
                    break
            
            lines.append(f"User -> {target}: {step.step_number}. {actor_act}")
            lines.append(f"{target} -> Controller: Request Action")

        # B. SYSTEM RESPONSE
        if sys_resp:
            resp_lower = sys_resp.lower()
            
            # Cek akses database
            related_db = None
            for table_lower, table_real in entity_map.items():
                if table_lower in resp_lower:
                    related_db = table_real
                    break
            
            if related_db:
                lines.append(f"Controller -> {related_db}: Query ({sys_resp})")
                lines.append(f"{related_db} --> Controller: Return Result")
            
            lines.append(f"Controller --> {active_boundary}: Update View")
            lines.append(f"{active_boundary} --> User: {sys_resp}")

    # 3. ALTERNATIVE FLOW
    if alt_paths.exists():
        lines.append("")
        lines.append("== Alternative Flows ==")
        for alt in alt_paths:
            lines.append(f"group Alt Flow {alt.step_number}")
            # FIX: Gunakan field yang benar
            if alt.actor_action:
                lines.append(f"User -> {active_boundary}: {alt.actor_action}")
            if alt.system_response:
                lines.append(f"{active_boundary} --> User: {alt.system_response}")
            lines.append("end")

    # 4. EXCEPTION FLOW
    if exc_paths.exists():
        lines.append("")
        lines.append("== Exception Flows ==")
        for exc in exc_paths:
            lines.append(f"group Exception {exc.step_number}")
            # FIX: Gunakan field yang benar
            if exc.actor_action:
                lines.append(f"User -[#red]> {active_boundary}: {exc.actor_action}")
            if exc.system_response:
                lines.append(f"{active_boundary} --[#red]> User: {exc.system_response}")
            lines.append("end")

    lines.append("@enduml")
    return "\n".join(lines)