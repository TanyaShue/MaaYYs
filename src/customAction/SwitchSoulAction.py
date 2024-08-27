from annotations.custom_Annotation import customAction
from maa.custom_action import CustomAction
import json

@customAction
class SwitchSoulAction(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        custom_param = json.loads(custom_param)
        context.swipe()
        return True
    
    
    def stop(self) -> None:
        pass