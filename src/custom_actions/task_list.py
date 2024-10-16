import json

from maa.context import Context
from maa.custom_action import CustomAction


class TaskList(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数{"task_list": ["A", "B", "C"]}
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        json_data = json.loads(argv.custom_action_param)

        task_list = json_data.get("task_list", [])

        if not task_list:
            print("无效的task_list")
            return False

        print(f"开始执行任务列表 {task_list}")

        for task in task_list:
            print(f"执行任务: {task}")
            context.run_pipeline(task)

        return True

    def stop(self):
        pass