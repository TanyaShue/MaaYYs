import os
import json
from datetime import date

from custom_dir import device_name


class DailyTaskTracker:
    """
    一个用于跟踪任务是否在当天执行过的辅助类。
    通过将执行日期记录在JSON文件中来确保任务每日只运行一次。
    每个设备将拥有独立的记录文件。
    """

    def __init__(self, record_filename_suffix: str = '_daily_tasks_record.json'):
        """
        初始化跟踪器。

        :param record_filename_suffix: 用于构成文件名后缀的部分。
        """
        project_root = os.getcwd()
        assets_path = os.path.join(project_root, 'assets')

        if not os.path.exists(assets_path):
            os.makedirs(assets_path)

        # 2. 使用导入的全局 device_name 来构建一个设备专属的文件名
        #    例如：'my_device_1_daily_tasks_record.json'
        record_filename = f"{device_name}{record_filename_suffix}"
        self.record_file = os.path.join(assets_path, record_filename)
        # 添加打印输出来方便调试
        print(f"DailyTaskTracker is using record file: '{self.record_file}'")

    def _read_records(self) -> dict:
        """
        从文件中读取执行记录。
        如果文件不存在或为空，则返回一个空字典。
        """
        if not os.path.exists(self.record_file):
            return {}

        with open(self.record_file, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def _write_records(self, records: dict) -> None:
        """
        将执行记录写入文件。

        :param records: 包含所有任务记录的字典。
        """
        with open(self.record_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=4)

    def has_executed_today(self, task_name: str) -> bool:
        """
        检查指定名称的任务今天是否已经执行过。

        :param task_name: 要检查的任务的唯一名称。
        :return: 如果今天已经执行过，返回 True，否则返回 False。
        """
        today = str(date.today())
        records = self._read_records()
        last_execution_date = records.get(task_name)

        if last_execution_date == today:
            print(f"任务 '{task_name}' 今天已经在设备 '{device_name}' 上执行过，将跳过。")
            return True
        return False

    def record_execution(self, task_name: str) -> None:
        """
        记录指定名称的任务已在今天执行。

        :param task_name: 要记录的任务的唯一名称。
        """
        today = str(date.today())
        records = self._read_records()
        records[task_name] = today
        self._write_records(records)
        print(f"已为任务 '{task_name}' 在设备 '{device_name}' 上记录今天的执行日期：{today}")