import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "settings.json")

def get_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"output_device": ""}

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)
