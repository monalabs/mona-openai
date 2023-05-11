"""
Logic to create profanity analysis.
"""

from profanity_check import predict_prob, predict

_DECIMAL_PLACES = 2


def _get_profanity_prob(texts):
    return tuple(round(x, _DECIMAL_PLACES) for x in predict_prob(texts))


def _get_has_profanity(texts):
    return tuple(bool(x) for x in predict(texts))


def get_full_profainty_analysis(prompt, answers):
    return {
        "prompt_profanity_prob": _get_profanity_prob((prompt,))[0],
        "prompt_has_profanity": _get_has_profanity((prompt,))[0],
        "answer_profanity_prob": _get_profanity_prob(answers),
        "answer_has_profanity": _get_has_profanity(answers),
    }
