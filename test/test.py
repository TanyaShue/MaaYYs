import ctypes

from maa.library import Library


try:
    Library.framework_libpath=r"D:\DeveEnvironment\Program\Anaconda\envs\maafwtest\Lib\site-packages\maa\bin\MaaFramework.dll"

    Library.framework = ctypes.WinDLL(str(Library.framework_libpath))
except OSError:
    print("导入失败")

from ui.test import MainWindow
from PySide6.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
