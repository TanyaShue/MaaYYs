from maa.custom_action import CustomAction
import random
import json

class RandomSwipe(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        """
        执行滑动操作，从 custom_param 中获取起始和结束区域，生成随机点并执行滑动。

        :param context: 运行上下文，提供 swipe 方法。
        :param task_name: 任务名称。
        :param custom_param: 自定义参数，包含 {start_roi, end_roi ,delay}(start_roi:起始区域,end_roi:结束区域,delay:滑动间隔时间)
        :param box: 识别到的区域。
        :param rec_detail: 识别的详细信息。

        :return: 滑动是否成功。
        """        
        try:
            params = json.loads(custom_param)

            # 随机生成start点
            start_x = random.randint(params["start_roi"][0], params["start_roi"][0] + params["start_roi"][2])
            start_y = random.randint(params["start_roi"][1], params["start_roi"][1] + params["start_roi"][3])

            # 随机生成end点
            end_x = random.randint(params["end_roi"][0], params["end_roi"][0] + params["end_roi"][2])
            end_y = random.randint(params["end_roi"][1], params["end_roi"][1] + params["end_roi"][3])

            duration = params.get("delay", 200)

            context.swipe(start_x, start_y, end_x, end_y, duration)
            print(f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y}) with delay {duration}")
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Swipe action failed: {e}")
            return False
        
    
    def stop(self) -> None:
        pass
