import json
import os
from pathlib import Path

########## JSON DECLARATION ##########
# Right now, planned to hold things such as shot counter
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "values.json"
# print(DATA_FILE)

def load_values():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: JSON corrupted or empty. Resetting.")
            return {}
    else:
        return {}

def save_values(values):
    with open(DATA_FILE, "w") as f:
        json.dump(values, f, indent=4)

########## ########## ##########