from .completion import CompletionWrapping, COMPLETION_CLASS_NAME
from .chat_completion import ChatCompletionWrapping, CHAT_COMPLETION_CLASS_NAME
from ..exceptions import WrongOpenAIClassException

# TODO(Itai): This is essetially a nice-looking "switch" statement. We should
#   try to use the name to find the exact monitoring-enrichment function and
#   filename instead of listing all options here.
ENDPOINT_NAME_TO_WRAPPING = {
    COMPLETION_CLASS_NAME: CompletionWrapping,
    CHAT_COMPLETION_CLASS_NAME: ChatCompletionWrapping,
}


def get_endpoint_wrapping(endpoint_name, specs):
    try:
        return ENDPOINT_NAME_TO_WRAPPING[endpoint_name](specs)
    except KeyError:
        raise WrongOpenAIClassException(
            f"Not a supported class name: {endpoint_name}"
        )
