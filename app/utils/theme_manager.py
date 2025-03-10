import os

from PySide6.QtWidgets import QApplication


class ThemeManager:
    def __init__(self):
        self.themes = {
            "dark": "assets/themes/dark.qss",
            "light": "assets/themes/light.qss"
        }
        self.current_theme = None

    def apply_theme(self, theme_name):
        if theme_name not in self.themes:
            print(f"Theme {theme_name} not found")
            return

        theme_path = self.themes[theme_name]
        if not os.path.exists(theme_path):
            print(f"Theme file {theme_path} not found")
            return

        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
                QApplication.instance().setStyleSheet(stylesheet)

            self.current_theme = theme_name
            print(f"Applied theme: {theme_name}")
        except Exception as e:
            print(f"Error applying theme: {e}")

    def get_current_theme(self):
        return self.current_theme