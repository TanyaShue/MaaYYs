from maa.custom_action import CustomAction
import random
import json


class SwitchSoul(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        """
        执行滑动操作，从 custom_param 中获取起始和结束区域，生成随机点并执行滑动。

        :param context: 运行上下文，提供 swipe 方法。
        :param task_name: 任务名称。
        :param custom_param: 自定义参数
        :param box: 识别到的区域。
        :param rec_detail: 识别的详细信息。

        :return: 滑动是否成功。
        """             
        # 读取 box 的参数
        json_data = json.loads(custom_param)     
        print(json_data)
    
         
        return True


    def stop(self) -> None:
        pass

