from main.models import UserStory, UserStoryScenario, Page, ImportedTable

# main/generators/sequence_generator.py

def build_sequence_plantuml(usecase_spec, basic_paths, alt_paths, exc_paths, pages, tables, relationships):
    lines = []
    lines.append("@startuml")
    lines.append("autonumber")
    lines.append("skinparam responseMessageBelowArrow true")
    lines.append("actor User")

    # =============================
    # 1. BOUNDARY (GUI)
    # =============================
    boundary_map = {}
    active_boundary = "UI"

    if pages.exists():
        for page in pages:
            # Buat ID unik: B_NamaPage_ID
            safe_name = "".join(c for c in page.name if c.isalnum())
            safe_alias = f"B_{safe_name}_{page.id}"
            
            lines.append(f'boundary "{page.name}" as {safe_alias}')
            boundary_map[page.name.lower()] = safe_alias
        
        if boundary_map:
            active_boundary = list(boundary_map.values())[0]
    else:
        lines.append('boundary "Application UI" as UI')

    # =============================
    # 2. CONTROLLER (PERBAIKAN NAMA)
    # =============================
    # Logika: Jika nama fitur diawali "As a...", potong jadi "System Controller"
    # atau ambil kata kuncinya saja.
    
    feature_name = usecase_spec.feature_name
    display_name = feature_name
    
    # Jika nama fitur terlalu panjang atau berupa kalimat user story
    if len(feature_name) > 25 or "As a" in feature_name or "I want to" in feature_name:
        display_name = "System Controller"
    
    controller_alias = f"C_Controller_{usecase_spec.id}"
    lines.append(f'control "{display_name}" as {controller_alias}')

    # =============================
    # 3. ENTITY (DATABASE)
    # =============================
    entity_map = {}
    for table in tables:
        safe_tbl = "".join(c for c in table.name if c.isalnum())
        safe_entity = f"E_{safe_tbl}"
        lines.append(f'entity "{table.name}" as {safe_entity}')
        entity_map[table.name.lower()] = safe_entity

    lines.append("")
    lines.append(f"title {feature_name}") # Judul tetap nama asli agar jelas

    # =============================
    # 4. LOGIC LANGKAH
    # =============================
    def write_steps(path_list):
        if not path_list: return

        for step in path_list:
            # AKSI USER
            if step.actor_action:
                action = step.actor_action.replace('"', "'")
                lines.append(f"User -> {active_boundary}: {action}")

            # RESPON SISTEM
            if step.system_response:
                resp = step.system_response.replace('"', "'")
                resp_lower = resp.lower()
                
                # 1. Boundary -> Controller
                lines.append(f"{active_boundary} -> {controller_alias}: Request Process")
                
                # 2. Cek apakah respon mengandung nama tabel (Entity)
                found_entity = None
                for tbl_name, tbl_alias in entity_map.items():
                    if tbl_name in resp_lower:
                        found_entity = tbl_alias
                        break
                
                # 3. Controller -> Entity (Jika ada)
                if found_entity:
                    lines.append(f"{controller_alias} -> {found_entity}: Query/Update")
                    lines.append(f"{found_entity} --> {controller_alias}: Result Data")
                
                # 4. Controller -> Boundary
                lines.append(f"{controller_alias} --> {active_boundary}: Return Result")
                
                # 5. Boundary -> User
                lines.append(f"{active_boundary} --> User: {resp}")

    # =============================
    # 5. DRAW FLOWS
    # =============================
    
    # Cek Data Kosong (Penting untuk debugging user)
    if not basic_paths.exists():
        lines.append(f"note right of User #ffaaaa")
        lines.append(f"DATA KOSONG:\nTidak ada langkah 'Basic Flow' di database.\nSilakan input langkah-langkah di menu Input Informasi Tambahan.")
        lines.append("end note")

    lines.append("== Basic Flow ==")
    write_steps(basic_paths)

    if alt_paths.exists():
        lines.append("")
        lines.append("alt Alternative Flow")
        write_steps(alt_paths)
        lines.append("end")

    if exc_paths.exists():
        lines.append("")
        lines.append("group Exception Flow")
        write_steps(exc_paths)
        lines.append("end")

    lines.append("@enduml")
    return "\n".join(lines)