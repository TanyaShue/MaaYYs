from maa.custom_action import CustomAction
from until.common import find_best_answer
import json

class FindAnswer(CustomAction):
    question = ""
    qa_dict_v2 = ""
    answer = []


    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        rec_detail = json.loads(rec_detail)
        self.question = ''.join([item['text'] for item in rec_detail['all']])
        self.answer = find_best_answer(self.question, self.qa_dict_v2)
        print(f"问题为：{self.question}")
        print(f"答案为：{self.answer}")
        return True

    def stop(self) -> None:
        pass
