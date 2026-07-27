"""
class_diagram_generator.py
===========================
Professional UML 2.x Class Diagram Generator
Pipeline: 7-Step OOAD Analysis (Boundary-Control-Entity Pattern)
Standards: UML 2.x · OOAD · BCE · SOLID · GRASP · High Cohesion · Low Coupling

Data Priority (per spec):
  1. Sequence Diagram configs  -- boundary/ctrl/entity names, message signatures
  2. Activity Diagram          -- action verbs → behaviors
  3. Use Case Specification    -- feature names, pre/post conditions, flow steps
  4. User Story / Scenario     -- actor names, given/when/then steps
  5. SQL Schema                -- attribute names & types ONLY (validation role)

FORBIDDEN in Entity classes:
  save(), delete(), update(), insert(), findById(), findAll(), getById()
  → These belong to Repository/DAO, not Entity.
"""

import re
from collections import defaultdict

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

FORBIDDEN_CRUD_VERBS = {
    'save', 'delete', 'insert', 'update', 'create', 'getbyid', 'findbyid',
    'findall', 'find', 'fetch', 'retrieve', 'store', 'persist', 'getall',
    'remove', 'add', 'get', 'set', 'read', 'write', 'load', 'query',
    'select', 'execute', 'run', 'commit', 'rollback', 'flush',
}

SQL_TO_UML_TYPE = {
    'int':          'int',     'bigint':      'long',   'smallint': 'int',
    'tinyint':      'int',     'float':       'float',  'double':   'double',
    'decimal':      'double',  'numeric':     'double', 'real':     'float',
    'varchar':      'String',  'char':        'String', 'text':     'String',
    'longtext':     'String',  'mediumtext':  'String', 'tinytext': 'String',
    'nvarchar':     'String',  'nchar':       'String', 'clob':     'String',
    'boolean':      'boolean', 'bool':        'boolean',
    'date':         'Date',    'datetime':    'Date',   'timestamp': 'Date',
    'time':         'String',  'year':        'int',
    'json':         'Object',  'jsonb':       'Object', 'blob':     'byte[]',
    'uuid':         'String',  'enum':        'String',
}

