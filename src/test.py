import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# 定义box的参数
class Box:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

# 随机生成正态分布的点
def generate_random_point(box):
    center_x = box.x + box.w / 2
    center_y = box.y + box.h / 2

    random_x = random.gauss(center_x, box.w / 6)
    random_y = random.gauss(center_y, box.h / 6)

    # 限制生成的点在box范围内
    random_x = min(max(random_x, box.x), box.x + box.w)
    random_y = min(max(random_y, box.y), box.y + box.h)

    return random_x, random_y

# 初始化图像
def init():
    scat.set_offsets(np.empty((0, 2)))  # 清空散点，二维空数组
    return scat,

# 动画更新函数
def update(frame):
    point = generate_random_point(box)
    points.append(point)
    scat.set_offsets(points)
    return scat,

# 定义box
box = Box(x=377, y=138, w=55, h=24)

# 初始化数据
points = []

# 创建绘图
fig, ax = plt.subplots(figsize=(8, 6))
scat = ax.scatter([], [], alpha=0.5, s=10, label='Random Points')

# 绘制box边框
ax.plot([box.x, box.x + box.w, box.x + box.w, box.x, box.x],
        [box.y, box.y, box.y + box.h, box.y + box.h, box.y], 'r-', label='Box Border')

ax.set_xlim(box.x - 10, box.x + box.w + 10)
ax.set_ylim(box.y - 10, box.y + box.h + 10)
ax.set_xlabel('X Axis')
ax.set_ylabel('Y Axis')
ax.set_title('Random Points within the Box (Gaussian Distribution)')
ax.legend()
ax.grid(True)

# 创建动画
ani = animation.FuncAnimation(fig, update, frames=1000, init_func=init, blit=True, interval=10, repeat=False)

# 显示动画
plt.show()
