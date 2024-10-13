import json

from src.utils.config_projects import ProjectsJson


def test_projects_json():
    # 模拟一个JSON数据作为测试数据
    json_data = {
        "projects": [
            {
                "project_name": "阴阳师1",
                "program_name": "阴阳师",
                "adb_config": {
                    "adb_path": "D:\\leidian\\LDPlayer9\\adb.exe",
                    "adb_address": "127.0.0.1:5555"
                },
                "selected_tasks": [
                    "自动地鬼",
                    "自动结界",
                    "自动悬赏",
                    "打开游戏",
                    "自动逢魔"
                ],
                "option": {
                    "选择区服": {
                        "select": "测试服"
                    },
                    "悬赏封印分组预设": {
                        "input": "默认分组"
                    },
                    "悬赏封印队伍预设": {
                        "input": "默认队伍"
                    },
                    "结界突破分组预设": {
                        "input": "默认队伍"
                    }
                }
            },
            {
                "project_name": "阴阳师2",
                "program_name": "阴阳师",
                "adb_config": {
                    "adb_path": "C:/Program Files/BlueStacks_nxt/HD-Adb.exe",
                    "adb_address": "127.0.0.1:5625"
                },
                "selected_tasks": [
                    "自动地鬼",
                    "打开游戏",
                    "启动加速器"
                ],
                "option": {}
            }
        ]
    }

    # 模拟将该数据写入到一个JSON文件并从中读取
    json_file = '../assets/config/projects.json'

    # with open(json_file, 'w', encoding='utf-8') as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=4)

    # 测试从文件中加载JSON并解析为对象
    projects_json = ProjectsJson.load_from_file(json_file)

    # 1. 获取所有的project
    projects = projects_json.projects
    print("所有的Projects:")
    for project in projects:
        print(f"- Project Name: {project.project_name}, Program Name: {project.program_name}")
        print(f"  ADB Path: {project.adb_config.adb_path}, ADB Address: {project.adb_config.adb_address}")
        print(f"  Selected Tasks: {project.selected_tasks}")
        if project.option:
            print(f"  Option: {project.option.to_json()}")


if __name__ == "__main__":
    test_projects_json()
