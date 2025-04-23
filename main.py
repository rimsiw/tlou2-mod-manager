import questionary
import os
import json
import shutil

jsonfile = "settings.json"

def settings(responses, filename = jsonfile):
    with open(filename, 'w', encoding = 'utf-8') as f:
        json.dump(responses, f, indent=4)

def settings_load(filename = jsonfile):
    if os.path.exists(filename):
        with open(filename, 'r', encoding = 'utf-8') as f:
            return json.load(f)
    return None

def question_setup():
    question = [
        {
            'type': 'path',
            'name': 'filepath',
            'message': 'Please select The Last Of Us Part II directory on your disk.',
            'only_directories': True,
        }
    ]

    responses = questionary.prompt(question)

    if responses:
        settings(responses)
        print(f"\nYour path has been saved.")
    else:
        print(f"\nYour path couldn't be saved.")

if not os.path.exists(jsonfile):
    question_setup()
    exit()
else:
    opt = settings_load()
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

    modsall = modsf + disabledf

    choices = [
        {
            'name': f,
            'checked': f in modsf
        }
        for f in modsall
    ]

    if not choices:
        print(f"\nNo valid files found.")
        exit()
    else:
        select = questionary.checkbox(
            "Enable and disable mods.",
            choices=choices
        ).ask()

    if select is None:
        print(f"\nNo changes were made")
        exit()

    for f in modsall:
        enabled_now = f in modsf
        enabled_future = f in select
        
        if enabled_now and not enabled_future:
            shutil.move(os.path.join(modsdir, f), os.path.join(disableddir, f))
            print(f"Mod '{f}' are now disabled.")
        elif not enabled_now and enabled_future:
            shutil.move(os.path.join(disableddir, f), os.path.join(modsdir, f))
            print(f"Mod '{f}' is now enabled.")
