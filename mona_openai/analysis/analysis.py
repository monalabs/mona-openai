"""
A module to gather analysis metrics from given prompts and and answers.

NOTE: It remains to be seen if the functionality here should be
    further refactored to better fit more endpoints besides
    "Completion".

TODO(itai): Add more analysis categories.
"""

from .privacy import get_full_privacy_analysis
from .textual import get_full_textual_analysis
from .profanity import get_full_profainty_analysis

ANALYSIS_TYPES_TO_FUNCTION = {
    "privacy": get_full_privacy_analysis,
    "textual": get_full_textual_analysis,
    "profanity": get_full_profainty_analysis,
}


def get_full_analysis(prompt, answers, specs):
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
        x: ANALYSIS_TYPES_TO_FUNCTION[x](prompt, answers)
        for x in ANALYSIS_TYPES_TO_FUNCTION
        if specs.get("analysis", {}).get(x, True)
    }
