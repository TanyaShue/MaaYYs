from maa.custom_action import CustomAction
from common.common import find_best_answer
from annotations.custom_Annotation import customAction
import json


@customAction
class Find_answer(CustomAction):
    question = ""
    qa_dict_v2 = ""
    answer = []

    def __init__(self):
        super().__init__()
        # 调试输出，确认 _is_custom_action 属性是否存在
        print(f"Init Find_answer, _is_custom_action: {hasattr(self, '_is_custom_action')}")

    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        # 解析 JSON 字符串为字典对象
        rec_detail = json.loads(rec_detail)
        print(self.question)
        # 将所有的 text 属性连接成一个长字符串
        self.question = ''.join([item['text'] for item in rec_detail['all']])
        self.answer = find_best_answer(self.question, self.qa_dict_v2)
        print(f"问题为：{self.question}")
        print(f"答案为：{self.answer}")
        return True

    def stop(self) -> None:
        pass
