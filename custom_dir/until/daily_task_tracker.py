# daily_task_tracker.py
# -*- coding: UTF-8 -*-
import os
import json
from datetime import date
import threading

# 导入 custom_dir 包以动态获取 device_name
import custom_dir


class DailyTaskTracker:
    """
    一个用于跟踪任务是否在当天执行过的辅助类。
    通过将所有设备的执行日期记录在【单个JSON文件】中来确保任务每日只运行一次。
    """
    _lock = threading.Lock()  # 添加一个线程锁来防止多线程并发读写文件冲突

    def __init__(self, record_filename: str = 'daily_tasks_record.json'):
        """
        初始化跟踪器。

        :param record_filename: 用于存储所有设备执行记录的JSON文件名。
        """
        project_root = os.getcwd()
        assets_path = os.path.join(project_root, 'assets')

        if not os.path.exists(assets_path):
            os.makedirs(assets_path)

        # 现在文件名是固定的，不再包含设备名
        self.record_file = os.path.join(assets_path, record_filename)
        print(f"DailyTaskTracker is using a single record file: '{self.record_file}'")

    def _read_records(self) -> dict:
        """
        从单个文件中读取所有设备的执行记录。
        """
        with self._lock:
            if not os.path.exists(self.record_file):
                return {}

            with open(self.record_file, 'r', encoding='utf-8') as f:
                try:
                    # 添加一个检查，如果文件为空，则返回空字典
                    if os.fstat(f.fileno()).st_size == 0:
                        return {}
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}

    def _write_records(self, all_records: dict) -> None:
        """
        将所有设备的执行记录写回单个文件。

        :param all_records: 包含所有设备及其任务记录的完整字典。
        """
        with self._lock:
            with open(self.record_file, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, ensure_ascii=False, indent=4)

    def has_executed_today(self, task_name: str) -> bool:
        """
        检查指定任务对于【当前设备】今天是否已经执行过。
        """
        today = str(date.today())
        current_device = custom_dir.device_name

        all_records = self._read_records()

        # .get(current_device, {}) 会安全地获取当前设备的记录，如果设备是第一次运行，则返回一个空字典
        device_records = all_records.get(current_device, {})
        last_execution_date = device_records.get(task_name)

        if last_execution_date == today:
            print(f"任务 '{task_name}' 今天已经在设备 '{current_device}' 上执行过，将跳过。")
            return True
        return False

    def record_execution(self, task_name: str) -> None:
        """
        记录指定任务已在【当前设备】的命名空间下执行。
        """
        today = str(date.today())
        current_device = custom_dir.device_name

        all_records = self._read_records()

        # 如果这是该设备的第一次记录，先为它创建一个空字典
        if current_device not in all_records:
            all_records[current_device] = {}

        # 在当前设备的记录中更新任务的执行日期
        all_records[current_device][task_name] = today

        # 将更新后的完整数据写回文件
        self._write_records(all_records)
        print(f"已为任务 '{task_name}' 在设备 '{current_device}' 上记录今天的执行日期：{today}")