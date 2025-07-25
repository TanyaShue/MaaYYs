# -*- coding: UTF-8 -*-
import json
import random
import time

from maa.context import Context
from maa.custom_action import CustomAction


from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("SwitchSoul")
class SwitchSoul(CustomAction):
    def __init__(self):
        super().__init__()
        self._logger = None
        self._running = True

    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        执行御魂切换操作

        :param context: 运行上下文
        :param argv: 运行参数，需包含 {"group_name": "分组名称", "team_name": "队伍名称"}
        :return: 是否执行成功
        """

        # 解析参数
        try:
            json_data = json.loads(argv.custom_action_param)
            group_name = json_data.get('group_name')
            team_name = json_data.get('team_name')

            if not group_name or not team_name:
                print("参数错误：分组名称和队伍名称不能为空")
                return False

            print(f"开始执行自定义动作：装备切换御魂 - 分组：{group_name}，队伍：{team_name}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"参数解析错误: {str(e)}")
            return False
        result = context.run_task("识别是否位于预设界面", {
            "识别是否位于预设界面":{
                "timeout": 1000,
                "recognition": "OCR",
                "expected": "管理分组",
                "roi": [1128,637,116,52],
            }
        })
        print(result)
        # 检查点击结果
        if not result.nodes:
            print("不处于预设选中状态")

            # 步骤1：点击预设按钮
            if not self._click_preset(context):
                print("点击预设按钮失败")
                return False

        # 步骤2：查找并点击指定分组
        if not self._find_and_click_group(context, group_name):
            print(f"找不到指定分组: {group_name}")
            return False

        # 步骤3：查找并装备指定队伍的御魂
        if not self._find_and_equip_team(context, team_name):
            print(f"找不到指定队伍或装备失败: {team_name}")
            return False

        print("御魂切换完成")
        return True

    def _click_preset(self, context: Context) -> bool:
        """点击预设按钮"""
        print("尝试点击预设按钮")
        result = context.run_task("识别预设", {
            "识别预设": {
                "timeout": 2000,
                "recognition": "OCR",
                "expected": "预设",
                "roi": [334,69,93,50],
                "action": "Click",
                "next":"识别是否位于预设界面"
            },
            "识别是否位于预设界面":{
                "timeout": 2000,
                "recognition": "OCR",
                "expected": "管理分组",
                "roi": [1128,637,116,52],
            }
        })

        # 检查点击结果
        if not result.nodes:
            print("预设按钮点击失败")
            return False

        time.sleep(0.5)  # 等待界面响应
        return True

    def _find_and_click_group(self, context: Context, group_name: str) -> bool:
        """
        查找并点击指定分组

        :param context: 运行上下文
        :param group_name: 分组名称
        :return: 是否成功点击
        """
        print(f"开始查找分组: {group_name}")

        # 先返回最上方以确保从头开始查找
        context.run_task("返回最上页分组", {
            "返回最上页分组": {
                "action": "Custom",
                "custom_action": "RandomSwipe",
                "custom_action_param": {
                    "end_roi": [1085, 442, 152, 60],
                    "start_roi": [1085, 161, 162, 58],
                    "delay": 1000
                }
            }
        })
        time.sleep(2)

        # 开始查找分组
        max_attempts = 10  # 最大尝试次数
        for attempt in range(1, max_attempts + 1):
            if not self._running:
                return False

            print(f"查找分组 - 第{attempt}次尝试")

            # 截图并识别
            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("点击分组", img, {
                "点击分组": {
                    "timeout": 2000,
                    "recognition": "OCR",
                    "action": "Click",
                    "expected": group_name,
                    "roi": [1085, 86, 162, 542]
                }
            })

            # 找到分组
            if detail is not None:
                # 精确点击位置
                click_x = random.randint(detail.box.x, detail.box.x + detail.box.w)
                click_y = random.randint(detail.box.y, detail.box.y + detail.box.h)
                context.tasker.controller.post_click(click_x, click_y).wait()
                print(f"成功找到并点击分组: {group_name}")
                return True

            # 未找到分组，尝试滑动到下一页
            if attempt % 3 == 0:  # 每3次尝试，返回顶部重新开始
                print("返回顶部重新查找")
                context.run_task("返回最上页分组", {
                    "返回最上页分组": {
                        "action": "Custom",
                        "custom_action": "RandomSwipe",
                        "custom_action_param": {
                            "end_roi": [1085, 442, 152, 60],
                            "start_roi": [1085, 161, 162, 58],
                            "delay": 1000
                        }
                    }
                })
            else:
                # 向下滑动
                print("向下滑动继续查找")
                context.run_task("下一页", {
                    "下一页": {
                        "action": "Custom",
                        "post_delay": 1000,  # 减少延迟时间
                        "custom_action": "RandomSwipe",
                        "custom_action_param": {
                            "start_roi": [1085, 442, 152, 60],
                            "end_roi": [1085, 161, 162, 58],
                            "delay": 1000
                        }
                    }
                })

            time.sleep(2)  # 降低等待时间，提高效率

        print(f"经过{max_attempts}次尝试，未找到分组: {group_name}")
        return False

    def _find_and_equip_team(self, context: Context, team_name: str) -> bool:
        """
        查找并装备指定队伍的御魂

        :param context: 运行上下文
        :param team_name: 队伍名称
        :return: 是否成功装备
        """
        print(f"开始查找队伍: {team_name}")

        max_attempts = 8  # 最大尝试次数
        for attempt in range(1, max_attempts + 1):
            if not self._running:
                return False

            print(f"查找队伍 - 第{attempt}次尝试")

            time.sleep(0.5)  # 等待界面稳定
            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("点击队伍", img, {
                "点击队伍": {
                    "timeout": 2000,
                    "recognition": "OCR",
                    "expected": team_name,
                    "roi": [573,128,255,436]
                }
            })
            time.sleep(0.5)  # 等待界面稳定
            # 找到队伍
            if detail is not None:
                roi = [detail.box.x - 30, detail.box.y - 30, 500, 80]
                print(f"找到队伍: {team_name}，尝试装备御魂")
                # 点击"装备御魂"按钮，然后点击确定
                equip_result = context.run_task("通用_装备御魂", {
                    "通用_装备御魂": {
                        "roi": roi
                    }
                })

                if equip_result:
                    print(f"成功装备队伍 {team_name} 的御魂")
                    return True
                else:
                    print(f"找到队伍 {team_name} 但装备御魂失败")
                    return False

            # 未找到队伍，尝试滑动
            if attempt % 3 == 0:  # 每3次尝试，返回顶部重新开始
                print("返回顶部重新查找队伍")
                context.run_task("返回最上页分队", {
                    "返回最上页分队": {
                        "action": "Custom",
                        "custom_action": "RandomSwipe",
                        "custom_action_param": {
                            "end_roi": [585, 495, 273, 112],
                            "start_roi": [588, 171, 410, 76],
                            "delay": 500
                        }
                    }
                })
            else:
                # 向下滑动
                print("向下滑动继续查找队伍")
                context.run_task("下一页", {
                    "下一页": {
                        "action": "Custom",
                        "custom_action": "RandomSwipe",
                        "custom_action_param": {
                            "start_roi": [585, 495, 273, 112],
                            "end_roi": [588, 171, 410, 76],
                            "delay": 400
                        }
                    }
                })

            time.sleep(1)  # 降低等待时间，提高效率

        print(f"经过{max_attempts}次尝试，未找到队伍: {team_name}")
        return False

    def stop(self) -> None:
        """停止执行"""
        print("停止执行自定义动作")
        self._running = False