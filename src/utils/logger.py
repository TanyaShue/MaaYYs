import os
import logging
import shutil
import time

# 压缩日志文件的函数
def compress_log_file(log_file_path):
    # 获取当前时间戳
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    # 构建压缩文件的名称
    compressed_log_name = f"app_log_{timestamp}.bak"

    # 压缩日志文件
    with open(log_file_path, 'rb') as log_file:
        with open(compressed_log_name, 'wb') as compressed_file:
            shutil.copyfileobj(log_file, compressed_file)

    # 清空原日志文件
    open(log_file_path, 'w').close()


# 配置日志的函数
def setup_logging(log_file_path):
    # 确保日志文件所在的目录存在
    log_directory = os.path.dirname(log_file_path)
    os.makedirs(log_directory, exist_ok=True)  # 使用 exist_ok 避免手动检查

    # 配置日志记录
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s][%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, mode='a', encoding="UTF-8"),  # 追加模式
            logging.StreamHandler()
        ]
    )

    # 检查并压缩日志文件
    if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 128 * 1024 * 1024:  # 128MB
        compress_log_file(log_file_path)