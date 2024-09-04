import json

def load_default_config():
    try:
        with open("config.json", "r") as file:
            config = json.load(file)
            return config
    except Exception as e:
        return {"adb_path": "", "adb_port": ""}
