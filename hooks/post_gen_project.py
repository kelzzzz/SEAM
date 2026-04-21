import os
import shutil
from pathlib import Path

# This file is executed by Cookiecutter after the project is generated.
# It moves the selected topology template folder to the project root and removes
# any other unused template folders. It also cleans up slice managers to keep only
# the abstract manager and the one matching the selected template.

selected_template = "{{ cookiecutter.topology_template }}"
TEMPLATES_DIR = Path("templates")
MANAGERS_DIR = Path("src") / "util" / "managers"

# mapping from template to manager file (without .py extension)
TEMPLATE_TO_MANAGER = "{{ cookiecutter.topology_template }}"+"_slice_manager"

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


def _cleanup_managers(keep_manager):
    if not MANAGERS_DIR.exists():
        return

    for candidate in MANAGERS_DIR.iterdir():
        if candidate.is_file() and candidate.suffix == '.py':
            if candidate.stem == 'abstract_slice_manager':
                continue  # always keep
            if candidate.stem == keep_manager:
                continue  # keep the matching one
            # remove others
            candidate.unlink()
            print(f"Removed unused manager: {candidate.name}")


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

    # clean up managers
    keep_manager = TEMPLATE_TO_MANAGER
    if keep_manager:
        _cleanup_managers(keep_manager)
        print(f"Kept abstract_slice_manager.py and {keep_manager}.py")
    else:
        print(f"No specific manager found for template '{selected_template}'; keeping only abstract_slice_manager.py")


if __name__ == "__main__":
    main()

