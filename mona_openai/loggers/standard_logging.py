from .logger import Logger
from logging import getLogger, INFO


class StandardLogger(Logger):
    """
    A simple logging class that logs monitored data using python's logging
    package.
    """

    def __init__(
        self,
        logging_level=INFO,
        underlying_logger=None,
    ):
        self.underlying_logger = underlying_logger or getLogger("Mona")
        self.level = logging_level

    def log(self, message: dict, context_id=None, export_timestamp=None):
        self.underlying_logger.log(
            self.level,
            {
                "message": message,
                "context_id": context_id,
                "export_timestamp": export_timestamp,
            },
        )

    async def alog(
        self, message: dict, context_id=None, export_timestamp=None
    ):
        return self.log(message, context_id, export_timestamp)

    def start_monitoring(self, openai_class_name):
        self.underlying_logger.log(
            self.level, f"Started monitoring for OpenAI's {openai_class_name}"
        )
