import json

from src.utils.config_programs import ProgramsJson


# Assuming the previously provided classes are available

def test_programs_json():
    # 模拟一个JSON数据作为测试数据
    json_data = {
        "programs": [
            {
                "program_name": "阴阳师",
                "program_tasks": [
                    {
                        "task_name": "打开游戏",
                        "task_entry": "打开阴阳师",
                        "option": ["选择区服"]
                    },
                    {
                        "task_name": "自动地鬼",
                        "task_entry": "自动地鬼",
                        "option": []
                    }
                ],
                "option": {
                    "选择区服": {
                        "select": [
                            {
                                "name": "官服",
                                "pipeline_override": {
                                    "打开阴阳师": {
                                        "package": "com.netease.onmyoji/.tag0"
                                    }
                                }
                            },
                            {
                                "name": "测试服",
                                "pipeline_override": {
                                    "打开阴阳师": {
                                        "package": "com.netease.onmyoji/.tag0"
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            {
                "program_name": "明日方舟",
                "program_tasks": [
                    {
                        "task_name": "任务1",
                        "task_entry": "任务入口1",
                        "option": []
                    }
                ],
                "option": {}
            }
        ]
    }

    # 模拟将该数据写入到一个JSON文件并从中读取
    json_file = '../assets/config/programs.json'
    # json_file = 'test_config.json'

    #
    # with open("../assets/config/programs.json", 'w', encoding='utf-8') as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=4)

    # 测试从文件中加载JSON并解析为对象
    programs_json = ProgramsJson.load_from_file(json_file)

    # 1. 获取所有的program
    programs = programs_json.programs
    print("所有的Program:")
    for program in programs:
        print(f"- Program Name: {program.program_name}")

    assert len(programs) == 2, "Program数量不正确"

    # 2. 获取每个program的task
    for program in programs:
        print(f"\nProgram: {program.program_name}")
        tasks = program.program_tasks
        for task in tasks:
            print(f"  Task Name: {task.task_name}, Task Entry: {task.task_entry}")

    for program in programs:
        print(f"\nProgram: {program.program_name}")

        # 检查是否有option
        if program.option is None:
            print(f"  {program.program_name} 没有 options")
            continue

        for task in program.program_tasks:
            print(f"  Task: {task.task_name}")
            options = program.option.options  # Program级别的option

            # 只打印在task中存在的option
            for option_name, option_value in options.items():
                if option_name in task.option:  # Check if option exists in the task's options
                    print(f"    Option Name: {option_name}")

                    # 打印 SelectOption
                    for select_option in option_value.select:
                        print(f"      Select Name: {select_option.name}")
                        if select_option.pipeline_override:
                            print(f"        Pipeline Override: {select_option.pipeline_override}")

                    # 打印 InputOption
                    for input_option in option_value.input:
                        print(f"      Input Name: {input_option.name}, Default: {input_option.default}")
                        if input_option.pipeline_override:
                            print(f"        Pipeline Override: {input_option.pipeline_override}")

    print("\n所有测试通过！")

    # # 验证pipeline_override是否正确
                # if option_name == "选择区服":
                #     assert len(option_value.select) == 2, "选择区服的选项数量不正确"
                #     assert option_value.select[0].name == "官服", "选择区服第一个选项错误"
                #     assert option_value.select[0].pipeline_override == {
                #         "打开阴阳师": {"package": "com.netease.onmyoji/.tag0"}
                #     }, "官服的pipeline_override不正确"

    print("\n所有测试通过！")


if __name__ == "__main__":
    test_programs_json()
