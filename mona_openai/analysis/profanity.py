"""
Logic to create profanity analysis.
"""

from profanity_check import predict_prob


def _get_profanity_prob(texts):
    return tuple(round(x, 2) for x in predict_prob(texts))


def get_full_profainty_analysis(prompt, answers):
    return {
        "prompt_profanity_prob": _get_profanity_prob((prompt,))[0],
        "answer_profanity_prob": _get_profanity_prob(answers),
    }
