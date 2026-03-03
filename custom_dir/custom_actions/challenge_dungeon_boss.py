# -*- coding: UTF-8 -*-
import json
from datetime import datetime, time

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer

from custom_dir.until.daily_task_tracker import DailyTaskTracker

from custom_dir import print_to_ui


@AgentServer.custom_action("ChallengeDungeonBoss")
class ChallengeDungeonBoss(CustomAction):

    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        :param argv:
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        json_data = json.loads(argv.custom_action_param)
        print(json_data)
        print("开始执行自定义动作: 自动挑战地鬼")

        # 从参数中获取挑战次数，默认为1
        count = json_data.get("count", 1)
        print(f"挑战地鬼数: {count}")

        for i in range(count):
            print(f"开始挑战第 {i + 1} 只地鬼")
            r=context.run_task("地鬼-点击筛选",{
                "地鬼-识别挑战位置": {"index": i}})
            if r is None:
                return False

            r=context.run_task("自动地鬼3")
            if r is None:
                return False


        print("自动地鬼挑战完成")

        return True

    def stop(self) -> None:
        pass
