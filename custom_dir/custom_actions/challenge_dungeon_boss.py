# --- START OF FILE challenge_dungeon_boss.py ---

# -*- coding: UTF-8 -*-
import time
import json

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer

from custom_dir.until.daily_task_tracker import DailyTaskTracker


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

        # 读取 custom_param 的参数{"group_name":"xxx", "team_name":"xxx", "count":3, "daily_once": true}
        json_data = json.loads(argv.custom_action_param)

        # 新增逻辑：检查是否需要每日只执行一次
        daily_once = json_data.get("daily_once", False)
        lock_squad = json_data.get("lock_squad", True)
        task_name = "ChallengeDungeonBoss"  # 定义当前任务的唯一名称

        if daily_once:
            tracker = DailyTaskTracker()
            # 调用封装好的方法来检查今天是否已执行
            if tracker.has_executed_today(task_name):
                return True  # 返回True，表示任务“成功”跳过

        print("开始执行自定义动作: 自动挑战地鬼")

        # 从参数中获取挑战次数，默认为1
        count = json_data.get("count", 1)
        print(f"挑战地鬼数: {count}")

        for i in range(count):
            print(f"开始挑战第 {i + 1} 只地鬼")

            # 筛选模板容易出现分数不够的情况
            context.run_task("点击筛选", {
                "点击筛选": {"next": ["点击筛选_1", "自动地鬼1"]},
                "点击筛选_1": {"post_delay": 2000, "timeout": 500, "recognition": "TemplateMatch",
                               "template": "地域鬼王/地域鬼王_筛选.png", "action": "Click",
                               "target": [1102, 17, 58, 73],
                               "roi": [1077, 2, 99, 121]}})
            context.run_task("点击热门", {
                "点击热门": {"post_delay": 2000, "timeout": 500, "target": [1185, 220, 50, 120], "action": "Click"}})
            context.run_task("识别挑战位置", {
                "识别挑战位置": {"post_delay": 2000, "timeout": 500, "index": i, "order_by": "Vertical",
                                 "recognition": "TemplateMatch", "template": "地域鬼王/地鬼_挑战.png",
                                 "action": "Click", "roi": [1035, 192, 135, 504]}})

            # 选择挑战等级
            # TODO
            print("点击挑战")

            # 开始挑战
            if lock_squad:
                context.run_task("自动地鬼3",{"自动地鬼12_装备预设": {"enabled": False}})

            else:
                context.run_task("自动地鬼3", {"自动地鬼12": {
                    "custom_action_param": {"group_name": json_data["group_name"],
                                            "team_name": json_data["team_name"]}},
                                                        "自动地鬼12_装备预设": {"enabled": True}})

        print("自动地鬼挑战完成")

        # 如果需要每日只执行一次，并且执行成功，则更新记录文件
        if daily_once:
            # 调用封装好的方法来记录执行
            tracker.record_execution(task_name)

        return True

    def stop(self) -> None:
        pass
