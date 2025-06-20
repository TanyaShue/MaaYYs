# -*- coding: UTF-8 -*-
import json
import os
import difflib
import time

import pandas as pd
from datetime import datetime

from maa.context import Context
from maa.custom_action import CustomAction


class QuestionMatcher(CustomAction):
    def __init__(self):
        super().__init__()
        self.csv_path = os.path.join("assets", "答案.csv")
        self.similarity_threshold = 0.8  # 相似度阈值
        self.current_question = ""  # 保存当前问题
        self.current_answers = []  # 保存当前答案列表

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数
                     格式: {"question": "要匹配的问题"}
        :param context: 运行上下文
        :return: 是否执行成功。
        """

        print("开始执行自定义动作：问题匹配")

        # 获取问题和答案
        question = self.get_question(context)
        print(f"识别的问题: {question}")

        if not question:
            print("错误：未能识别到问题")
            return False

        answers = self.get_answer(context)
        print(f"识别的答案: {answers}")

        if not answers:
            print("错误：未能识别到答案")
            return False

        # 保存当前问题和答案，供后续使用
        self.current_question = question
        self.current_answers = answers

        # 确保assets文件夹存在
        os.makedirs("assets", exist_ok=True)

        # 查找或保存问题
        correct_answer = self.find_or_save_question(question, answers)

        if correct_answer:
            print(f"找到正确答案: {correct_answer}")
            # 点击正确答案
            self.click_correct_answer(context, answers, correct_answer)
            return True
        else:
            print("未找到匹配的问题，将点击第一个答案并获取正确答案")
            # 默认点击第一个答案
            if answers:
                first_answer = answers[0]
                box = first_answer['box']
                print(box)
                x, y, w, h = box
                center_x = int(x + w / 2)
                center_y = int(y + h / 2)

                context.tasker.controller.post_click(center_x, center_y).wait()
                print(f"已点击第一个答案: {first_answer['text']},点击位置为{center_x}.{center_y}")

                # 等待结果显示
                time.sleep(0.8)  # 根据实际情况调整等待时间

                # 获取并保存正确答案
                self.get_and_save_correct_answer(context)

        return True

    def get_question(self, context: Context) -> str:
        question = ""
        img = context.tasker.controller.post_screencap().wait().get()
        result = context.run_recognition("自动逢魔_识别题目", img)

        if result and result.filterd_results:
            print(f"识别到 {len(result.filterd_results)} 个文本片段")
            for r in result.filterd_results:
                print(f"文本片段: {r.text}")
                question = question + r.text
        else:
            print("警告：未能识别到题目文本")

        return question.strip()

    def get_answer(self, context: Context) -> list[dict[str, list]]:
        img = context.tasker.controller.post_screencap().wait().get()
        answers = []

        for i in range(1, 4):  # 自动循环识别三个答案
            result = context.run_recognition(f"自动逢魔_识别答案_{i}", img)
            if result and result.best_result:
                answer_data = {
                    "text": result.best_result.text.strip(),
                    "box": result.best_result.box
                }
                answers.append(answer_data)
                print(f"答案{i}: {answer_data['text']}, 位置: {answer_data['box']}")

        return answers

    def get_and_save_correct_answer(self, context: Context) -> None:
        """
        获取正确答案的标识框，通过高度匹配找到正确答案并保存
        """
        img = context.tasker.controller.post_screencap().wait().get()
        result = context.run_recognition("自动逢魔_识别正确答案", img)

        if not result or not result.best_result:
            print("警告：未能识别到正确答案标识")
            return

        correct_box = result.best_result.box
        print(f"正确答案标识框: {correct_box}")

        # 计算正确答案标识的中心Y坐标
        correct_y = (correct_box[1] + correct_box[3]) // 2
        print(f"正确答案标识中心Y坐标: {correct_y}")

        # 找到Y坐标最接近的答案
        min_distance = float('inf')
        correct_answer_text = ""
        correct_answer_index = -1

        for idx, answer in enumerate(self.current_answers):
            answer_box = answer['box']
            # 计算答案框的中心Y坐标
            answer_y = (answer_box[1] + answer_box[3]) // 2
            # 计算距离
            distance = abs(correct_y - answer_y)

            print(f"答案{idx + 1} '{answer['text']}' 中心Y坐标: {answer_y}, 距离: {distance}")

            if distance < min_distance:
                min_distance = distance
                correct_answer_text = answer['text']
                correct_answer_index = idx

        if correct_answer_text:
            print(f"识别出正确答案是第{correct_answer_index + 1}个: {correct_answer_text}")
            # 更新CSV文件中的正确答案
            self.update_correct_answer(self.current_question, correct_answer_text)
        else:
            print("错误：无法确定正确答案")

    def find_or_save_question(self, question: str, answers: list[dict[str, object]]) -> str:
        """
        在CSV文件中查找问题，如果找到返回正确答案，否则保存问题
        """
        # 检查问题是否为空
        if not question or not question.strip():
            print("警告：问题为空，无法保存")
            return None

        # 读取或创建CSV文件
        if os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path, encoding='utf-8', dtype=str)
            print(f"读取现有CSV文件，共有 {len(df)} 条记录")
        else:
            # 创建新的DataFrame
            df = pd.DataFrame(columns=['问题', '正确答案', '所有选项'])
            df.to_csv(self.csv_path, index=False, encoding='utf-8')
            print("创建新的CSV文件")

        # 查找匹配的问题
        if not df.empty:
            for idx, row in df.iterrows():
                stored_question = str(row['问题']) if pd.notna(row['问题']) else ''
                # 使用difflib进行模糊匹配
                similarity = difflib.SequenceMatcher(None, question, stored_question).ratio()
                if similarity >= self.similarity_threshold:
                    print(f"找到匹配的问题 (相似度: {similarity:.2f})")
                    correct_answer = str(row['正确答案']) if pd.notna(row['正确答案']) else ''
                    # 只返回非空的正确答案
                    return correct_answer if correct_answer else None

        # 如果没找到，保存新问题
        all_options = ','.join([ans['text'] for ans in answers])
        print(f"准备保存新问题: {question}")
        print(f"所有选项: {all_options}")

        new_row = pd.DataFrame([{
            '问题': question,
            '正确答案': '',  # 留空，等待后续填写
            '所有选项': all_options
        }])

        # 使用concat而不是append（pandas新版本推荐）
        df = pd.concat([df, new_row], ignore_index=True)

        # 保存到CSV文件
        try:
            df.to_csv(self.csv_path, index=False, encoding='utf-8')
            print(f"成功保存到CSV文件，当前共有 {len(df)} 条记录")
        except Exception as e:
            print(f"保存CSV文件时出错: {e}")

        return None

    def click_correct_answer(self, context: Context, answers: list[dict[str, object]], correct_answer: str):
        """
        点击正确答案
        """
        for answer in answers:
            if answer['text'] == correct_answer:
                # 计算答案框中心点
                box = answer['box']
                center_x = (box[0] + box[2]) // 2
                center_y = (box[1] + box[3]) // 2

                # 执行点击
                context.tasker.controller.post_click(center_x, center_y).wait()
                print(f"已点击答案: {correct_answer}")
                break
        else:
            print(f"警告：未找到正确答案 '{correct_answer}' 的位置")

    def update_correct_answer(self, question: str, correct_answer: str):
        """
        更新CSV文件中的正确答案
        """
        if not os.path.exists(self.csv_path):
            print("CSV文件不存在")
            return False

        df = pd.read_csv(self.csv_path, encoding='utf-8', dtype=str)
        updated = False

        for idx, row in df.iterrows():
            stored_question = str(row['问题']) if pd.notna(row['问题']) else ''
            similarity = difflib.SequenceMatcher(None, question, stored_question).ratio()
            if similarity >= self.similarity_threshold:
                df.at[idx, '正确答案'] = correct_answer
                updated = True
                print(f"已更新问题 '{question}' 的正确答案为: {correct_answer}")
                break

        if updated:
            try:
                df.to_csv(self.csv_path, index=False, encoding='utf-8')
                print("CSV文件更新成功")
                return True
            except Exception as e:
                print(f"更新CSV文件时出错: {e}")
                return False
        else:
            print(f"未找到匹配的问题: {question}")
            return False

    def debug_csv_content(self):
        """
        调试方法：打印CSV文件内容
        """
        if not os.path.exists(self.csv_path):
            print("CSV文件不存在")
            return

        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8', dtype=str)
            print(f"\n=== CSV文件内容 ({self.csv_path}) ===")
            print(f"总记录数: {len(df)}")
            print("\n列名:", list(df.columns))
            print("\n内容:")
            for idx, row in df.iterrows():
                print(f"\n记录 {idx + 1}:")
                print(f"  问题: {row['问题']}")
                print(f"  正确答案: {row['正确答案']}")
                print(f"  所有选项: {row['所有选项']}")
            print("=== 结束 ===\n")
        except Exception as e:
            print(f"读取CSV文件时出错: {e}")

    def stop(self):
        pass