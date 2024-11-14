import difflib
import logging
import os
import json

from typing import Tuple, List

import psutil


def load_config():
    """加载 app_config.json 配置文件"""
    config_path = os.path.join(os.getcwd(), "assets", "config", "app_config.json")
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config  # 如果配置文件中没有DEBUG字段，则默认True

def _terminate_adb_processes():
    """查找并终止所有名为 adb.exe 的进程"""
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'adb.exe':
            try:
                logging.info(f"Terminating adb.exe process [PID: {process.info['pid']}]...")
                process.terminate()
                process.wait(timeout=5)
            except psutil.NoSuchProcess:
                logging.warning(f"Process [PID: {process.info['pid']}] already terminated.")
            except psutil.TimeoutExpired:
                logging.warning(f"Process [PID: {process.info['pid']}] did not terminate, killing it...")
                process.kill()
            except Exception as e:
                logging.error(f"Failed to terminate process [PID: {process.info['pid']}]: {e}")

def is_inside(big_rect: Tuple[int, int, int, int], small_rect: Tuple[int, int, int, int]) -> bool:
    """
    判断 small_rect 是否完全位于 big_rect 内。
    big_rect 和 small_rect 都是 (x, y, w, h) 格式。
    """
    big_x, big_y, big_w, big_h = big_rect
    small_x, small_y, small_w, small_h = small_rect

    # 计算 big_rect 的右下角坐标
    big_x2 = big_x + big_w
    big_y2 = big_y + big_h

    # 计算 small_rect 的右下角坐标
    small_x2 = small_x + small_w
    small_y2 = small_y + small_h

    # 判断 small_rect 是否完全位于 big_rect 内
    return (small_x >= big_x and 
            small_y >= big_y and 
            small_x2 <= big_x2 and 
            small_y2 <= big_y2)


def check_if_rect_is_inside_any(rectangles: List[Tuple[int, int, int, int]], rect_to_check: Tuple[int, int, int, int]) -> Tuple[bool, Tuple[int, int, int, int]]:
    """
    检查 rect_to_check 是否在 rectangles 列表中的任意一个矩形内。
    返回 (bool, 包含的矩形) 或 (False, None)。
    """
    for big_rect in rectangles:
        if is_inside(big_rect, rect_to_check):
            return True, big_rect
    return False, None

def find_best_answer(question, qa_dict):
    """
    根据输入的问题，找到最相近的问题并返回其答案列表。
    """
    # 使用 difflib 来寻找最佳匹配
    best_match = difflib.get_close_matches(question, qa_dict.keys(), n=1, cutoff=0.5)

    # 返回匹配结果或提示信息
    return qa_dict[best_match[0]] if best_match else "未找到匹配的答案"


def load_tasks_from_pipeline(directory):
    tasks = {}
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                data = json.load(file)
                tasks.update(data)
    return tasks