import random
from maa.custom_action import CustomAction
from annotations.custom_Annotation import customAction

@customAction
class Random_touch(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        
        print(custom_param)

        
        print("开始执行自定义动作：随机点击")
        # 读取 box 的参数
        x, y, w, h = box.x, box.y, box.w, box.h
        
        print(f"box参数: {box}")
        
        # 计算中心点的坐标
        center_x = x + w / 2
        center_y = y + h / 2
        
        # 使用正态分布随机生成点
        random_x = random.gauss(center_x, w / 6)  # 6 chosen to keep most points within the box
        random_y = random.gauss(center_y, h / 6)  # Adjusting sigma for distribution width
        
        # 限制生成的点在box范围内
        random_x = min(max(random_x, x), x + w)
        random_y = min(max(random_y, y), y + h)

        # 点击随机生成的点
        context.click(round(random_x), round(random_y))
        print(f"随机生成的点: {random_x, random_y}")
                
        return True
    def stop(self) -> None:
        pass