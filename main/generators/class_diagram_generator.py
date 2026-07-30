import json
import base64

# class_diagram_generator.py
# Generator for Class Diagram strictly based on Sequence Diagram configs

def is_return_message(msg):
    msg = msg.strip().lower()
    return msg.startswith('return') or msg.startswith('menghasilkan') or msg in ('response', 'result', 'error', 'display result', 'show error', 'menampilkan pesan')

def format_operation(msg):
    msg = msg.strip()
    if not msg:
        return ''
    if '(' not in msg:
        msg = msg + '()'
    if not msg.startswith('+'):
        msg = '+' + msg
    return msg

def add_method_unique(methods_list, msg):
    if not msg or is_return_message(msg):
        return
    formatted = format_operation(msg)
    if formatted not in methods_list:
        methods_list.append(formatted)

def generate_class_diagram(project, seq_configs=None):
    if not seq_configs:
        seq_configs = []

    # In views.py, seq_configs comes from request.session.get('sequence_configs', {}) 
    # which is a dictionary. So if seq_configs is a dict, get its values.
    if isinstance(seq_configs, dict):
        seq_configs = seq_configs.values()

    boundaries = {}
    controllers = {}
    entities = {}
    associations = []
    
    for cfg in seq_configs:
        if hasattr(cfg, 'get'):
            feature_name = cfg.get('featureName') or cfg.get('feature_name') or 'Feature'
            b_name = cfg.get('boundaryName') or cfg.get('boundary_name') or (feature_name + 'UI')
            
            ab_methods = cfg.get('actorBoundaryMethods') or cfg.get('actor_boundary_methods') or []
            if not ab_methods:
                ab_single = cfg.get('actorBoundaryMethod') or cfg.get('actor_boundary_method') or ''
                if ab_single:
                    ab_methods = [ab_single]
                    
            b_selfs = cfg.get('boundary_self_calls') or []
            bc_method = cfg.get('boundaryCtrlMethod') or cfg.get('boundary_controller_method') or ''
            c_selfs = cfg.get('controller_self_calls') or []
            selected_ents = cfg.get('selectedEntities') or cfg.get('selected_entities') or []
            cem = cfg.get('ctrlEntityMethods') or cfg.get('ctrl_entity_methods') or {}
            
            alt_ab = cfg.get('alt_actor_boundary') or ''
            exc_ab = cfg.get('exc_actor_boundary') or ''
            alt_bs = cfg.get('alt_boundary_self') or ''
            exc_bs = cfg.get('exc_boundary_self') or ''
            alt_bc = cfg.get('alt_boundary_ctrl') or ''
            exc_bc = cfg.get('exc_boundary_ctrl') or ''
            
        else:
            continue
            
        c_name = feature_name.replace(" ", "") + 'Controller'
        if "UI" not in b_name and "Page" not in b_name and "Boundary" not in b_name and "Form" not in b_name:
            b_name = b_name + "UI"
        
        # Init classes
        if b_name not in boundaries:
            boundaries[b_name] = []
        if c_name not in controllers:
            controllers[c_name] = []
            
        # Add Boundary -> Controller relationship
        assoc_b_c = f'{b_name} --> {c_name}'
        if assoc_b_c not in associations:
            associations.append(assoc_b_c)
            
        # Actor -> Boundary
        for m in ab_methods:
            add_method_unique(boundaries[b_name], m)
            
        # Alt/Exc Actor -> Boundary
        add_method_unique(boundaries[b_name], alt_ab)
        add_method_unique(boundaries[b_name], exc_ab)
        
        # Boundary Self-calls
        for m in b_selfs:
            add_method_unique(boundaries[b_name], m)
        add_method_unique(boundaries[b_name], alt_bs)
        add_method_unique(boundaries[b_name], exc_bs)
        
        # Boundary -> Controller
        add_method_unique(controllers[c_name], bc_method)
        add_method_unique(controllers[c_name], alt_bc)
        add_method_unique(controllers[c_name], exc_bc)
        
        # Controller Self-calls
        for m in c_selfs:
            add_method_unique(controllers[c_name], m)
            
        # Entities & Controller -> Entity
        for ent in selected_ents:
            if ent not in entities:
                entities[ent] = []
            assoc_c_e = f'{c_name} --> {ent}'
            if assoc_c_e not in associations:
                associations.append(assoc_c_e)
                
        # Methods on Entities
        for ent_name, method_str in cem.items():
            if ent_name not in entities:
                entities[ent_name] = []
            add_method_unique(entities[ent_name], method_str)
            assoc_c_e = f'{c_name} --> {ent_name}'
            if assoc_c_e not in associations:
                associations.append(assoc_c_e)
                
    # Build PlantUML
    lines = [
        '@startuml',
        '!theme plain',
        'skinparam classAttributeIconSize 0',
        'skinparam linetype ortho',
        'skinparam ArrowThickness 1.5',
        ''
    ]
    
    # Render Boundaries
    for b_name, methods in boundaries.items():
        lines.append(f'class "{b_name}" as {b_name.replace(" ", "_")} <<boundary>> {{')
        for m in methods:
            lines.append(f'  {m}')
        if not methods:
            lines.append('  {abstract}')
        lines.append('}')
        lines.append('')
        
    # Render Controllers
    for c_name, methods in controllers.items():
        lines.append(f'class "{c_name}" as {c_name.replace(" ", "_")} <<control>> {{')
        for m in methods:
            lines.append(f'  {m}')
        if not methods:
            lines.append('  {abstract}')
        lines.append('}')
        lines.append('')
        
    # Render Entities
    for e_name, methods in entities.items():
        lines.append(f'class "{e_name}" as {e_name.replace(" ", "_")} <<entity>> {{')
        for m in methods:
            lines.append(f'  {m}')
        if not methods:
            lines.append('  {abstract}')
        lines.append('}')
        lines.append('')
        
    # Relationships
    for assoc in associations:
        parts = assoc.split(' --> ')
        if len(parts) == 2:
            left_alias = parts[0].replace(" ", "_")
            right_alias = parts[1].replace(" ", "_")
            lines.append(f'{left_alias} --> {right_alias}')
            
    lines.append('@enduml')
    plantuml_text = '\n'.join(lines)
    
    # Return standard result format
    report = {
        'passed': ['Class diagram generated strictly from sequence configs.'],
        'repaired': [],
        'warnings': []
    }
    
    return {
        'basic': plantuml_text,
        'detailed': plantuml_text,
        'methods': plantuml_text,
        'complete': plantuml_text,
        'metadata': {
            'boundary_count': len(boundaries),
            'controller_count': len(controllers),
            'entity_count': len(entities),
            'association_count': len(associations),
            'boundaries': list(boundaries.keys()),
            'controllers': list(controllers.keys()),
            'entities': list(entities.keys()),
            'candidate_count': len(boundaries) + len(controllers) + len(entities),
        },
        'validation': report,
    }
