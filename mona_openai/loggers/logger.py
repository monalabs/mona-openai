import abc


class Logger(metaclass=abc.ABCMeta):
    """
    An abstract class/interface for logging messages containing OpenAI calls
    analysis data.
    """

    def start_monitoring(self, openai_class_name):
        """
        This function will be called once this logger is used for wrapping
        an OpenAI class.
        Child classes may choose to use this hook in order to run some logic
        preliminary to actual logging.
        """
        pass

    @abc.abstractmethod
    def log(self, message: dict, context_id=None, export_timestamp=None):
        """
        Every child class must implement this basic function which gets a
        dictionary to be logged.

        The interface here allows the logger to get two other parameters:
        - context_id: used to trace different logs related to the same
            context, in logging mechanisms where such a capability is
            relevant.
        - export_timestamp: Used to simulate logging of historical data,
            allowing the caller to specify when the message was created, in
            logging mechanisms where such a capability is relevant.
        """
        pass

    @abc.abstractmethod
    async def alog(
        self, message: dict, context_id=None, export_timestamp=None
    ):
        """
        Child classes should implement this async version of the "log"
        function.
        """
        pass
