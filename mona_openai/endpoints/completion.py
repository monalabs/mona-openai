"""
The Mona wrapping code for OpenAI's Completion API.
"""
from copy import deepcopy

from ..analysis.analysis import get_full_analysis
from ..util.validation_util import validate_openai_class

COMPLETION_CLASS_NAME = "Completion"


def get_completion_class(openai_class):
    """
    Returns a monitored class wrapping the given openai class, which is
    expected to be a "openai.Completion" class, enriching it with
    specific capabilities to be used by an inhereting monitored class.
    """
    validate_openai_class(openai_class, COMPLETION_CLASS_NAME)

    class MonitoredCompletion(openai_class):
        @classmethod
        def _get_analysis_params(cls, input, response, specs):
            return get_full_analysis(
                prompt=input["prompt"],
                answers=tuple(choice["text"] for choice in response["choices"]),
                specs=specs,
            )

        @classmethod
        def _get_clean_message(cls, message, specs):
            new_message = deepcopy(message)
            if not specs.get("export_prompt", False):
                new_message["input"].pop("prompt")

            if "response" in message and not specs.get(
                "export_response_texts", False
            ):
                for choice in new_message["response"]["choices"]:
                    choice.pop("text")

            return new_message

    return MonitoredCompletion
