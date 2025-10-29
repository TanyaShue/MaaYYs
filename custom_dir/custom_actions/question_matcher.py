# -*- coding: UTF-8 -*-
import json
import os
import difflib
import time
import requests
import io

import pandas as pd
from datetime import datetime

from maa.context import Context
from maa.custom_action import CustomAction

from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("QuestionMatcher")
class QuestionMatcher(CustomAction):
    def __init__(self):
        super().__init__()
        self.csv_path = os.path.join("assets", "答案.csv")
        self.api_base_url = "https://csv-data-collector.disjoint7.workers.dev/"
        self.similarity_threshold = 0.8
        self.current_question = ""
        self.current_answers = []
        self.data_modified = False

        self.stats = {
            "total_questions": 0,
            "correct_from_db": 0,
            "wrong_from_db": 0,
            "new_questions": 0,
        }

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        json_data = json.loads(argv.custom_action_param)
        upload = json_data.get("upload", True)
        sync = json_data.get("sync", True)

        print("开始执行自定义动作：问题匹配")
        print(f"参数设置 - 同步: {sync}, 上传: {upload}")

        os.makedirs("assets", exist_ok=True)

        if sync:
            if not self.sync_from_remote():
                print("警告：远程同步失败，将使用本地数据")

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

        self.current_question = question
        self.current_answers = answers
        self.stats["total_questions"] += 1

        # 查找问题，返回一个已知正确答案的列表
        known_answers = self.find_or_save_question(question, answers)

        # 默认点击第一个答案的函数
        def click_first_and_learn():
            if answers:
                first_answer = answers[0]
                box = first_answer['box']
                x, y, w, h = box
                center_x = int(x + w / 2)
                center_y = int(y + h / 2)
                context.tasker.controller.post_click(center_x, center_y).wait()
                print(f"已点击第一个答案: {first_answer['text']}, 点击位置为({center_x},{center_y})")
                time.sleep(0.8)
                self.get_and_save_correct_answer(context)

        if known_answers:
            print(f"题库中找到的已知答案: {known_answers}")
            clicked_answer = self.click_correct_answer(context, answers, known_answers)

            if clicked_answer:
                # 成功点击了题库中的一个答案，现在验证它
                time.sleep(1)
                print("验证答案正确性...")
                actual_correct = self.get_and_save_correct_answer(context)

                if actual_correct:
                    if actual_correct != clicked_answer:
                        print(f"警告：题库答案错误！我们点击了：{clicked_answer}，但实际正确答案是：{actual_correct}")
                        self.stats["wrong_from_db"] += 1
                    else:
                        print("题库答案正确！")
                        self.stats["correct_from_db"] += 1
                else:
                    print("警告：无法验证答案正确性，假设题库正确。")
                    self.stats["correct_from_db"] += 1
            else:
                # **新逻辑：题库有答案，但当前屏幕选项中一个都匹配不上**
                print("题库中已知的答案均未在当前选项中找到，将默认选择第一个答案。")
                self.stats["new_questions"] += 1  # 视为新情况
                click_first_and_learn()
        else:
            # 题库中完全没有这个问题
            print("未找到匹配的问题，将点击第一个答案并获取正确答案")
            self.stats["new_questions"] += 1
            click_first_and_learn()

        self.print_statistics()

        if upload and self.data_modified:
            if self.upload_to_remote():
                print("数据已成功上传到远程服务器")
            else:
                print("警告：数据上传失败，仅保存在本地")
        return True

    def find_or_save_question(self, question: str, answers: list[dict[str, object]]) -> list[str]:
        """
        在CSV文件中查找问题。
        - 如果找到，返回一个包含所有已知正确答案的列表。
        - 如果未找到，保存新问题并返回一个空列表。
        """
        if not question or not question.strip():
            print("警告：问题为空，无法保存")
            return []

        if os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path, encoding='utf-8', dtype=str).fillna('')
        else:
            df = pd.DataFrame(columns=['问题', '正确答案', '所有选项'])
            df.to_csv(self.csv_path, index=False, encoding='utf-8')
            print("创建新的CSV文件")

        if not df.empty:
            for idx, row in df.iterrows():
                stored_question = str(row['问题'])
                similarity = difflib.SequenceMatcher(None, question, stored_question).ratio()

                if similarity >= self.similarity_threshold:
                    print(f"找到匹配的问题 (相似度: {similarity:.2f})")
                    correct_answers_str = str(row['正确答案'])
                    # 如果正确答案字符串不为空，则按分隔符'|'拆分为列表
                    return correct_answers_str.split('|') if correct_answers_str else []

        # 如果没找到，保存新问题
        all_options = ','.join([ans['text'] for ans in answers])
        new_row = pd.DataFrame([{'问题': question, '正确答案': '', '所有选项': all_options}])
        df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_csv(self.csv_path, index=False, encoding='utf-8')
            print(f"成功保存新问题到CSV文件，当前共有 {len(df)} 条记录")
            self.data_modified = True
        except Exception as e:
            print(f"保存CSV文件时出错: {e}")

        return []  # 对于新问题，返回空列表

    def click_correct_answer(self, context: Context, answers: list[dict[str, object]],
                             known_correct_answers: list[str]) -> str:
        """
        在屏幕上的选项中查找并点击一个已知的正确答案。
        返回实际点击的答案文本，如果没找到则返回 None。
        """
        for screen_answer in answers:
            if screen_answer['text'] in known_correct_answers:
                box = screen_answer['box']
                center_x = (box[0] + box[2]) // 2
                center_y = (box[1] + box[3]) // 2
                context.tasker.controller.post_click(center_x, center_y).wait()
                print(f"已从题库中找到并点击答案: {screen_answer['text']}, 位置:({center_x},{center_y})")
                return screen_answer['text']

        return None  # 表示没有找到可点击的答案

    def update_correct_answer(self, question: str, new_correct_answer: str) -> bool:
        """
        更新CSV文件：将新的正确答案追加到该问题的答案列表中，确保不重复。
        """
        if not os.path.exists(self.csv_path):
            print("CSV文件不存在")
            return False

        df = pd.read_csv(self.csv_path, encoding='utf-8', dtype=str).fillna('')
        updated = False

        for idx, row in df.iterrows():
            stored_question = str(row['问题'])
            similarity = difflib.SequenceMatcher(None, question, stored_question).ratio()
            if similarity >= self.similarity_threshold:
                old_answers_str = str(row['正确答案'])
                known_answers = old_answers_str.split('|') if old_answers_str else []

                if new_correct_answer not in known_answers:
                    known_answers.append(new_correct_answer)
                    new_answers_str = '|'.join(known_answers)
                    df.at[idx, '正确答案'] = new_answers_str
                    updated = True
                    print(f"已将新答案 '{new_correct_answer}' 添加到问题 '{question}' 的答案库中。")
                else:
                    print(f"答案 '{new_correct_answer}' 已存在于题库中，无需更新。")
                break

        if updated:
            try:
                df.to_csv(self.csv_path, index=False, encoding='utf-8')
                print("CSV文件更新成功")
                return True
            except Exception as e:
                print(f"更新CSV文件时出错: {e}")
        return False

    # --- 以下函数无需修改 ---

    def sync_from_remote(self) -> bool:
        try:
            print("正在从远程服务器同步数据...")
            response = requests.get(f"{self.api_base_url}/api/data", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    df = pd.DataFrame(data["data"])
                    df.to_csv(self.csv_path, index=False, encoding='utf-8')
                    print(f"成功同步 {len(df)} 条数据到本地")
                    return True
                else:
                    print("远程服务器暂无数据")
                    return True
            else:
                print(f"同步失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"同步数据时发生错误: {e}")
            return False

    def upload_to_remote(self) -> bool:
        try:
            if not os.path.exists(self.csv_path):
                return False
            print("正在上传数据到远程服务器...")
            with open(self.csv_path, 'rb') as f:
                files = {'file': ('答案.csv', f, 'text/csv')}
                response = requests.post(
                    f"{self.api_base_url}/api/upload",
                    files=files,
                    timeout=5
                )
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    stats = result.get("stats", {})
                    print(f"上传成功！新增 {stats.get('newRows', 0)} 条记录")
                    self.data_modified = False
                    return True
                else:
                    print(f"上传失败: {result.get('error', '未知错误')}")
                    return False
            else:
                print(f"上传失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"上传数据时发生错误: {e}")
            return False

    def get_question(self, context: Context) -> str:
        question = ""
        img = context.tasker.controller.post_screencap().wait().get()
        result = context.run_recognition("自动逢魔_识别题目", img)
        if result and result.filterd_results:
            for r in result.filterd_results:
                question = question + r.text
        else:
            print("警告：未能识别到题目文本")
        return question.strip()

    def get_answer(self, context: Context) -> list[dict[str, list]]:
        img = context.tasker.controller.post_screencap().wait().get()
        answers = []
        for i in range(1, 4):
            result = context.run_recognition(f"自动逢魔_识别答案_{i}", img)
            if result and result.best_result:
                answers.append({
                    "text": result.best_result.text.strip(),
                    "box": result.best_result.box
                })
        return answers

    def get_and_save_correct_answer(self, context: Context) -> str:
        img = context.tasker.controller.post_screencap().wait().get()
        result = context.run_recognition("自动逢魔_识别正确答案", img)
        if not result or not result.best_result:
            print("警告：未能识别到正确答案标识")
            return ""

        correct_box = result.best_result.box
        correct_y = (correct_box[1] + correct_box[3]) // 2
        min_distance = float('inf')
        correct_answer_text = ""
        for answer in self.current_answers:
            answer_y = (answer['box'][1] + answer['box'][3]) // 2
            distance = abs(correct_y - answer_y)
            if distance < min_distance:
                min_distance = distance
                correct_answer_text = answer['text']

        if correct_answer_text:
            print(f"识别出实际正确答案是: {correct_answer_text}")
            if self.update_correct_answer(self.current_question, correct_answer_text):
                self.data_modified = True
            return correct_answer_text
        else:
            print("错误：无法确定正确答案")
            return ""

    def print_statistics(self):
        print("\n=== 答题统计 ===")
        print(f"总回答题数: {self.stats['total_questions']}")
        print(f"题库正确回答: {self.stats['correct_from_db']}")
        print(f"题库答案错误: {self.stats['wrong_from_db']}")
        print(f"新情况(新问题/选项不符): {self.stats['new_questions']}")
        if self.stats['total_questions'] > 0:
            # 修正准确率计算，仅基于题库有答案的情况
            db_attempts = self.stats['correct_from_db'] + self.stats['wrong_from_db']
            if db_attempts > 0:
                accuracy = (self.stats['correct_from_db'] / db_attempts) * 100
                print(f"题库命中准确率: {accuracy:.1f}%")
        print("================\n")

    def stop(self):
        if self.data_modified:
            print("检测到未上传的修改，尝试在停止前上传...")
            self.upload_to_remote()
        pass