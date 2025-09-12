import json
import time
from maa.context import Context
from maa.custom_action import CustomAction

from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("RepeatChallengeNTimes")
class RepeatChallengeNTimes(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:
        """
        数字识别验证动作
        :param argv: 运行参数, 包括 start_repeat, expected_number
        :param context: 运行上下文
        :return: 是否执行成功
        """

        # 读取 custom_param 的参数
        # {"start_repeat": true, "expected_number": x}
        json_data = json.loads(argv.custom_action_param)

        # 获取参数
        start_repeat = json_data.get("start_repeat", True)
        expected_number = str(json_data.get("expected_number", 1))


        if not expected_number :
            print("无效的参数：expected_number")
            return False

        print(f"开始点击自动允许次数设置：期望数字 {expected_number}")
        if start_repeat:
            context.run_task("通用_启动设置挑战次数")
            print("启动自动挑战")
        else:
            context.run_task("通用_取消设置挑战次数")
            print("关闭自动挑战")
            return True



        # 识别当前区域的数字
        current_number = self._recognize_number(context)
        print(f"当前设置次数为{current_number}")

        if current_number == expected_number:
            print("当前数字与期望数字相同,完成次数设置")
        else:
            self.input_expected_number(context,expected_number)


        return True

    def _recognize_number(self, context: Context) -> str:
        """
        识别指定区域的数字
        :param context: 运行上下文
        :param
        :return: 识别到的数字
        """

        # 运行识别任务
        img = context.tasker.controller.post_screencap().wait().get()
        result = context.run_recognition("通用_识别挑战次数",img)
        if result and result.best_result:
            try:
                value = str(result.best_result.text)
                return value
            except (ValueError, TypeError):
                return "10"
        else:
            return "10"

    def input_expected_number(self,context: Context,expected_number):
        print("开始点击数字")
        context.run_task("设置挑战次数_点击数字编辑")
        number_list=list(expected_number)
        print(number_list)
        for n in number_list:
            print(f"开始点击数字: {n}")
            context.run_task("设置挑战次数_点击目标数字",{"设置挑战次数_点击目标数字":{"expected":n}})
        print("点击数字完成")
        nu=self._recognize_number(context)
        if nu == expected_number:
            context.run_task("设置挑战次数_点击确定")

    def stop(self) -> None:
        """停止执行的逻辑"""
        print("停止数字验证动作")
        pass
