import os
import shutil
from pathlib import Path

# This file is executed by Cookiecutter after the project is generated.
# It moves the selected topology template folder to the project root and removes
# any other unused template folders.

selected_template = "{{ cookiecutter.topology_template }}"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"

def _resolve_template_dir(choice):
    choice_name = choice
    if not TEMPLATES_DIR.exists():
        return None
    
    for candidate in TEMPLATES_DIR.iterdir():
        if candidate.is_dir() and candidate.name.lower() == choice_name.lower():
            return candidate

    return None


def _remove_other_templates(keep_name):
    if not TEMPLATES_DIR.exists():
        return

    for candidate in TEMPLATES_DIR.iterdir():
        if candidate.is_dir() and candidate.name != keep_name:
            shutil.rmtree(candidate)

    try:
        if not any(TEMPLATES_DIR.iterdir()):
            TEMPLATES_DIR.rmdir()
            
    except OSError:
        pass


def main():
    selected_dir = _resolve_template_dir(selected_template)
    
    if selected_dir is None:
        print(f"(!!) Could not find template folder for '{selected_template}' in {TEMPLATES_DIR}")
        return

    target_dir = PROJECT_ROOT / selected_template
    
    if selected_dir.resolve() != target_dir.resolve():
        selected_dir.rename(target_dir)
    else:
        # move the selected directory out of templates to the project root
        target_dir = PROJECT_ROOT / selected_dir.name
        if not target_dir.exists():
            selected_dir.rename(target_dir)

    _remove_other_templates(selected_template)
    print(f"Selected template '{selected_template}' and removed other template folders.")


if __name__ == '__main__':
    main()
