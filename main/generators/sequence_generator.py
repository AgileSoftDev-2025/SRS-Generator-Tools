import re
from main.models import UserStory, UserStoryScenario, Page, ImportedTable

def build_sequence_plantuml(usecase_spec, basic_paths, alt_paths, exc_paths, pages, tables, relationships):
    # ====================================================
    # 1. SETUP DEBUG & TEXT ANALYSIS
    # ====================================================
    print("\n" + "="*40)
    print("🚀 SEQUENCE GENERATOR START")
    
    # Gabungkan semua teks langkah untuk analisa global
    all_steps_text = ""
    for path in basic_paths: all_steps_text += f" {path.system_response or ''} {path.actor_action or ''} "
    for path in alt_paths: all_steps_text += f" {path.system_response or ''} {path.actor_action or ''} "
    for path in exc_paths: all_steps_text += f" {path.system_response or ''} {path.actor_action or ''} "
    
    all_steps_text = all_steps_text.lower()
    print(f"📄 Analisis Teks Langkah: {all_steps_text[:100]}...")

    # ====================================================
    # 2. BANGUN LOOKUP TABLE (Mapping Nama Tabel ke Alias)
    # ====================================================
    table_lookup = {}
    active_entities = {} # Menyimpan tabel yang BENAR-BENAR dipanggil
    
    if tables.exists():
        print(f"📊 Total Tabel SQL Ditemukan: {tables.count()}")
        for table in tables:
            # 1. Bersihkan nama tabel (misal: "tbl_customers" -> "customer")
            clean_name = table.name.lower()
            clean_name = re.sub(r'^(tbl_|tb_|m_|t_|tr_|mst_|dt_)', '', clean_name) # Hapus prefix
            clean_name = re.sub(r'(_table|_tbl|_data|_list)$', '', clean_name) # Hapus suffix
            clean_name = re.sub(r'\d+$', '', clean_name) # Hapus angka
            
            # 2. Buat variasi Singular & Plural
            # Contoh: customers -> [customers, customer]
            variations = set()
            variations.add(clean_name)
            variations.add(table.name.lower()) # Nama asli
            
            if clean_name.endswith('s'): 
                variations.add(clean_name[:-1]) # customers -> customer
            else: 
                variations.add(clean_name + 's') # customer -> customers

            # Tambahan khusus (Hardcode logic umum)
            if "auth" in clean_name or "login" in clean_name:
                variations.add("user")
                variations.add("users")

            alias = f"E_{table.id}"
            
            # Simpan ke lookup
            for var in variations:
                table_lookup[var] = {
                    "real_name": table.name,
                    "alias": alias
                }
            
            # DEBUG: Cek apakah tabel ini disebut di teks?
            is_found = False
            for var in variations:
                # Cek exact word match atau partial match panjang
                if re.search(r'\b' + re.escape(var) + r'\b', all_steps_text) or (len(var) > 4 and var in all_steps_text):
                    active_entities[alias] = table.name
                    print(f"   ✅ MATCH: Tabel '{table.name}' terdeteksi via kata '{var}'")
                    is_found = True
                    break
            
            if not is_found:
                print(f"   ❌ SKIP: Tabel '{table.name}' tidak disebut di langkah-langkah.")

    # ====================================================
    # 3. HEADER & PARTICIPANTS DEFINITION
    # ====================================================
    lines = []
    lines.append("@startuml")
    lines.append("autonumber")
    lines.append("skinparam style strictuml")
    lines.append("skinparam responseMessageBelowArrow true")
    lines.append("skinparam ParticipantPadding 25")
    lines.append("skinparam BoxPadding 10")
    
    lines.append(f"title {usecase_spec.feature_name}")

    # A. Actor
    lines.append("actor User as U")

    # B. Boundary (UI)
    boundary_alias = "UI"
    boundary_name = "System UI"
    if pages.exists():
        first_page = pages.first()
        boundary_name = first_page.name
        boundary_alias = f"B_{first_page.id}"
    lines.append(f'boundary "{boundary_name}" as {boundary_alias}')

    # C. Controller
    ctrl_alias = "CTRL"
    lines.append(f'control "System Controller" as {ctrl_alias}')

    # D. Entity (Hanya render tabel yang terdeteksi aktif)
    for alias, name in active_entities.items():
        lines.append(f'entity "{name}" as {alias}')

    # E. Generic DB (Fallback jika ada aktivitas DB tapi tabel spesifik tidak ketemu)
    fallback_db_alias = "DB_GENERIC"
    db_keywords = ['save', 'simpan', 'store', 'update', 'delete', 'hapus', 'insert', 'create', 'fetch', 'get', 'retrieve', 'ambil', 'cari', 'check', 'validate', 'validasi', 'database', 'db', 'record']
    
    has_generic_activity = False
    # Cek apakah ada kata kerja DB tapi tidak ada tabel yang cocok di kalimat itu
    # (Kita lakukan pengecekan per kalimat di logic bawah, tapi deklarasi di sini)
    if any(kw in all_steps_text for kw in db_keywords):
        # Jika tidak ada satupun entity spesifik yang aktif, ATAU mau fallback ditampilkan
        if not active_entities:
            lines.append(f'database "Database System" as {fallback_db_alias}')
            has_generic_activity = True
            print("   ⚠️ Menggunakan Generic Database (karena tidak ada tabel spesifik yang cocok)")

    lines.append("")

    # ====================================================
    # 4. HELPER FUNCTION PENCARI TARGET
    # ====================================================
    def get_target_db(sentence):
        sentence = sentence.lower()
        
        # 1. Cek Tabel Spesifik (Prioritas Utama)
        for keyword, data in table_lookup.items():
            # Regex boundary match (biar 'user' tidak match 'username')
            if re.search(r'\b' + re.escape(keyword) + r'\b', sentence):
                return data['alias']
            # Partial match untuk kata panjang
            if len(keyword) > 4 and keyword in sentence:
                return data['alias']
        
        # 2. Cek Generic DB
        if has_generic_activity:
            if any(kw in sentence for kw in db_keywords):
                return fallback_db_alias
        
        return None

    # ====================================================
    # 5. LOGIC FLOW WRITER
    # ====================================================
    def write_steps(path_list):
        if not path_list: return

        for step in path_list:
            # --- ACTION ---
            if step.actor_action:
                action = step.actor_action.replace('"', "'")
                lines.append(f"U -> {boundary_alias}: {action}")

            # --- RESPONSE ---
            if step.system_response:
                resp = step.system_response.replace('"', "'")
                
                # UI -> Controller
                lines.append(f"{boundary_alias} -> {ctrl_alias}: Request Process")
                lines.append(f"activate {ctrl_alias}")

                # Controller -> Database (Mana yang dipanggil?)
                target_alias = get_target_db(resp)
                
                if target_alias:
                    # Tentukan jenis operasi (Read/Write)
                    method = "Query"
                    if any(k in resp.lower() for k in ['save', 'simpan', 'add', 'tambah', 'create', 'update']):
                        method = "Insert/Update"
                    elif any(k in resp.lower() for k in ['delete', 'hapus']):
                        method = "Delete"
                    
                    lines.append(f"{ctrl_alias} -> {target_alias}: {method}")
                    lines.append(f"activate {target_alias}")
                    lines.append(f"{target_alias} --> {ctrl_alias}: Result")
                    lines.append(f"deactivate {target_alias}")

                # Controller -> UI
                lines.append(f"{ctrl_alias} --> {boundary_alias}: Response")
                lines.append(f"deactivate {ctrl_alias}")

                # UI -> User
                lines.append(f"{boundary_alias} --> U: {resp}")
                lines.append("")

    # ====================================================
    # 6. GENERATE BODY
    # ====================================================
    lines.append("group Basic Flow")
    if basic_paths.exists(): write_steps(basic_paths)
    else: lines.append(f"U -> {boundary_alias}: (No steps)")
    lines.append("end")

    if alt_paths.exists():
        lines.append("")
        lines.append("group Alternative Flow")
        write_steps(alt_paths)
        lines.append("end")

    if exc_paths.exists():
        lines.append("")
        lines.append("group Exception Flow")
        write_steps(exc_paths)
        lines.append("end")

    lines.append("@enduml")
    
    print("🚀 SEQUENCE GENERATOR FINISHED")
    print("="*40 + "\n")
    
    return "\n".join(lines)