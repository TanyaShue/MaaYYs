from datetime import datetime
from typing import Optional


class LogEntry:
    def __init__(self, message: str, level: str = "INFO", task_id: Optional[str] = None):
        self.timestamp = datetime.now()
        self.message = message
        self.level = level
        self.task_id = task_id

    def to_dict(self) -> dict:
        return {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": self.message,
            "level": self.level,
            "task_id": self.task_id
        }
