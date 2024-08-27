import pandas as pd
import difflib

from typing import Tuple, List

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



def load_qa_from_excel_v2(file_path):
    """
    优化版本：从Excel文件中加载问题和答案，将其存储在字典中，处理多个答案的情况。
    """
    # 读取Excel文件，假设数据在第一列且没有列名，并过滤掉空行
    df = pd.read_excel(file_path, header=None, usecols=[0]).dropna()

    # 使用 rsplit 以最后一个 '-' 为分割点，生成题目和答案列
    df[['题目', '答案']] = df[0].str.rsplit('-', n=1, expand=True)

    # 过滤掉题目或答案为空的行
    df = df.dropna(subset=['题目', '答案'])

    # 创建字典，并处理多答案情况
    qa_dict = {}
    for q, a in zip(df['题目'], df['答案']):
        if pd.notna(q) and pd.notna(a):
            # 将答案按 '/' 分割，形成一个答案列表
            answers = [ans.strip() for ans in a.split('/') if ans.strip()]
            qa_dict[q] = answers

    return qa_dict

def find_best_answer(question, qa_dict):
    """
    根据输入的问题，找到最相近的问题并返回其答案列表。
    """
    # 使用 difflib 来寻找最佳匹配
    best_match = difflib.get_close_matches(question, qa_dict.keys(), n=1, cutoff=0.5)

    # 返回匹配结果或提示信息
    return qa_dict[best_match[0]] if best_match else "未找到匹配的答案"
