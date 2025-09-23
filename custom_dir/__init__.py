from maa.context import Context


def print_to_ui(context:Context,message,leve:str="info"):
    context.run_task("自定义输出", {"自定义输出": {"focus": {"start": f"{message}"}}})
