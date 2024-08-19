import time
import random

# 生成一个随机的等待时间，范围可以是 1 到 10 秒
wait_time = random.uniform(1, 10)

# 打印等待时间
print(f"等待 {wait_time:.2f} 秒...")

# 等待指定的时间
time.sleep(wait_time)

print("等待结束！")
