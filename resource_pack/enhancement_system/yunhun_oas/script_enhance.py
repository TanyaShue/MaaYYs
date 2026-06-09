# This Python file uses the following encoding: utf-8
import os
import sys
from random import uniform
from time import sleep

cur_path = os.path.abspath(__file__)
oas_path = cur_path.split("tasks")[0]
if oas_path not in sys.path:
    sys.path.append(oas_path)

from module.logger import logger
from module.exception import TaskEnd
from tasks.Yuhun.script_common import YuhunBase


class EnhanceScriptTask(YuhunBase):
    """御魂强化设置页调试脚本：计算并强化。"""

    def run(self):
        self.run_enhance_page()
        raise TaskEnd("Yuhun enhance page done")

    def run_enhance_page(self) -> None:
        logger.hr("Yuhun enhance page")
        self.click_calc_button(self.I_ENHANCE_CALC, "强化设置页计算")
        self.log_blank()
        self.click_confirm_enhance_button(self.I_ENHANCE_CONFIRM, "强化设置页强化")
        self.wait_enhance_animation()

    def run_result_continue_enhance(self) -> None:
        self.log_blank()
        logger.hr("Yuhun result continue enhance")
        logger.info("点击继续强化入口")
        if not self.wait_until_appear(self.I_RESULT_ENHANCE, wait_time=8):
            raise RuntimeError("未检测到结果页继续强化入口")
        self.click(self.I_RESULT_ENHANCE, interval=1)
        self.click_calc_button(self.I_RESULT_CALC, "结果页计算")
        self.log_blank()
        self.click_result_confirm_enhance_button()
        self.wait_enhance_animation()

    def click_calc_button(self, button, label: str) -> None:
        logger.info("等待%s按钮", label)
        if not self.wait_until_appear(button, wait_time=8):
            raise RuntimeError(f"未检测到{label}按钮")
        logger.info("点击%s直到按钮消失", label)
        self.ui_click_until_disappear(button, interval=1)
        sleep(0.5)

    def click_result_confirm_enhance_button(self) -> None:
        logger.info("等待结果页强化按钮")
        if not self.wait_until_appear(self.I_RESULT_CONFIRM_ENHANCE, wait_time=8):
            raise RuntimeError("未检测到结果页强化按钮")
        logger.info("点击结果页强化")
        self.click(self.I_RESULT_CONFIRM_ENHANCE, interval=1)

    @staticmethod
    def wait_enhance_animation() -> None:
        wait_seconds = uniform(4, 5)
        logger.info("等待强化动画 %.1fs", wait_seconds)
        sleep(wait_seconds)

    def click_confirm_enhance_button(self, button, label: str) -> None:
        logger.info("等待%s按钮", label)
        if not self.wait_until_appear(button, wait_time=8):
            raise RuntimeError(f"未检测到{label}按钮")
        logger.info("点击%s", label)
        self.click(button, interval=1)
        sleep(0.5)


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    config = Config("tmp_ios")
    device = Device(config)
    EnhanceScriptTask(config, device).run()
