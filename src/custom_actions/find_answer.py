from maa.context import Context
from maa.custom_action import CustomAction

from src.utils.common import find_best_answer


class FindAnswer(CustomAction):
    question = ""
    qa_dict_v2 = ""
    answer = []

    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        rec_detail = argv.reco_detail
        self.question = ''.join([item.text for item in rec_detail.all_results])
        self.answer = find_best_answer(self.question, self.qa_dict_v2)
        print(f"问题为：{self.question}")
        print(f"答案为：{self.answer}")
        return True

    def stop(self) -> None:
        pass
