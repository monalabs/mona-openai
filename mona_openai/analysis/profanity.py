"""
Logic to create profanity analysis.
"""

from profanity_check import predict_prob, predict

_DECIMAL_PLACES = 2


def get_profanity_prob(texts):
    return tuple(round(x, _DECIMAL_PLACES) for x in predict_prob(texts))


def get_has_profanity(texts):
    return tuple(bool(x) for x in predict(texts))
