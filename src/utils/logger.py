# logger_module.py
import time

class Logger:
    log_output: object
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.log_output = None
        return cls._instance


    def set_log_output(self, log_output):
        self.log_output = log_output


    def add_log(self, message):
        if self.log_output:
            timestamp = time.strftime('%H:%M:%S', time.localtime())
            self.log_output.append(f"{timestamp}: {message}")  # 追加文本
            self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())  # 自动滚动到底部


    def add_log_thread_safe(self, message):
        if self.log_output:
            # 使用 Qt 的信号槽机制或 `QMetaObject.invokeMethod` 来确保线程安全
            self.log_output.append(f"{time.strftime('%H:%M:%S', time.localtime())}: {message}")
            self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())
