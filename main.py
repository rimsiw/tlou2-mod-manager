import questionary
import os
import json
import shutil

jsonfile = "settings.json"

def settings(responses, filename=jsonfile):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(responses, f, indent=4)

def settings_load(filename=jsonfile):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def question_setup():
    print("\n=== The Last of Us Part II Mod Manager ===")
    print("Please set the path to your game installation directory.")

    question = [
        {
            'type': 'path',
            'name': 'filepath',
            'message': 'Please select The Last Of Us Part II directory on your disk:',
            'only_directories': True,
        }
    ]

    responses = questionary.prompt(question)

    if responses and 'filepath' in responses:
        path = os.path.expanduser(responses['filepath'])
        if not os.path.exists(path):
            print(f"\nWarning: The path '{path}' does not exist.")
            if not questionary.confirm("Continue with this path anyway?").ask():
                return question_setup()
        settings(responses)
        print(f"\nYour path has been saved: {path}")
        return responses
    else:
        print(f"\nPath selection was cancelled.")
        if questionary.confirm("Would you like to try again?").ask():
            return question_setup()
        else:
            print("Exiting program as no path was set.")
            exit()

def add_mods(modsdir):
    """Add mods using text-based path input"""
    print("\n=== Add Mods ===")

    while True:
        mod_path = questionary.path(message='Enter the full path to the mod file (.psarc) or directory containing mods.',).ask()

        mod_path = os.path.expanduser(mod_path)
        if not os.path.exists(mod_path):
            print(f"Error: Path '{mod_path}' does not exist.")
            continue

        if os.path.isfile(mod_path):
            if not mod_path.lower().endswith('.psarc'):
                print("")
                confirm = questionary.confirm(message='Warning: The file does not have a .psarc extension. Are you sure this is a mod file?').ask()
                if confirm != True:
                    continue

            file_name = os.path.basename(mod_path)
            destination = os.path.join(modsdir, file_name)

            try:
                shutil.copy2(mod_path, destination)
                print(f"Successfully added mod: {file_name}")
            except Exception as e:
                print(f"Failed to add {file_name}: {str(e)}")

        # Feature for directories in the works

        add_more = questionary.confirm(message='Add more?')
        if add_more != True:
            break

def main():
    opt = settings_load()
    valid_settings = False

    if opt and 'filepath' in opt:
        tloupath = os.path.expanduser(opt['filepath'])
        if os.path.exists(tloupath):
            valid_settings = True

    if not valid_settings:
        print("No valid game path found. Setting up...")
        opt = question_setup()
        if not opt:
            print("Setup cancelled. Exiting.")
            exit()

    tloupath = os.path.expanduser(opt['filepath'])

    modsdir = os.path.join(tloupath, "mods")
    disableddir = os.path.join(modsdir, "disabled")

    if not os.path.exists(disableddir):
        os.makedirs(disableddir)

    if not os.path.exists(modsdir):
        os.makedirs(modsdir)

    modsf = [f for f in os.listdir(modsdir) 
    if os.path.isfile(os.path.join(modsdir, f)) and f.endswith(".psarc")]

    disabledf = [f for f in os.listdir(disableddir) 
    if os.path.isfile(os.path.join(disableddir, f)) and f.endswith(".psarc")]

    choice = questionary.select(
        "What do you want to do?",
        choices=[
            'Change The Path',
            'Add mods',
            'Enable/Disable mods',
            'Exit'
        ]).ask()

    if choice == 'Change The Path':
        question_setup()
        main()
        return
    elif choice == 'Add mods':
        add_mods(modsdir)
        main()
        return
    elif choice == 'Enable/Disable mods':
        modsall = modsf + disabledf

        if not modsall:
            print("No mods found. Please add some mods first.")
            input("Press Enter to continue...")
            main()
            return

        choices = [
            {
                'name': f,
                'checked': f in modsf
            }
            for f in modsall
        ]

        select = questionary.checkbox(
            'Select mods to enable (checked = enabled):',
            choices=choices
        ).ask()

        if select is None:
            main()
            return

        for f in modsall:
            enabled_now = f in modsf
            enabled_future = f in select

            if enabled_now and not enabled_future:
                try:
                    shutil.move(os.path.join(modsdir, f), os.path.join(disableddir, f))
                    print(f"Mod '{f}' is now disabled.")
                except Exception as e:
                    print(f"Error disabling '{f}': {str(e)}")

            elif not enabled_now and enabled_future:
                try:
                    shutil.move(os.path.join(disableddir, f), os.path.join(modsdir, f))
                    print(f"Mod '{f}' is now enabled.")
                except Exception as e:
                    print(f"Error enabling '{f}': {str(e)}")

        input("\nPress Enter to continue...")
        main()
        return
    elif choice == 'Exit':
        print("Exiting program. Goodbye!")
        return

if __name__ == "__main__":
    print("=== The Last of Us Part II Mod Manager ===")
    main()
