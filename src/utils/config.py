import json
from utils.logger import Logger
import os

def load_default_config():
    print(os.getcwd())

    try:
        with open("assets/app_config.json", "r",encoding="utf-8") as file:
            config = json.load(file)
            return config
    except Exception as e:
        Logger().add_log(f"读取配置文件失败: {e}")
        return {"adb_path": "", "adb_port": ""}


def load_config_tasks():
    try:
        with open("assets/app_config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
            return config["task"]
    except Exception as e:
        Logger().add_log(f"读取配置文件失败: {e}")
        return {}
    
def get_task_entry(task_name):
    try:
        with open("assets/app_config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
            return config["task"][task_name]
    except Exception as e:
        Logger().add_log(f"读取配置文件失败: {e}")
        return {}