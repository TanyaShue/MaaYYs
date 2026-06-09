# This Python file uses the following encoding: utf-8
import os
import sys

cur_path = os.path.abspath(__file__)
oas_path = cur_path.split("tasks")[0]
if oas_path not in sys.path:
    sys.path.append(oas_path)

from module.exception import TaskEnd
from module.logger import logger
from tasks.Yuhun.script_result import ResultScriptTask
from tasks.Yuhun.script_select import SelectScriptTask


class ScriptTask(SelectScriptTask, ResultScriptTask):
    """御魂强化主流程：选择 -> 强化 -> 结果循环。"""

    def run(self):
        round_index = 1
        while True:
            if round_index > 1:
                self.log_blank()
            logger.hr(f"Yuhun flow round {round_index}")
            self.run_once()
            round_index += 1

    def run_once(self):
        souls = self.run_select_page()
        self.log_blank()
        self.run_enhance_page()
        self.mark_lowest_result_index_enhanced(souls, list(range(1, len(souls) + 1)))
        self.log_blank()
        self.run_result_page(souls)


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    config = Config("tmp_ios")
    device = Device(config)
    try:
        ScriptTask(config, device).run()
    except TaskEnd as e:
        logger.info(str(e))
