# query_profile_loader.py

import os
import yaml

def load_query_profiles(directory_path):
    profiles = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            full_path = os.path.join(directory_path, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        profiles.append(data)
                    else:
                        print(f"WARNUNG: Datei {filename} enthält kein gültiges YAML-Dictionary.")
            except Exception as e:
                print(f"Fehler beim Laden von {filename}: {e}")
    return profiles
