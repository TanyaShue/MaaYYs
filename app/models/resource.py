# app/models/resource.py
class ResourceSetting:
    def __init__(self, name, setting_type, value, options=None):
        self.name = name
        self.type = setting_type  # checkbox, combobox, input
        self.value = value
        self.options = options or []


class SettingGroup:
    def __init__(self, name, settings=None):
        self.name = name
        self.settings = settings or []


class Resource:
    def __init__(self, name, enabled=True, settings=None):
        self.name = name
        self.enabled = enabled
        self.settings = settings or []  # List of SettingGroup

    @classmethod
    def get_sample_resources(cls):
        return [
            cls("战双软件件", True, [
                SettingGroup("基本设置", [
                    ResourceSetting("启用自动战斗", "checkbox", True),
                    ResourceSetting("战斗难度", "combobox", "普通", ["简单", "普通", "困难"])
                ]),
                SettingGroup("高级设置", [
                    ResourceSetting("每日战斗次数", "input", "10"),
                    ResourceSetting("自动使用体力药", "checkbox", False)
                ])
            ]),
            cls("阴阳师", True, [
                SettingGroup("基本设置", [
                    ResourceSetting("自动接受邀请", "checkbox", True),
                    ResourceSetting("副本选择", "combobox", "御魂", ["御魂", "觉醒", "探索"])
                ]),
                SettingGroup("高级设置", [
                    ResourceSetting("运行时间(分钟)", "input", "60"),
                    ResourceSetting("自动接收礼物", "checkbox", True)
                ])
            ])
        ]