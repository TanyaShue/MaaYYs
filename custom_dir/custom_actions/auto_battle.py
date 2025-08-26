# -*- coding: UTF-8 -*-
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
import json
import random
import time


@AgentServer.custom_action("AutoBattle")
class AutoBattle(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        :param argv:
        :param context: 运行上下文
        :return: 是否执行成功。
        """

        print("2秒后开始战斗")
        time.sleep(2)
        # 加载自定义参数
        json_data = json.loads(argv.custom_action_param)

        # 点击预设
        if not json_data == {} and json_data["group_name"]:
            context.run_task("点击预设", {"点击预设": {"timeout": 100, "action": "Click", "target": [49, 658, 26, 51]}})

            # 添加重试机制，最多尝试3次
            max_retries = 3
            for retry in range(1, max_retries + 1):
                print(f"第{retry}次尝试查找分组和队伍")

                # 查找并点击分组
                if not self._select_group(context, json_data["group_name"]):
                    print(f"第{retry}次尝试：未找到分组 {json_data['group_name']}")
                    if retry == max_retries:
                        print("达到最大重试次数，查找分组失败")
                        return False
                    continue

                time.sleep(1)

                # 查找并点击队伍
                if self._select_team(context, json_data["team_name"]):
                    print(f"成功找到并选择队伍 {json_data['team_name']}")
                    break
                else:
                    print(f"第{retry}次尝试：未找到队伍 {json_data['team_name']}")
                    if retry == max_retries:
                        print("达到最大重试次数，查找队伍失败")
                        return False
                    print(f"重新从分组开始查找...")
                    time.sleep(1)

            # 出战队伍
            context.run_task("出战队伍", {
                "出战队伍": {
                    "action": "Click",
                    "recognition": "OCR",
                    "expected": "出战",
                    "roi": [352, 637, 146, 53],
                    "post_delay": 1000,
                    "timeout": 1000
                }
            })

        # 点击准备 开始战斗，这里点击两次，防止队伍上场失败导致准备无效
        for i in range(2):
            x, y = random.randint(1125, 1236), random.randint(539, 634)
            print(f"随机点击准备按钮: {x},{y}")
            time.sleep(1)
            context.tasker.controller.post_click(x, y).wait()

        return True

    def _select_group(self, context: Context, group_name: str) -> bool:
        """
        选择分组
        :param context: 运行上下文
        :param group_name: 分组名称
        :return: 是否成功选择分组
        """
        # 分组回到最上页
        for _ in range(2):
            context.run_task("返回最上页分组", {
                "返回最上页分组": {
                    "action": "Custom",
                    "custom_action": "RandomSwipe",
                    "custom_action_param": {
                        "end_roi": [39, 582, 113, 36],
                        "start_roi": [39, 270, 120, 38],
                        "delay": 200
                    }
                }
            })

        time.sleep(3)

        # 点击分组
        for count in range(1, 21):
            time.sleep(2)
            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("点击分组", img, {
                "点击分组": {
                    "timeout": 500,
                    "post_delay": 1000,
                    "recognition": "OCR",
                    "expected": group_name,
                    "roi": [34, 241, 132, 440]
                }
            })
            time.sleep(1)

            if detail is not None:
                context.tasker.controller.post_click(
                    random.randint(detail.box.x, detail.box.x + detail.box.h),
                    random.randint(detail.box.y, detail.box.y + detail.box.w)
                ).wait()
                print(f"切换到分组 {group_name}")
                return True

            if count >= 5:
                context.run_task("返回最上页分组", {
                    "返回最上页分组": {
                        "action": "Custom",
                        "post_delay": 1000,
                        "custom_action": "RandomSwipe",
                        "custom_action_param": {
                            "end_roi": [39, 582, 113, 36],
                            "start_roi": [39, 270, 120, 38],
                            "delay": 1000
                        }
                    }
                })
            else:
                context.run_task("下一页", {
                    "下一页": {
                        "action": "Custom",
                        "per_delay": 1000,
                        "post_delay": 1000,
                        "custom_action": "RandomSwipe",
                        "custom_action_param": {
                            "start_roi": [39, 582, 113, 36],
                            "end_roi": [39, 270, 120, 38],
                            "delay": 1000
                        }
                    }
                })
                time.sleep(2)
        return False

    def _select_team(self, context: Context, team_name: str) -> bool:
        """
        选择队伍
        :param context: 运行上下文
        :param team_name: 队伍名称
        :return: 是否成功选择队伍
        """
        print("开始执行自定义动作：点击队伍")

        # 点击队伍
        for count in range(1, 10):
            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("点击队伍", img, {
                "点击队伍": {
                    "timeout": 500,
                    "recognition": "OCR",
                    "expected": team_name,
                    "roi": [254, 235, 263, 355]
                }
            })
            time.sleep(1)

            if detail is not None:
                time.sleep(1)
                print(f"切换到队伍 {team_name}")
                context.tasker.controller.post_click(
                    random.randint(detail.box.x, detail.box.x + detail.box.h),
                    random.randint(detail.box.y, detail.box.y + detail.box.w)
                ).wait()
                time.sleep(1)
                context.tasker.controller.post_click(
                    random.randint(359, 490),
                    random.randint(647, 682)
                ).wait()
                return True

            if count >= 5:
                context.run_task("返回最上页分队", {
                    "返回最上页分队": {
                        "action": "Custom",
                        "custom_action": "RandomSwipe",
                        "custom_action_param": {
                            "end_roi": [328, 484, 253, 103],
                            "start_roi": [334, 235, 300, 90],
                            "delay": 1000
                        }
                    }
                })
            else:
                context.run_task("下一页", {
                    "下一页": {
                        "action": "Custom",
                        "custom_action": "RandomSwipe",
                        "custom_action_param": {
                            "start_roi": [328, 484, 253, 103],
                            "end_roi": [334, 235, 300, 90],
                            "delay": 1000
                        }
                    }
                })

        print("队伍不存在")
        return False

    def stop(self) -> None:
        pass
