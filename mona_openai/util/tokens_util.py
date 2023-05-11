"""
A utility module for everything realted to encoding tokens.
"""
import tiktoken


def _get_number_of_tokens(text, enc):
    return len(enc.encode(text))


def get_usage(request, response):
    """
    Returns a usage dict containing the number of tokens in the prompt, in the
    response, and totally.
    """
    enc = tiktoken.encoding_for_model(
        request.get("model", request.get("engine"))
    )
    usage = {
        "prompt_tokens": _get_number_of_tokens(request["prompt"], enc),
        "completion_tokens": sum(
            _get_number_of_tokens(choice["text"], enc)
            for choice in response["choices"]
        ),
    }
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    return usage
