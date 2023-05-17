import abc
from ..util.validation_util import validate_openai_class


class OpenAIEndpointWrappingLogic(metaclass=abc.ABCMeta):
    """
    An abstract class used for wrapping OpenAI endpoints. Each child of this
    class must implement several key logics for wrapping specific OpenAI
    endpoints' logic.

    Note that subclasses are not the actual wrappers of the OpenAI endpoint
    classes, but provide functions to create the actual wrapper classes.
    """

    def __init__(self, specs):
        self._specs = specs
        self._analysis_functions = {
            "privacy": self._get_full_privacy_analysis,
            "textual": self._get_full_textual_analysis,
            "profanity": self._get_full_profainty_analysis,
        }

    def wrap_class(self, openai_class):
        """
        Returns a monitored class wrapping the given openai class, enriching it
        with specific capabilities to be used by an inhereting monitored class.
        """
        validate_openai_class(openai_class, self._get_endpoint_name())

        class MonitoredCompletion(openai_class):
            @classmethod
            def _get_full_analysis(cls, input, response):
                return self.get_full_analysis(input, response)

            @classmethod
            def _get_clean_message(cls, message):
                return self.get_clean_message(message)

        return MonitoredCompletion

    @abc.abstractmethod
    def _get_endpoint_name(self):
        pass

    @abc.abstractmethod
    def get_clean_message(self, message):
        pass

    def get_full_analysis(self, input, response):
        """
        Returns a dict mapping each analysis type to all related analysis
        fields for the given prompt and answers according to the given
        specs (if no "analysis" spec is given - return result for all
        analysis types).

        TODO(itai): Consider propogating the specs to allow the user to
            choose specific anlyses to be made from within each analysis
            category.
        """
        return {
            x: self._analysis_functions[x](input, response)
            for x in self._analysis_functions
            if self._specs.get("analysis", {}).get(x, True)
        }

    @abc.abstractmethod
    def _get_full_privacy_analysis(self, input, response):
        pass

    @abc.abstractmethod
    def _get_full_textual_analysis(self, input, response):
        pass

    @abc.abstractmethod
    def _get_full_profainty_analysis(self, input, response):
        pass
