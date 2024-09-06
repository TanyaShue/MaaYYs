# logger_module.py
import time

class Logger:
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
            self.log_output.config(state='normal')  # 允许编辑
            self.log_output.insert("end", f"{time.strftime('%H:%M:%S', time.localtime())}: {message}\n")
            self.log_output.see("end")
            self.log_output.config(state='disabled')  # 禁止编辑
            
    
    def add_log_thread_safe(self, message):
        if self.log_output:
            self.log_output.after(0, self.add_log, message)

            

