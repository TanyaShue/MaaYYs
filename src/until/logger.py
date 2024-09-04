import tkinter as tk

log_output = None

def set_log_output(output):
    global log_output
    log_output = output

def add_log(message):
    if log_output:
        log_output.insert(tk.END, f"{message}\n")
        log_output.see(tk.END)  # 自动滚动到最新的日志
