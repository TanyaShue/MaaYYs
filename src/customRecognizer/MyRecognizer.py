from typing import Tuple
from maa.define import RectType
from maa.custom_recognizer import CustomRecognizer
from annotations.custom_Annotation import customRecognizer
from customAction.Find_answer import Find_answer
from common.common import check_if_rect_is_inside_any


@customRecognizer
class MyRecognizer(CustomRecognizer):
    print("MyRecognizer loaded")
    def analyze(
            self, context, image, task_name, custom_param
        ) -> Tuple[bool,RectType, str]:
        # 假设 Find_answer.answer 是一个包含多个答案的列表
        possible_answers = Find_answer.answer
        # image = cv2.imread("Screenshot_2024.08.19_17.04.27.366.png")
        print(f"Possible answers: {possible_answers}")
        print("------------------hellow-----------------")

        entry = "OCR"
        
        for answer in possible_answers:
            param = {
                "OCR": {
                    "recognition": "OCR",
                    "expected": answer,
                    "roi": [902, 174, 328, 397]
                }
            }
            rec_ = context.run_recognition(image, entry, param)
            if image is None:
                rec_[1].x, rec_[1].y, rec_[1].w, rec_[1].h = 100,200,200,100
                return True, rec_[1], "No match found"

            # 检查识别结果，假设 rec_ 返回的是包含识别到的答案的元组
            recognized_text = rec_[2]  # 假设识别到的文本在这个位置
            print(rec_[1])
            # 判断识别到的文本是否匹配当前答案
            if recognized_text and answer in recognized_text:
                print(f"开始匹配答案: {answer}")
                rectangles = [
                (906,281,323,65),  # 示例矩形1
                (904,399,325,59),  # 示例矩形2
                (904,169,324,69),   # 示例矩形3
                (902,509,329,59)    # 示例矩形4，特别包含 Rect(904, 300, 200, 20)
                ]
                is_inside_any, enclosing_rect = check_if_rect_is_inside_any(rectangles, rec_[1])

                if is_inside_any:
                    print(f"Rect {rec_[1]} is inside the rectangle {enclosing_rect}.")
                    rec_[1].x, rec_[1].y, rec_[1].w, rec_[1].h = enclosing_rect[0],enclosing_rect[1],enclosing_rect[2],enclosing_rect[3]
                    return rec_

                else:
                    print(f"Rect {rec_[1]} is not inside any of the rectangles.xxxxxxxxxxxxxxxxxxxxxxxxx")
                                    
        # 如果没有找到匹配，返回一个默认值
        print("没找到答案--------------------------")
        rec_[1].x, rec_[1].y, rec_[1].w, rec_[1].h = 100,200,200,100
        return True, rec_[1], "No match found"
