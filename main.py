import questionary
import os
import json
import shutil
import sys
import requests

LOCAL_VERSION = "0.3.1"
jsonfile = "settings.json"

def update():
    try:
        response = requests.get("https://raw.githubusercontent.com/rimsiw/tlou2-mod-manager/refs/heads/main/version", timeout=5)
        if response.status_code == 200:
            LATEST_VERSION = response.text.strip()
            if LATEST_VERSION != LOCAL_VERSION:
                print(f"\n\n[UPDATE] This version is outdated.\nCurrent Version: {LOCAL_VERSION}\nVersion Found: {LATEST_VERSION}\nDownload the new version at https://www.nexusmods.com/thelastofuspart2/mods/170\n\n")
    except Exception as e:
        print(f"\nCould not check for updates: {e}.")

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
            sys.exit()

def mod_data():
    datadir = os.path.join(os.getcwd(), "data")
    librarydir = os.path.join(datadir, "mods")
    profilesdir = os.path.join(datadir, "profiles")

    for d in [datadir, librarydir, profilesdir]:
        if not os.path.exists(d):
            os.makedirs(d)

    return librarydir, profilesdir

def add_mods(librarydir):
    """Add mods using text-based path input"""
    print("\n=== Add Mods ===")

    while True:
        mod_path = questionary.path(message='Enter the full path to the mod file (.psarc) containing mods.').ask()

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
            destination = os.path.join(librarydir, file_name)

            try:
                shutil.copy2(mod_path, destination)
                print(f"Successfully added mod '{file_name}' to the library.")
            except Exception as e:
                print(f"Failed to add {file_name}: {str(e)}")

        # Feature for directories in the works

        add_more = questionary.confirm(message='Add more?')
        if add_more != True:
            break

def save_profile(librarydir, profilesdir):
    mods = [f for f in os.listdir(librarydir) if f.endswith('.psarc')]

    if not mods:
        print("No mods found in the library.")
        return
    
    selections = questionary.checkbox("Select mods for this profile.", choices=mods).ask()
    if not selections:
        print("No mods were selected.")
        return
    
    profilename = questionary.text("Please enter a name for this profile:").ask()
    if not profilename:
        print("Profile name cannot be empty.")
        return

    profilepath = os.path.join(profilesdir, f"{profilename}.json")
    profiledata = {
        "mods": selections
    }

    with open(profilepath, 'w', encoding='utf-8') as f:
        json.dump(profiledata, f, indent=4)

    print(f"Profile '{profilename}' has been saved")

def load_profile(modsdir, profilesdir, librarydir):
    profiles = [f[:-5] for f in os.listdir(profilesdir) if f.endswith('.json')]

    if not profiles:
        print("No profiles available at the current moment.")
        return
    
    profileselected = questionary.select("Select a profile to load:", choices=profiles).ask()
    if not profileselected:
        return
    
    profilepath = os.path.join(profilesdir, f"{profileselected}.json")
    with open(profilepath, 'r', encoding='utf-8') as f:
        profile = json.load(f)
    
    enabled_future = profile.get("mods", [])

    for f in os.listdir(modsdir):
        fullpath = os.path.join(modsdir, f)
        try:
            if os.path.isfile(fullpath) or os.path.islink(fullpath):
                os.remove(fullpath)
            elif os.path.isdir(fullpath):
                shutil.rmtree(fullpath)
        except Exception as e:
            print(f"Failed to delete {fullpath}: {e}")

    for mod in enabled_future:
        src = os.path.join(librarydir, mod)
        dest = os.path.join(modsdir, mod)
        if os.path.exists(src):
            shutil.copy2(src, dest)
            print(f"Activated: {mod}")
        else:
            print(f"Mod {mod} is missing in the library")

    print(f"Selected profile '{profileselected} has been loaded")

def delete_profile(profilesdir):
    profiles = [f[:-5] for f in os.listdir(profilesdir) if f.endswith('.json')]

    if not profiles:
        print("No profiles to delete")
        return

    profileselected = questionary.select("Select a profile to delete:", choices=profiles).ask()

    profilepath = os.path.join(profilesdir, f"{profileselected}.json")
    try:
        os.remove(profilepath)
        print(f"Profile '{profileselected} has been deleted")
    except Exception as e:
        print(f"Failed to delete profile: {str(e)}")

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
            sys.exit()

    tloupath = os.path.expanduser(opt['filepath'])

    modsdir = os.path.join(tloupath, "mods")
    disableddir = os.path.join(modsdir, "disabled")

    if not os.path.exists(disableddir):
        os.makedirs(disableddir)

    if not os.path.exists(modsdir):
        os.makedirs(modsdir)

    librarydir, profilesdir = mod_data()

    while True:
        choice = questionary.select(
            "What do you want to do?",
            choices=[
                'Change The Path',
                'Add mods to the library',
                'Create a profile',
                'Load a profile',
                'Delete a profile',
                'Exit'
            ]).ask()

        if choice == 'Change The Path':
            question_setup()
            main()
            return
        elif choice == 'Add mods to the library':
            add_mods(librarydir)
        elif choice == 'Create a profile':
            save_profile(librarydir, profilesdir)
        elif choice == 'Load a profile':
            load_profile(modsdir, profilesdir, librarydir)
        elif choice == 'Delete a profile':
            delete_profile(profilesdir)
        elif choice == 'Exit':
            print("Exiting program. Goodbye!")
            break

if __name__ == "__main__":
    print("=== The Last of Us Part II Mod Manager ===")
    main()