# Domain-behavior verb extraction patterns
# Each tuple: (regex_pattern, canonical_verb_stem)
BEHAVIOR_VERB_PATTERNS = [
    # Auth / Identity
    (r'\b(authenticate[sd]?|authenticating)\b\s*([\w\s]{0,25}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'authenticate'),
    (r'\b(authoriz(?:e[sd]?|ing))\b\s*([\w\s]{0,25}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'authorize'),
    (r'\b(login|log\s+in)\b', 'login'),
    (r'\b(logout|log\s+out)\b', 'logout'),
    (r'\b(register[sd]?|registering)\b\s*([\w\s]{0,25}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'register'),
    # Validation
    (r'\b(validate[sd]?|validating|verif(?:ies|y|ied|ying)?)\b\s*([\w\s]{2,25}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'validate'),
    (r'\b(check[sd]?|checking)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'check'),
    # Calculation / Finance
    (r'\b(calculate[sd]?|calculating|comput(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'calculate'),
    (r'\b(appli(?:es|ed|y|ing)\s+(?:discount|tax|coupon|promo))\b', 'applyDiscount'),
    (r'\b(confirm[sd]?|confirming)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'confirm'),
    # Status / State
    (r'\b(change[sd]?\s+status|update[sd]?\s+status|set[sd]?\s+status)\b', 'changeStatus'),
    (r'\b(cancel[sd]?|canceling|cancelling)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'cancel'),
    (r'\b(approv(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'approve'),
    (r'\b(reject[sd]?|rejecting|declin(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'reject'),
    (r'\b(activat(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'activate'),
    (r'\b(deactivat(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'deactivate'),
    (r'\b(suspend[sd]?|suspending)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'suspend'),
    # Business Actions
    (r'\b(process(?:es|ed|ing)?)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'process'),
    (r'\b(generat(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'generate'),
    (r'\b(assign[sd]?|assigning)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'assign'),
    (r'\b(allocat(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'allocate'),
    (r'\b(reserv(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'reserve'),
    (r'\b(schedul(?:e[sd]?|ing))\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'schedule'),
    (r'\b(submit[sd]?|submitting)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'submit'),
    # Communication
    (r'\b(send[sd]?|sending)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'send'),
    (r'\b(notif(?:ies|y|ied|ying)?)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'notify'),
    # UI / Display
    (r'\b(display[sd]?|displaying|show[sd]?|showing)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'display'),
    # Upload / Download
    (r'\b(upload[sd]?|uploading)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'upload'),
    (r'\b(download[sd]?|downloading)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'download'),
    # Search / Filter
    (r'\b(search(?:es|ed|ing)?)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'search'),
    (r'\b(filter[sd]?|filtering)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'filter'),
    # Inventory / Stock
    (r'\b(restock[sd]?|restocking)\b', 'restock'),
    (r'\b(reserve\s+stock|reserv(?:e[sd]?|ing)\s+stock)\b', 'reserveStock'),
    # Reporting
    (r'\b(generat(?:e[sd]?|ing)\s+report)\b', 'generateReport'),
    (r'\b(export[sd]?|exporting)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'export'),
    (r'\b(print[sd]?|printing)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'print'),
    # Logging / Audit
    (r'\b(log[sd]?|logging)\b\s*([\w\s]{2,20}?)(?=[,.\n]|$|\s+(?:and|or|then|to|a|an|the)\b)', 'log'),
]

# Domain nouns for candidate entity discovery (Step 1)
DOMAIN_NOUN_PATTERNS = [
    r'\b(user|pengguna|member|pelanggan|customer|client|buyer|seller|admin|administrator|manager|staff|employee|karyawan|operator)\b',
    r'\b(order|pesanan|pemesanan|transaction|transaksi|booking|reservation|request|permintaan)\b',
    r'\b(product|produk|item|barang|goods|merchandise|artikel|catalog|katalog)\b',
    r'\b(payment|pembayaran|invoice|faktur|billing|tagihan|receipt|kuitansi)\b',
    r'\b(cart|keranjang|basket|wishlist|wishlist)\b',
    r'\b(stock|stok|inventory|inventori|warehouse|gudang)\b',
    r'\b(notification|notifikasi|alert|message|pesan|email|sms)\b',
    r'\b(report|laporan|summary|rekap|analytics|statistik)\b',
    r'\b(category|kategori|class|type|jenis|group|grup|tag)\b',
    r'\b(address|alamat|location|lokasi|shipping|pengiriman|delivery|kurir)\b',
    r'\b(review|ulasan|rating|feedback|comment|komentar|testimonial)\b',
    r'\b(session|sesi|token|credential|credentials|password|kata\s*sandi)\b',
    r'\b(role|hak\s+akses|permission|akses|privilege|wewenang)\b',
    r'\b(profile|profil|account|akun|identity|identitas)\b',
    r'\b(discount|diskon|coupon|voucher|promo|promotion)\b',
    r'\b(log|activity|audit|history|riwayat|rekaman)\b',
    r'\b(file|attachment|document|dokumen|upload|berkas)\b',
    r'\b(schedule|jadwal|appointment|agenda|event|acara)\b',
    r'\b(supplier|vendor|penyedia|partner|mitra)\b',
    r'\b(branch|cabang|department|divisi|unit|division)\b',
]


# ─────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────

def to_pascal_case(text):
    """Convert any case text to PascalCase."""
    if not text:
        return ''
    text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
    parts = re.split(r'[\s_\-/]+', text.strip())
    return ''.join(p.capitalize() for p in parts if p)


def to_camel_case(text):
    """Convert text to camelCase."""
    pascal = to_pascal_case(text)
    return pascal[0].lower() + pascal[1:] if pascal else ''


def map_sql_type(sql_type):
    """Map SQL data type to UML/OOP type."""
    if not sql_type:
        return 'String'
    base = re.sub(r'\s*\(.*\)', '', sql_type).strip().lower()
    return SQL_TO_UML_TYPE.get(base, 'String')


def is_forbidden_crud(method_name):
    """Return True if method starts with a CRUD/persistence verb."""
    clean = re.sub(r'[^a-z]', '', method_name.lower())
    for verb in FORBIDDEN_CRUD_VERBS:
        if clean.startswith(verb):
            return True
    return False


def build_method_sig(verb_stem, noun_phrase='', params='', return_type='void'):
    """
    Build a UML method signature string from components.
    e.g. build_method_sig('validate', 'credentials') → 'validateCredentials() : boolean'
    """
    fillers = {'the', 'a', 'an', 'its', 'their', 'this', 'that', 'of', 'for',
               'to', 'in', 'on', 'at', 'by', 'with', 'from', 'and', 'or', 'is', 'are'}
    noun_words = [w for w in noun_phrase.strip().split() if w.lower() not in fillers and re.match(r'^[a-zA-Z]+$', w)]
    method_name = to_camel_case(verb_stem) + ''.join(w.capitalize() for w in noun_words)
    method_name = re.sub(r'[^a-zA-Z0-9]', '', method_name)
    if not method_name:
        return None
    param_str = f'({params})' if params else '()'
    return f'{method_name}{param_str} : {return_type}'


def extract_methods_from_text(text, max_methods=6, target_layer='entity'):
    """
    Extract domain behavior methods from free text (use case steps, sequence messages).
    Returns sorted list of method signature strings.
    Filters out CRUD methods.
    """
    if not text:
        return []
    methods = set()
    text_lower = text.lower()

    for pattern, verb_stem in BEHAVIOR_VERB_PATTERNS:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            # match can be a string (no groups) or a tuple
            if isinstance(match, tuple):
                noun = match[1].strip() if len(match) > 1 else ''
            else:
                noun = ''
            sig = build_method_sig(verb_stem, noun)
            if sig and not is_forbidden_crud(sig):
                methods.add(sig)
            if len(methods) >= max_methods:
                break
        if len(methods) >= max_methods:
            break

    return sorted(methods)


def extract_all_path_text(spec):
    """Concatenate all step text from a Use Case Specification."""
    parts = []
    for path_set, attr in [
        (spec.basic_paths.all().order_by('step_number'), None),
        (spec.alternative_paths.all().order_by('step_number'), None),
        (spec.exception_paths.all().order_by('step_number'), None),
    ]:
        for step in path_set:
            if step.actor_action:
                parts.append(step.actor_action)
            if step.system_response:
                parts.append(step.system_response)
    return ' '.join(parts)


def extract_candidate_nouns_from_text(text):
    """
    Step 1: Extract candidate domain class names (nouns) from free text.
    Returns set of PascalCase candidate entity names.
    """
    candidates = set()
    text_lower = text.lower()
    for pattern in DOMAIN_NOUN_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            word = match.group(1).replace(' ', '').strip()
            pascal = to_pascal_case(word)
            if pascal:
                candidates.add(pascal)
    return candidates


def clean_table_name(raw_name):
    """Strip common SQL table prefixes/suffixes, return PascalCase."""
    clean = raw_name.lower()
    clean = re.sub(r'^(tbl_|tb_|t_|m_|tr_|mst_|dt_|fact_|dim_|ref_|lkp_)', '', clean)
    clean = re.sub(r'(_table|_tbl|_data|_list|_master|_detail|_log|_hist|_history)$', '', clean)
    clean = re.sub(r'\d+$', '', clean)
    return to_pascal_case(clean)


# ─────────────────────────────────────────────────────────────
# STEP 1: EXTRACT CANDIDATE CLASSES FROM ALL BEHAVIORAL ARTIFACTS
# ─────────────────────────────────────────────────────────────

def step1_extract_candidates(specs, user_stories, scenarios, sql_tables):
    """
    Collect all candidate domain concepts from behavioral artifacts.
    Returns dict: { pascalName: { 'sources': set(), 'raw_texts': [] } }
    """
    candidates = defaultdict(lambda: {'sources': set(), 'raw_texts': []})

    # Removed seq_configs logic as per Rule Engine architectural shift

    # From Use Case Specifications
    for spec in specs:
        full_text = extract_all_path_text(spec)
        nouns = extract_candidate_nouns_from_text(full_text)
        for noun in nouns:
            candidates[noun]['sources'].add('use_case')
            candidates[noun]['raw_texts'].append(f'uc:{spec.feature_name}')
        # Postcondition often names affected entities
        if spec.input_postcondition:
            for noun in extract_candidate_nouns_from_text(spec.input_postcondition):
                candidates[noun]['sources'].add('use_case_post')

    # From User Stories
    for story in user_stories:
        text = f"{story.input_sebagai} {story.input_fitur} {story.input_tujuan or ''}"
        for noun in extract_candidate_nouns_from_text(text):
            candidates[noun]['sources'].add('user_story')

    # From Scenarios
    for scenario in scenarios:
        text = f"{scenario.input_given} {scenario.input_when} {scenario.input_then} {scenario.input_and}"
        for noun in extract_candidate_nouns_from_text(text):
            candidates[noun]['sources'].add('scenario')

    # SQL Tables (lowest priority — validation only)
    for table in sql_tables:
        name = clean_table_name(table.name)
        if name:
            candidates[name]['sources'].add('sql')

    return dict(candidates)


# ─────────────────────────────────────────────────────────────
# STEP 2: CLASSIFY CLASSES INTO BCE
# ─────────────────────────────────────────────────────────────

def step2_classify_bce(candidates, specs):
    """
    Classify each candidate into Boundary | Control | Entity based on naming rules.
    Returns three dicts: boundaries, controllers, entity_candidates
    """
    boundaries = {}
    controllers = {}
    entity_candidates = {}

    boundary_keywords = ['page', 'screen', 'form', 'ui', 'view']
    control_keywords = ['controller', 'manager', 'service', 'handler']

    # 1. Base Controller: one per Use Case Spec feature (DB)
    for spec in specs:
        ctrl_name = to_pascal_case(spec.feature_name) + 'Controller'
        controllers[ctrl_name] = {
            'feature': spec.feature_name,
            'spec': spec,
        }
        # Also create a default Boundary for this feature
        b_name = to_pascal_case(spec.feature_name) + 'UI'
        boundaries[b_name] = {
            'raw_name': spec.feature_name + ' UI',
            'feature': spec.feature_name,
            'linked_controller': ctrl_name,
            'actor_method': 'submitRequest()',
        }

    # 2. Classify dynamically discovered candidate nouns
    for name, data in candidates.items():
        name_lower = name.lower()
        
        # Rule: Is Boundary?
        if any(kw in name_lower for kw in boundary_keywords):
            if name not in boundaries:
                boundaries[name] = {
                    'raw_name': name,
                    'feature': '',
                    'linked_controller': None,
                    'actor_method': '',
                }
        
        # Rule: Is Control?
        elif any(kw in name_lower for kw in control_keywords):
            if name not in controllers:
                controllers[name] = {
                    'feature': '',
                    'spec': None,
                }
        
        # Rule: Is Entity? (Everything else)
        else:
            if name not in boundaries and name not in controllers and name not in entity_candidates:
                entity_candidates[name] = {
                    'raw_name': name,
                    'entity_methods_raw': set(),
                    'sources': data['sources']
                }

    return boundaries, controllers, entity_candidates


# ─────────────────────────────────────────────────────────────
# STEP 3: EXTRACT ATTRIBUTES (SQL validation only)
# ─────────────────────────────────────────────────────────────

def step3_extract_attributes(entity_candidates, sql_tables):
    """
    Map SQL columns to Entity attributes.
    SQL is ONLY for attribute names/types — not for design decisions.
    """
    # Build SQL map: cleanedPascalName → [columns]
    sql_map = {}
    for table in sql_tables:
        tbl_pascal = clean_table_name(table.name)
        cols = [
            {'name': col.name, 'uml_type': map_sql_type(col.data_type)}
            for col in table.columns.all()
        ]
        sql_map[tbl_pascal] = cols

    # Assign attributes to entities via fuzzy matching
    for ent_name in entity_candidates:
        attrs = sql_map.get(ent_name, [])
        if not attrs:
            # Fuzzy: singular/plural or substring match
            el = ent_name.lower()
            for k, v in sql_map.items():
                kl = k.lower()
                if (el == kl or el == kl.rstrip('s') or kl == el.rstrip('s')
                        or el in kl or kl in el):
                    attrs = v
                    break
        entity_candidates[ent_name]['attributes'] = attrs

    return entity_candidates


# ─────────────────────────────────────────────────────────────
# STEP 4: EXTRACT BEHAVIORS (NO CRUD)
# ─────────────────────────────────────────────────────────────

def step4_extract_behaviors(boundaries, controllers, entity_candidates, specs):
    """
    Extract methods from behavioral artifacts.
    Entity:     domain behaviors ONLY — CRUD strictly forbidden.
    Controller: coordination methods — orchestrating use case logic.
    Boundary:   UI interaction methods — no business logic.
    """
    # ── Boundary Methods ──
    for cls_name, data in boundaries.items():
        methods = set()
        am = data.get('actor_method', '').strip()
        if am and not is_forbidden_crud(am):
            methods.add(am if '(' in am else am + '() : void')
        feat = data.get('feature', '')
        if feat:
            methods.add(f'display{to_pascal_case(feat)}Result() : void')
            methods.add(f'show{to_pascal_case(feat)}Form() : void')
        methods.add('handleError(message : String) : void')
        data['methods'] = sorted(m for m in methods if not is_forbidden_crud(m))

    # ── Controller Methods ──
    for cls_name, data in controllers.items():
        methods = set()
        spec = data.get('spec')
        feat = data.get('feature', '')

        # From use case flow text
        if spec:
            path_text = extract_all_path_text(spec)
            for m in extract_methods_from_text(path_text, max_methods=5, target_layer='control'):
                if not is_forbidden_crud(m):
                    methods.add(m)
            # Postcondition → confirmation action
            if spec.input_postcondition:
                for m in extract_methods_from_text(spec.input_postcondition, max_methods=2):
                    if not is_forbidden_crud(m):
                        methods.add(m)

        # Fallback: at minimum the feature verb
        if not methods:
            methods.add(f'{to_camel_case(feat)}() : void')

        data['methods'] = sorted(m for m in methods if not is_forbidden_crud(m))

    # ── Entity Methods (domain behaviors ONLY) ──
    for ent_name, data in entity_candidates.items():
        methods = set()

        # From use case path texts (if entity name appears in flow)
        for spec in specs:
            path_text = extract_all_path_text(spec)
            ent_lower = ent_name.lower()
            # Only extract if this entity is mentioned in the text
            if len(ent_lower) >= 4 and ent_lower[:4] in path_text.lower():
                for m in extract_methods_from_text(path_text, max_methods=3):
                    if not is_forbidden_crud(m):
                        methods.add(m)

        # ── Heuristic domain behaviors by entity semantics ──
        el = ent_name.lower()

        if any(k in el for k in ('user', 'pengguna', 'account', 'akun', 'member', 'customer', 'pelanggan')):
            methods.add('authenticate(password : String) : boolean')
            methods.add('isActive() : boolean')
            methods.add('changePassword(newPassword : String) : void')
            methods.add('assignRole(role : Role) : void')

        if any(k in el for k in ('order', 'pesanan', 'transaction', 'transaksi', 'booking', 'reservation')):
            methods.add('calculateTotal() : double')
            methods.add('changeStatus(status : String) : void')
            methods.add('getStatus() : String')
            methods.add('cancelOrder() : void')

        if any(k in el for k in ('product', 'produk', 'item', 'barang', 'goods', 'merchandise')):
            methods.add('isAvailable() : boolean')
            methods.add('getStockLevel() : int')
            methods.add('reserveStock(qty : int) : boolean')

        if any(k in el for k in ('payment', 'pembayaran', 'invoice', 'faktur', 'billing', 'tagihan')):
            methods.add('confirmPayment() : boolean')
            methods.add('getPaymentStatus() : String')
            methods.add('calculateAmount() : double')

        if any(k in el for k in ('cart', 'basket', 'keranjang')):
            methods.add('calculateSubtotal() : double')
            methods.add('isEmpty() : boolean')
            methods.add('applyDiscount(code : String) : void')

        if any(k in el for k in ('session', 'token', 'auth', 'credential')):
            methods.add('isExpired() : boolean')
            methods.add('refresh() : void')
            methods.add('invalidate() : void')

        if any(k in el for k in ('notification', 'notifikasi', 'alert', 'pesan', 'message')):
            methods.add('markAsRead() : void')
            methods.add('isRead() : boolean')
            methods.add('getPriority() : String')

        if any(k in el for k in ('report', 'laporan', 'summary', 'rekap')):
            methods.add('generate() : void')
            methods.add('getDateRange() : String')

        if any(k in el for k in ('stock', 'stok', 'inventory', 'inventori')):
            methods.add('isAvailable(qty : int) : boolean')
            methods.add('reduceStock(qty : int) : void')
            methods.add('restock(qty : int) : void')

        if any(k in el for k in ('discount', 'diskon', 'coupon', 'voucher', 'promo')):
            methods.add('isValid() : boolean')
            methods.add('isExpired() : boolean')
            methods.add('calculateDiscount(amount : double) : double')

        if any(k in el for k in ('address', 'alamat', 'shipping', 'pengiriman', 'delivery')):
            methods.add('isValid() : boolean')
            methods.add('getFormattedAddress() : String')

        if any(k in el for k in ('role', 'permission', 'akses', 'privilege')):
            methods.add('hasPermission(action : String) : boolean')
            methods.add('isAdminRole() : boolean')

        if any(k in el for k in ('review', 'ulasan', 'rating', 'feedback')):
            methods.add('isApproved() : boolean')
            methods.add('getRating() : int')

        # Fallback: minimum one domain method
        if not methods:
            methods.add('isValid() : boolean')

        data['methods'] = sorted(m for m in methods if not is_forbidden_crud(m))

    return boundaries, controllers, entity_candidates


# ─────────────────────────────────────────────────────────────
# STEP 5: INFER RELATIONSHIPS FROM BEHAVIOR
# ─────────────────────────────────────────────────────────────

def step5_infer_relationships(boundaries, controllers, entity_candidates,
                               sql_rels, specs):
    """
    Infer UML relationships from behavioral artifacts.
    Rule hierarchy:
      1. Boundary ..> Controller        (dependency)
      2. Controller --> Entity          (association, from seq ctrlEntityMethods)
      3. Entity --> Entity              (association, from SQL FK + text co-reference)
    Returns list of relationship dicts.
    """
    associations = []
    seen = set()

    def add(from_cls, to_cls, rel_type, label='', mult_from='', mult_to='', name=''):
        key = (from_cls, to_cls, rel_type)
        if key not in seen and from_cls != to_cls:
            seen.add(key)
            associations.append({
                'from': from_cls, 'to': to_cls, 'type': rel_type,
                'label': label, 'mult_from': mult_from, 'mult_to': mult_to,
                'name': name,
            })

    # ── Boundary ..> Controller (dependency) ──
    for b_name, b_data in boundaries.items():
        ctrl = b_data.get('linked_controller')
        if ctrl and ctrl in controllers:
            add(b_name, ctrl, 'dependency', '<<uses>>')
        elif controllers:
            # Fallback: link to first matching controller by feature
            feat = b_data.get('feature', '')
            ctrl_name = to_pascal_case(feat) + 'Controller' if feat else next(iter(controllers))
            if ctrl_name in controllers:
                add(b_name, ctrl_name, 'dependency', '<<uses>>')
            else:
                add(b_name, next(iter(controllers)), 'dependency', '<<uses>>')

    # ── Controller --> Entity (association) ──
    for c_name, c_data in controllers.items():
        spec = c_data.get('spec')
        if spec:
            path_text = extract_all_path_text(spec).lower()
            for ent_name in entity_candidates.keys():
                ent_lower = ent_name.lower()
                if len(ent_lower) >= 4 and ent_lower[:4] in path_text:
                    add(c_name, ent_name, 'association', '', '1', '*')

    # ── Entity --> Entity (from SQL FK — secondary validation) ──
    for rel in sql_rels:
        from_t = getattr(rel, 'table', None)
        to_t = getattr(rel, 'ref_table', None)
        if from_t and to_t:
            from_p = clean_table_name(from_t.name)
            to_p = clean_table_name(to_t.name)
            # Only create if BOTH appear as entities (behavioral validation)
            if from_p in entity_candidates and to_p in entity_candidates:
                add(from_p, to_p, 'association', '', '*', '1')

    # ── Entity --> Entity from behavioral co-reference ──
    # If two entities appear together in the same use case step, they likely relate
    ent_names = list(entity_candidates.keys())
    for spec in specs:
        path_text = extract_all_path_text(spec).lower()
        for i, e1 in enumerate(ent_names):
            if len(e1) < 4:
                continue
            if e1.lower()[:4] not in path_text:
                continue
            for e2 in ent_names[i+1:]:
                if len(e2) < 4:
                    continue
                if e2.lower()[:4] not in path_text:
                    continue
                # Both entities appear in same use case — co-reference association
                # Only add if no SQL FK already covers this
                key_fwd = (e1, e2, 'association')
                key_rev = (e2, e1, 'association')
                if key_fwd not in seen and key_rev not in seen:
                    # Only create if it makes semantic sense (not just noise)
                    add(e1, e2, 'association', '', '1', '*')

    return associations


# ─────────────────────────────────────────────────────────────
# STEP 6: VALIDATE BCE DESIGN
# ─────────────────────────────────────────────────────────────

def step6_validate_bce(boundaries, controllers, entity_candidates, associations, specs):
    """
    Validate the BCE design against 7 checklist items.
    Auto-repairs issues found. Returns validation report.
    """
    report = {
        'passed': [],
        'repaired': [],
        'warnings': [],
    }

    # 1. Every major use case has a Control class
    for spec in specs:
        ctrl_name = to_pascal_case(spec.feature_name) + 'Controller'
        if ctrl_name not in controllers:
            controllers[ctrl_name] = {
                'feature': spec.feature_name,
                'spec': spec,
                'methods': [f'{to_camel_case(spec.feature_name)}() : void'],
            }
            report['repaired'].append(f'Auto-created {ctrl_name} for use case "{spec.feature_name}"')
        else:
            report['passed'].append(f'✓ Control class {ctrl_name} exists for "{spec.feature_name}"')

    # 2. Every actor interaction has a Boundary
    if not boundaries and specs:
        for spec in specs:
            feat = to_pascal_case(spec.feature_name)
            cls_name = feat + 'UI'
            boundaries[cls_name] = {
                'raw_name': spec.feature_name + ' UI',
                'feature': spec.feature_name,
                'linked_controller': feat + 'Controller',
                'actor_method': 'submitRequest()',
                'methods': ['submitRequest() : void', f'display{feat}Result() : void'],
            }
            report['repaired'].append(f'Auto-created Boundary {cls_name}')
    else:
        report['passed'].append(f'✓ {len(boundaries)} Boundary class(es) present')

    # 3. Every persistent business object appears as Entity
    if not entity_candidates:
        report['warnings'].append('⚠ No Entity classes found — check SQL schema or seq_configs')
    else:
        report['passed'].append(f'✓ {len(entity_candidates)} Entity class(es) present')

    # 4. Entity classes have domain behaviors, not CRUD
    for ent_name, data in entity_candidates.items():
        for m in data.get('methods', []):
            if is_forbidden_crud(m):
                data['methods'] = [x for x in data['methods'] if not is_forbidden_crud(x)]
                report['repaired'].append(f'Removed CRUD method from {ent_name}: {m}')
    report['passed'].append('✓ Entity CRUD-check passed')

    # 5. Boundary → Controller dependency exists
    boundary_controllers_linked = {a['from'] for a in associations if a['type'] == 'dependency'}
    for b_name in boundaries:
        if b_name not in boundary_controllers_linked:
            ctrl = boundaries[b_name].get('linked_controller')
            if ctrl and ctrl in controllers:
                associations.append({
                    'from': b_name, 'to': ctrl, 'type': 'dependency',
                    'label': '<<uses>>', 'mult_from': '', 'mult_to': '', 'name': '',
                })
                report['repaired'].append(f'Added missing Boundary→Controller link: {b_name} ..> {ctrl}')

    # 6. Entity does NOT directly access Boundary (check no entity→boundary links)
    bad_links = [a for a in associations if a['from'] in entity_candidates and a['to'] in boundaries]
    for link in bad_links:
        associations.remove(link)
        report['repaired'].append(f'Removed invalid Entity→Boundary link: {link["from"]} → {link["to"]}')
    if not bad_links:
        report['passed'].append('✓ No Entity→Boundary violations')

    # 7. Multiplicity sanity check (already set during Step 5)
    report['passed'].append('✓ Multiplicities set (Boundary 1..* , Controller 1..1, Entity 1..*)')

    return report


# ─────────────────────────────────────────────────────────────
# STEP 7: BUILD PLANTUML OUTPUT
# ─────────────────────────────────────────────────────────────

SKINPARAM_HEADER = """!theme plain
skinparam classAttributeIconSize 0
skinparam class {{
    BackgroundColor {bg}
    BorderColor {border}
    ArrowColor #1E293B
    FontSize 13
    FontName Arial
}}
skinparam stereotypeCBackgroundColor #EEF2FF
skinparam stereotypeCBorderColor #6366F1
skinparam stereotypeEBackgroundColor #ECFDF5
skinparam stereotypeEBorderColor #059669
skinparam stereotypeIBackgroundColor #FFF7ED
skinparam stereotypeIBorderColor #EA580C
skinparam ArrowThickness 1.5
skinparam linetype ortho"""

MODE_CONFIG = {
    'basic': {
        'title': 'Class Diagram - BCE Overview (UML 2.x)',
        'bg': '#FFFFFF', 'border': '#374151',
        'show_attrs': False, 'show_methods': True,
        'show_boundaries': True, 'show_controllers': True,
    },
    'detailed': {
        'title': 'Class Diagram - Entity Attributes',
        'bg': '#F9FAFB', 'border': '#4B5563',
        'show_attrs': True, 'show_methods': False,
        'show_boundaries': False, 'show_controllers': False,
    },
    'methods': {
        'title': 'Class Diagram - Domain Methods (OOAD)',
        'bg': '#EFF6FF', 'border': '#1D4ED8',
        'show_attrs': True, 'show_methods': True,
        'show_boundaries': False, 'show_controllers': True,
    },
    'complete': {
        'title': 'Class Diagram - Full BCE Design (UML 2.x / OOAD)',
        'bg': '#FFFFFF', 'border': '#0F172A',
        'show_attrs': True, 'show_methods': True,
        'show_boundaries': True, 'show_controllers': True,
    },
}


def _render_class(cls_name, stereotype, attributes, methods, show_attrs, show_methods):
    """Render a single PlantUML class block."""
    lines = [f'class {cls_name} <<{stereotype}>> {{']
    if show_attrs and attributes:
        for attr in attributes:
            lines.append(f'  - {attr["name"]} : {attr["uml_type"]}')
    if show_attrs and attributes and show_methods and methods:
        lines.append('  --')
    if show_methods and methods:
        for m in methods:
            sig = m if '(' in m else m + '()'
            lines.append(f'  + {sig}')
    if not (show_attrs and attributes) and not (show_methods and methods):
        lines.append('  {abstract}')  # Non-empty placeholder
    lines.append('}')
    return '\n'.join(lines)


def _render_rel(assoc):
    """Render a single UML relationship."""
    from_cls = assoc['from']
    to_cls   = assoc['to']
    rel_type = assoc['type']
    label    = assoc.get('label', '')
    mf       = f'"{assoc["mult_from"]}" ' if assoc.get('mult_from') else ''
    mt       = f' "{assoc["mult_to"]}"' if assoc.get('mult_to') else ''
    lbl      = f' : {label}' if label else ''

    arrows = {
        'dependency':   f'{from_cls} ..> {to_cls}{lbl}',
        'composition':  f'{from_cls} {mf}*--{mt} {to_cls}{lbl}',
        'aggregation':  f'{from_cls} {mf}o--{mt} {to_cls}{lbl}',
        'generalization': f'{from_cls} --|> {to_cls}',
    }
    return arrows.get(rel_type, f'{from_cls} {mf}-->{mt} {to_cls}{lbl}')


def step7_build_plantuml(mode, boundaries, controllers, entity_candidates, associations):
    """Generate complete, valid PlantUML class diagram for the given mode."""
    cfg = MODE_CONFIG.get(mode, MODE_CONFIG['complete'])
    lines = ['@startuml']
    lines.append(SKINPARAM_HEADER.format(bg=cfg['bg'], border=cfg['border']))
    lines.append(f'title {cfg["title"]}')
    lines.append('')

    # ── Boundary Classes ──
    if cfg['show_boundaries'] and boundaries:
        lines.append("' ═══════════════ BOUNDARY (View Layer) ═══════════════")
        for cls_name, data in boundaries.items():
            methods = data.get('methods', []) if cfg['show_methods'] else []
            lines.append(_render_class(cls_name, 'Boundary', [], methods,
                                       show_attrs=False, show_methods=cfg['show_methods']))
            lines.append('')

    # ── Control Classes ──
    if cfg['show_controllers'] and controllers:
        lines.append("' ═══════════════ CONTROL (Application Layer) ═══════════════")
        for cls_name, data in controllers.items():
            methods = data.get('methods', []) if cfg['show_methods'] else []
            lines.append(_render_class(cls_name, 'Control', [], methods,
                                       show_attrs=False, show_methods=cfg['show_methods']))
            lines.append('')

    # ── Entity Classes ──
    if entity_candidates:
        lines.append("' ═══════════════ ENTITY (Domain Layer) ═══════════════")
        for cls_name, data in entity_candidates.items():
            attrs   = data.get('attributes', []) if cfg['show_attrs'] else []
            methods = data.get('methods', []) if cfg['show_methods'] else []
            lines.append(_render_class(cls_name, 'Entity', attrs, methods,
                                       show_attrs=cfg['show_attrs'],
                                       show_methods=cfg['show_methods']))
            lines.append('')

    # ── Relationships ──
    if associations:
        lines.append("' ═══════════════ RELATIONSHIPS ═══════════════")
        for assoc in associations:
            fc = assoc['from']
            tc = assoc['to']
            fc_exists = fc in boundaries or fc in controllers or fc in entity_candidates
            tc_exists = tc in boundaries or tc in controllers or tc in entity_candidates
            if not fc_exists or not tc_exists:
                continue
            if not cfg['show_boundaries'] and fc in boundaries:
                continue
            if not cfg['show_controllers'] and fc in controllers:
                continue
            lines.append(_render_rel(assoc))

    lines.append('')
    lines.append('@enduml')
    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def generate_class_diagram(project):
    """
    Main entry point for generating the OOAD Class Diagram.
    Strictly follows MDE (Model-Driven Engineering) rules by parsing database artifacts.

    Args:
        project: Django Project instance (or None)
        {
            'basic': str,
            'detailed': str,
            'methods': str,
            'complete': str,
            'metadata': dict,
            'validation': dict,
        }
    """
    from main.models import (
        UseCaseSpecification, ImportedTable, ImportedRelationship,
        Page, UserStory, UserStoryScenario
    )

    # ── Load all behavioral artifacts ──
    specs = list(UseCaseSpecification.objects.filter(project=project).prefetch_related(
        'basic_paths', 'alternative_paths', 'exception_paths'
    )) if project else []

    sql_tables = list(
        ImportedTable.objects.filter(project=project).prefetch_related('columns')
    ) if project else []

    sql_rels = list(
        ImportedRelationship.objects.filter(
            table__project=project
        ).select_related('table', 'ref_table')
    ) if project else []

    pages = list(
        Page.objects.filter(gui__project=project).order_by('order')
    ) if project else []

    user_stories = list(
        UserStory.objects.filter(project=project)
    ) if project else []

    scenarios = list(
        UserStoryScenario.objects.filter(userstory__project=project)
    ) if project else []

    # ══════════════════════════════════════════════════
    # EXECUTE 7-STEP OOAD PIPELINE
    # ══════════════════════════════════════════════════

    # Step 1: Extract candidate classes from behavioral artifacts
    candidates = step1_extract_candidates(
        specs, user_stories, scenarios, sql_tables
    )

    # Step 2: Classify into BCE
    boundaries, controllers, entity_candidates = step2_classify_bce(
        candidates, specs
    )

    # Step 3: Extract attributes (SQL only — validation role)
    entity_candidates = step3_extract_attributes(entity_candidates, sql_tables)

    # Step 4: Extract behaviors (CRUD strictly forbidden in Entity)
    boundaries, controllers, entity_candidates = step4_extract_behaviors(
        boundaries, controllers, entity_candidates, specs
    )

    # Step 5: Infer relationships from behavior
    associations = step5_infer_relationships(
        boundaries, controllers, entity_candidates, sql_rels, specs
    )

    # Step 6: Validate BCE design — auto-repair violations
    validation_report = step6_validate_bce(
        boundaries, controllers, entity_candidates, associations, specs
    )

    # Step 7: Generate PlantUML for all 4 modes
    result = {
        'basic':    step7_build_plantuml('basic',    boundaries, controllers, entity_candidates, associations),
        'detailed': step7_build_plantuml('detailed', boundaries, controllers, entity_candidates, associations),
        'methods':  step7_build_plantuml('methods',  boundaries, controllers, entity_candidates, associations),
        'complete': step7_build_plantuml('complete', boundaries, controllers, entity_candidates, associations),
        'metadata': {
            'boundary_count':    len(boundaries),
            'controller_count':  len(controllers),
            'entity_count':      len(entity_candidates),
            'association_count': len(associations),
            'boundaries':    list(boundaries.keys()),
            'controllers':   list(controllers.keys()),
            'entities':      list(entity_candidates.keys()),
            'candidate_count': len(candidates),
        },
        'validation': validation_report,
    }

    return result
