from .logger import Logger
from collections import deque

DEFAULT_MAX_LEN = 1000


class InMemoryLogger(Logger):
    """
    A simple logging class that saves monitored data in an in-memory list
    under self.latest_messages.
    """

    def __init__(self, max_len=DEFAULT_MAX_LEN):
        self.latest_messages = deque(maxlen=max_len)

    def log(self, message: dict, context_id=None, export_timestamp=None):
        self.latest_messages.append(
            {
                "message": message,
                "context_id": context_id,
                "export_timestamp": export_timestamp,
            }
        )

    async def alog(
        self, message: dict, context_id=None, export_timestamp=None
    ):
        self.log(message, context_id, export_timestamp)
