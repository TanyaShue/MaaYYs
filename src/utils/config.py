import json
from utils.logger import Logger

def load_default_config():
    try:
        with open("assets/config/app_config.json", "r") as file:
            config = json.load(file)
            return config
    except Exception as e:
        Logger(None).add_log(f"读取配置文件失败: {e}")
        return {"adb_path": "", "adb_port": ""}
