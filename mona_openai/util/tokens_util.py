"""
A utility module for everything realted to encoding tokens.
"""
import tiktoken


def _get_number_of_tokens(text, enc):
    return len(enc.encode(text))


def _get_encoding(model):
    return tiktoken.encoding_for_model(model)


def get_usage(model, prompt_texts, response_texts):
    """
    Returns a usage dict containing the number of tokens in the prompt, in the
    response, and totally.
    """
    enc = _get_encoding(model)

    def get_tokens_sum(texts):
        return sum(_get_number_of_tokens(text, enc) for text in texts)

    usage = {
        "prompt_tokens": get_tokens_sum(prompt_texts),
        "completion_tokens": get_tokens_sum(response_texts),
    }
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

    return usage
