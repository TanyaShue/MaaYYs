from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QCheckBox, QComboBox
)


class SettingsContainer(QWidget):
    def __init__(self, parent=None, width=280):
        super().__init__(parent)
        self._expanded = False
        self._target_width = width
        self._animation_duration = 250

        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        # Constants for styling and layout
        self.HEADER_HEIGHT = 28

        # Main layout setup
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Title frame
        # self._create_title_frame(main_layout)

        # Scroll area setup
        self._create_scroll_area(main_layout)

        # Initial state
        self.setFixedWidth(0)
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)

    # def _create_title_frame(self, main_layout):
    #     self.title_frame = QFrame()
    #     self.title_frame.setFixedHeight(self.HEADER_HEIGHT)
    #     self.title_frame.setObjectName("SettingsHeader")
    #
    #     title_layout = QHBoxLayout(self.title_frame)
    #     title_layout.setContentsMargins(8, 0, 8, 0)
    #
    #     self.title_label = QLabel("设置选项")
    #     self.title_label.setObjectName("SettingsTitle")
    #     title_layout.addWidget(self.title_label)
    #
    #     self.toggle_button = QPushButton("展开")
    #     self.toggle_button.clicked.connect(self.toggle_visibility)
    #     self.toggle_button.setObjectName("ToggleButton")
    #     title_layout.addWidget(self.toggle_button)
    #
    #     main_layout.addWidget(self.title_frame)

    def _create_scroll_area(self, main_layout):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("SettingsScrollArea")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Settings container
        self.settings_container = QWidget()
        self.settings_container.setObjectName("SettingsInnerContainer")

        self.settings_layout = QVBoxLayout(self.settings_container)
        self.settings_layout.setSpacing(8)
        self.settings_layout.setContentsMargins(8, 8, 8, 8)
        self.settings_layout.setAlignment(Qt.AlignTop)
        self.settings_layout.addStretch()

        self.scroll_area.setWidget(self.settings_container)
        main_layout.addWidget(self.scroll_area)

    def _setup_animations(self):
        # Pre-create animation objects
        self._width_animation = QPropertyAnimation(self, b"maximumWidth")
        self._min_width_animation = QPropertyAnimation(self, b"minimumWidth")

        # Common animation settings
        for anim in [self._width_animation, self._min_width_animation]:
            anim.setDuration(self._animation_duration)
            anim.setEasingCurve(QEasingCurve.InOutCubic)

    def toggle_visibility(self):
        """Toggle the visibility of the settings container."""
        # Prevent multiple simultaneous animations
        if (self._width_animation.state() == QPropertyAnimation.Running or
                self._min_width_animation.state() == QPropertyAnimation.Running):
            return

        # Determine target width and button text
        target_width = self._target_width if not self._expanded else 0
        # self.toggle_button.setText("收起" if not self._expanded else "展开")

        # Configure and start animations
        for anim, prop in [(self._width_animation, "maximumWidth"),
                           (self._min_width_animation, "minimumWidth")]:
            anim.setPropertyName(prop.encode())
            anim.setStartValue(self.width())
            anim.setEndValue(target_width)

        self._width_animation.start()
        self._min_width_animation.start()

        self._expanded = not self._expanded

    def show_container(self, immediate=False):
        """
        Show the settings container.

        :param immediate: If True, shows the container without animation
        """
        if self._expanded:
            return

        if immediate:
            self.setFixedWidth(self._target_width)
            self.setMinimumWidth(self._target_width)
            self.setMaximumWidth(self._target_width)
            # self.toggle_button.setText("收起")
            self._expanded = True
        else:
            self.toggle_visibility()

    def hide_container(self, immediate=False):
        """
        Hide the settings container.

        :param immediate: If True, hides the container without animation
        """
        if not self._expanded:
            return

        if immediate:
            self.setFixedWidth(0)
            self.setMinimumWidth(0)
            self.setMaximumWidth(0)
            # self.toggle_button.setText("展开")
            self._expanded = False
        else:
            self.toggle_visibility()