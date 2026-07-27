import os

target_dir = r"c:\semuacodingan\ONEUML\SRS-Generator-Tools\main\templates\main"
steps = {
    'use_case_diagram.html': 1,
    'user_story.html': 2,
    'input_informasi_tambahan.html': 3,
    'use_case_spec.html': 4,
    'activity_diagram.html': 5,
    'input_gui.html': 6,
    'user_scenario.html': 7,
    'sequence_diagram.html': 8,
    'import_sql.html': 9,
    'class_diagram.html': 10,
    'generate_srs.html': 11
}

for filename, step_num in steps.items():
    filepath = os.path.join(target_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has stepper
        if "{% include 'main/stepper.html'" in content:
            print(f"Stepper already in {filename}")
            continue
            
        stepper_code = f"\n    {{% include 'main/stepper.html' with current_step={step_num} %}}\n"
        
        # Check for <main>
        if '<main>' in content:
            content = content.replace('<main>', '<main>' + stepper_code, 1)
        elif '<div class="container"' in content:
            # find first instance of <div class="container"...>
            parts = content.split('<div class="container"', 1)
            end_bracket = parts[1].find('>')
            content = parts[0] + '<div class="container"' + parts[1][:end_bracket+1] + stepper_code + parts[1][end_bracket+1:]
        elif '<body>' in content:
            content = content.replace('<body>', '<body>' + stepper_code, 1)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added stepper to {filename}")

print("Done")
