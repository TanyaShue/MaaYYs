from annotations.custom_Annotation import customAction
from maa.custom_action import CustomAction
import json

@customAction
class Random_swipe(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        print("开始执行自定义动作：随机滑动")
        custom_param = json.loads(custom_param)
        print(custom_param)
        return True
    
    
    def stop(self) -> None:
        pass