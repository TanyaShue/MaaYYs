# -*- coding: UTF-8 -*-
import time
import json
import os
from datetime import date

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer

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
        # group_name: 分组名称, team_name: 队伍名称, count: 挑战次数,daily_once: 是否每天只执行一次
        json_data = json.loads(argv.custom_action_param)

        # 新增逻辑：检查是否需要每日只执行一次
        daily_once = json_data.get("daily_once", False)
        if daily_once:
            # 获取当前日期
            today = str(date.today())
            # 定义记录文件路径
            project_root = os.getcwd()
            assets_path = os.path.join(project_root, 'assets')

            # 确保 assets 目录存在
            if not os.path.exists(assets_path):
                os.makedirs(assets_path)
            record_file = os.path.join(assets_path, 'date.json')

            # 读取记录文件
            record_data = {}
            if os.path.exists(record_file):
                with open(record_file, 'r') as f:
                    try:
                        record_data = json.load(f)
                    except json.JSONDecodeError:
                        pass # 文件为空或格式错误则忽略

            # 检查今天是否已经执行过
            if record_data.get("last_execution_date") == today:
                print("今天已经执行过自动挑战地鬼，脚本将不再执行。")
                return True # 返回True，表示任务“成功”跳过

        print("开始执行自定义动作: 自动挑战地鬼")

        # 从参数中获取挑战次数，默认为1
        count = json_data.get("count", 1)
        print(f"挑战地鬼数: {count}")

        for i in range(count):
            print(f"开始挑战第 {i + 1} 只地鬼")

            # 筛选模板容易出现分数不够的情况
            context.run_task("点击筛选", {
                "点击筛选": {"next":["点击筛选_1","自动地鬼1"]},"点击筛选_1":{"post_delay": 2000, "timeout": 500, "recognition": "TemplateMatch",
                             "template": "地域鬼王/地域鬼王_筛选.png", "action": "Click", "target": [1102, 17, 58, 73],
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

            # 点击挑战
            context.run_task("挑战地鬼", {
                "挑战地鬼": {"post_delay": 2000, "action": "Click", "target": [1109, 493, 102, 63]}})
            time.sleep(5)
            context.run_task("自动挑战", {
                "自动挑战": {"timeout": 100, "action": "Custom", "custom_action": "AutoBattle",
                             "custom_action_param": {"group_name": json_data["group_name"],
                                                     "team_name": json_data["team_name"]}}})

            time.sleep(20)
            print("等待识别分享按钮")

            context.run_task("结束战斗",
                             {"结束战斗": {"next": ["点击叉叉"], "interrupt": "点击屏幕继续", "timeout": 300000, },
                              "点击屏幕继续": {
                                  "roi": [481, 641, 380, 78], "recognition": "OCR", "expected": "点击屏幕继续",
                                  "action": "Click", "target": [275, 488, 652, 112]},
                              "点击叉叉": {"recognition": "TemplateMatch", "template": "通用图标/地鬼_关闭.png",
                                           "action": "Click"}})

        print("自动地鬼挑战完成")

        # 如果需要每日只执行一次，并且执行成功，则更新记录文件
        if daily_once:
            with open(record_file, 'w') as f:
                json.dump({"last_execution_date": today}, f)
            print(f"已记录今天的执行日期：{today}")
        return True

    def stop(self) -> None:
        pass