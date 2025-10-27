import re
import urllib.parse

# Configs
PLANTUML_SERVER = "http://www.plantuml.com/plantuml/img/"
MAX_USECASES_PER_DIAGRAM = 6

_ws_re = re.compile(r"\s+")

def _normalize_key(s: str) -> str:
    if not s:
        return ""
    s2 = s.strip().strip("\"'\"\"''()[]{}")
    s2 = _ws_re.sub(" ", s2)
    return s2.lower()

def _alias(prefix: str, idx: int) -> str:
    return f"{prefix}{idx}"

def generate_use_case_diagram(actors_data):
    """
    Generate PlantUML code from actors data
    """
    plantuml_code = "@startuml\nleft to right direction\nskinparam monochrome true\nskinparam shadowing false\n"
    
    # Add actors
    actor_aliases = {}
    for i, actor in enumerate(actors_data):
        if actor.get('name'):  # Only add actors with names
            alias = _alias("Actor", i)
            actor_aliases[actor['name']] = alias
            plantuml_code += f'actor "{actor["name"]}" as {alias}\n'
    
    # Add use cases
    use_case_counter = 0
    use_case_aliases = {}
    
    for actor in actors_data:
        for feature in actor.get('features', []):
            if feature.get('what') and feature.get('why'):
                alias = _alias("UC", use_case_counter)
                use_case_aliases[feature['what']] = alias
                plantuml_code += f'usecase "{feature["what"]}" as {alias}\n'
                use_case_counter += 1
    
    # Add relationships
    for actor in actors_data:
        actor_alias = actor_aliases.get(actor.get('name', ''))
        if actor_alias:
            for feature in actor.get('features', []):
                if feature.get('what') and feature.get('why'):
                    use_case_alias = use_case_aliases.get(feature['what'])
                    if use_case_alias:
                        plantuml_code += f'{actor_alias} --> {use_case_alias}\n'
    
    plantuml_code += "@enduml"
    return plantuml_code

def get_plantuml_url(plantuml_code):
    """
    Convert PlantUML code to URL using plantuml.com
    """
    # Encode the PlantUML code for URL
    import zlib
    import base64
    
    # PlantUML encoding format
    compressed = zlib.compress(plantuml_code.encode('utf-8'))
    encoded = base64.b64encode(compressed).decode('ascii')
    # Remove the first 2 bytes (zlib header) and decode
    encoded = encoded[1:]
    
    return f"{PLANTUML_SERVER}{encoded}"