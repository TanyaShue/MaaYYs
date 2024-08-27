from maa.custom_action import CustomAction
import random

class Random_touch(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        print(custom_param)
        print("开始执行自定义动作：随机点击")
        x, y, w, h = box.x, box.y, box.w, box.h
        center_x = x + w / 2
        center_y = y + h / 2
        random_x = random.gauss(center_x, w / 6)
        random_y = random.gauss(center_y, h / 6)
        random_x = min(max(random_x, x), x + w)
        random_y = min(max(random_y, y), y + h)
        context.click(round(random_x), round(random_y))
        print(f"随机生成的点: {random_x, random_y}")
        return True

    def stop(self) -> None:
        pass
