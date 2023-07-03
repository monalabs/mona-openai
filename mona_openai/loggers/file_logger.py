from .logger import Logger
import atexit
import json


class FileLogger(Logger):
    """
    A simple logging class that saves monitored data in a file.
    """

    def __init__(self, file_name):
        self.file = open(file_name, "w")

        atexit.register(self.close_file)

    def close_file(self):
        if not self.file.closed:
            self.file.close()

    def log(self, message: dict, context_id=None, export_timestamp=None):
        self.file.writelines(
            [
                json.dumps(
                    {
                        "message": message,
                        "context_id": context_id,
                        "export_timestamp": export_timestamp,
                    }
                )
            ]
        )

    async def alog(
        self, message: dict, context_id=None, export_timestamp=None
    ):
        # TODO: Imlement actual asyncio usage.
        return self.log(message, context_id, export_timestamp)
