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


class QuestionMatcher(CustomAction):
    def __init__(self):
        super().__init__()
        self.csv_path = os.path.join("assets", "答案.csv")
        self.api_base_url = "https://csv-data-collector.disjoint7.workers.dev/"  # 替换为实际的 API URL
        self.similarity_threshold = 0.8  # 相似度阈值
        self.current_question = ""  # 保存当前问题
        self.current_answers = []  # 保存当前答案列表
        self.data_modified = False  # 标记数据是否被修改

        # 统计信息
        self.stats = {
            "total_questions": 0,  # 总问题数
            "correct_from_db": 0,  # 从题库正确回答的数量
            "wrong_from_db": 0,  # 题库答案错误的数量
            "new_questions": 0,  # 新问题数量
        }

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数
                     格式: {"upload": bool, "sync": bool}
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        # 读取 custom_param 的参数
        json_data = json.loads(argv.custom_action_param)

        # 获取参数
        upload = json_data.get("upload", True)  # 是否上传修改后的数据
        sync = json_data.get("sync", True)  # 是否从远程同步数据

        print("开始执行自定义动作：问题匹配")
        print(f"参数设置 - 同步: {sync}, 上传: {upload}")

        # 确保assets文件夹存在
        os.makedirs("assets", exist_ok=True)

        # 从远程同步数据
        if sync:
            if not self.sync_from_remote():
                print("警告：远程同步失败，将使用本地数据")

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

        # 查找或保存问题
        correct_answer = self.find_or_save_question(question, answers)
        self.stats["total_questions"] += 1

        if correct_answer:
            print(f"找到正确答案: {correct_answer}")
            # 点击正确答案
            self.click_correct_answer(context, answers, correct_answer)

            # 等待结果显示
            time.sleep(0.8)

            # 即使点击了"正确答案"，也要验证实际的正确答案
            print("验证答案正确性...")
            actual_correct = self.get_and_save_correct_answer(context)

            # 如果实际正确答案与点击的不同，说明题库需要更新
            if actual_correct:
                if actual_correct != correct_answer:
                    print(f"警告：题库答案错误！题库答案：{correct_answer}，实际正确答案：{actual_correct}")
                    self.data_modified = True
                    self.stats["wrong_from_db"] += 1
                else:
                    print(f"题库答案正确！")
                    self.stats["correct_from_db"] += 1
            else:
                print("警告：无法验证答案正确性")
                self.stats["correct_from_db"] += 1  # 假设正确
        else:
            print("未找到匹配的问题，将点击第一个答案并获取正确答案")
            self.stats["new_questions"] += 1
            # 默认点击第一个答案
            if answers:
                first_answer = answers[0]
                box = first_answer['box']
                x, y, w, h = box
                center_x = int(x + w / 2)
                center_y = int(y + h / 2)

                context.tasker.controller.post_click(center_x, center_y).wait()
                print(f"已点击第一个答案: {first_answer['text']},点击位置为{center_x},{center_y}")

                # 等待结果显示
                time.sleep(0.8)  # 根据实际情况调整等待时间

                # 获取并保存正确答案
                self.get_and_save_correct_answer(context)

        # 输出统计信息
        self.print_statistics()

        # 如果数据被修改且需要上传，则上传到远程
        if upload and self.data_modified:
            if self.upload_to_remote():
                print("数据已成功上传到远程服务器")
            else:
                print("警告：数据上传失败，仅保存在本地")

        return True

    def sync_from_remote(self) -> bool:
        """
        从远程服务器同步数据
        """
        try:
            print("正在从远程服务器同步数据...")
            response = requests.get(f"{self.api_base_url}/api/data", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    # 转换为 DataFrame
                    df = pd.DataFrame(data["data"])

                    # 保存到本地 CSV
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
        """
        上传本地数据到远程服务器
        """
        try:
            if not os.path.exists(self.csv_path):
                print("本地CSV文件不存在，无法上传")
                return False

            print("正在上传数据到远程服务器...")

            # 读取本地CSV文件
            with open(self.csv_path, 'rb') as f:
                files = {'file': ('答案.csv', f, 'text/csv')}
                response = requests.post(
                    f"{self.api_base_url}/api/upload",
                    files=files,
                    timeout=30
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    stats = result.get("stats", {})
                    print(f"上传成功！新增 {stats.get('newRows', 0)} 条记录")
                    self.data_modified = False  # 重置修改标记
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

    def get_and_save_correct_answer(self, context: Context) -> str:
        """
        获取正确答案的标识框，通过高度匹配找到正确答案并保存
        返回识别到的正确答案文本
        """
        img = context.tasker.controller.post_screencap().wait().get()
        result = context.run_recognition("自动逢魔_识别正确答案", img)

        if not result or not result.best_result:
            print("警告：未能识别到正确答案标识")
            return ""

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
            if self.update_correct_answer(self.current_question, correct_answer_text):
                self.data_modified = True  # 标记数据已修改
            return correct_answer_text
        else:
            print("错误：无法确定正确答案")
            return ""

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
            self.data_modified = True  # 标记数据已修改
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

    def update_correct_answer(self, question: str, correct_answer: str) -> bool:
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
                # 检查是否需要更新
                old_answer = str(row['正确答案']) if pd.notna(row['正确答案']) else ''
                if old_answer != correct_answer:
                    df.at[idx, '正确答案'] = correct_answer
                    updated = True
                    print(f"已更新问题 '{question}' 的正确答案为: {correct_answer}")
                else:
                    print(f"问题 '{question}' 的答案已经是最新的")
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
            if not any(difflib.SequenceMatcher(None, question, str(row['问题']) if pd.notna(
                    row['问题']) else '').ratio() >= self.similarity_threshold for idx, row in df.iterrows()):
                print(f"未找到匹配的问题: {question}")
            return False

    def print_statistics(self):
        """
        打印统计信息
        """
        print("\n=== 答题统计 ===")
        print(f"总回答题数: {self.stats['total_questions']}")
        print(f"题库正确回答: {self.stats['correct_from_db']}")
        print(f"题库答案错误: {self.stats['wrong_from_db']}")
        print(f"新遇到的问题: {self.stats['new_questions']}")

        if self.stats['total_questions'] > 0:
            accuracy = (self.stats['correct_from_db'] / self.stats['total_questions']) * 100
            print(f"题库准确率: {accuracy:.1f}%")
        print("================\n")


    def stop(self):
        """
        停止动作时的清理工作
        """
        # 如果还有未上传的修改，尝试上传
        if self.data_modified:
            print("检测到未上传的修改，尝试上传...")
            self.upload_to_remote()
        pass