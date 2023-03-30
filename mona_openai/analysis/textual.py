"""
A module to derive text-related metrics such as text length, usage of
specific grammatical words, text repetition, etc...

These analyses can be used to detect significant drifts that could be
caused by hallucinations or bugs.

NOTE: There are many more analyses that can be added here.
"""

from ..util.math import get_quotients

PREPOSITIONS = set(
    (
        "aboard",
        "about",
        "above",
        "across",
        "after",
        "against",
        "along",
        "amid",
        "among",
        "around",
        "as",
        "at",
        "before",
        "behind",
        "below",
        "beneath",
        "beside",
        "between",
        "beyond",
        "but",
        "by",
        "concerning",
        "considering",
        "despite",
        "down",
        "during",
        "except",
        "for",
        "from",
        "in",
        "inside",
        "into",
        "like",
        "near",
        "of",
        "off",
        "on",
        "onto",
        "out",
        "outside",
        "over",
        "past",
        "regarding",
        "round",
        "since",
        "through",
        "throughout",
        "till",
        "to",
        "toward",
        "under",
        "underneath",
        "until",
        "unto",
        "up",
        "upon",
        "with",
        "within",
        "without",
    )
)


def _count_prepositions(splitted_text):
    """
    Returns the number of function words in a given text.
    """
    return len([x for x in splitted_text if x in PREPOSITIONS])


def _count_words_not_in_prompt_for_single_answer(
    prompt_words, splitted_answer
):
    return len([word for word in splitted_answer if word not in prompt_words])


def _count_words_not_in_prompt(splitted_prompt, splitted_answers):
    """
    for each answer, returns the number of words it has that do not
    exist in the prompt. High number of such "new" words can be a
    symptom of hallucinations.
    """
    prompt_words = set(splitted_prompt)
    return tuple(
        _count_words_not_in_prompt_for_single_answer(
            prompt_words, splitted_answer
        )
        for splitted_answer in splitted_answers
    )


def get_full_textual_analysis(prompt, answers):
    """
    Provides a dictionary with full textual analyses metrics about the
    prompt, the answers and their relationship.
    """
    splitted_prompt = prompt.split()
    splitted_answers = tuple(answer.split() for answer in answers)

    prompt_preposition_count = _count_prepositions(splitted_prompt)
    answer_preposition_counts = tuple(
        _count_prepositions(splitted_answer)
        for splitted_answer in splitted_answers
    )
    answer_words_counts = tuple(
        len(splitted_answer) for splitted_answer in splitted_answers
    )
    answer_words_not_in_prompt_count = _count_words_not_in_prompt(
        splitted_prompt, splitted_answers
    )

    return {
        "prompt_length": len(prompt),
        "answer_length": tuple(len(answer) for answer in answers),
        "prompt_word_count": len(splitted_prompt),
        "answer_word_count": answer_words_counts,
        "prompt_preposition_count": prompt_preposition_count,
        "prompt_preposition_ratio": prompt_preposition_count
        / len(splitted_prompt)
        if prompt_preposition_count != 0
        else 0,
        "answer_preposition_count": answer_preposition_counts,
        "answer_preposition_ratio": get_quotients(
            answer_preposition_counts, answer_words_counts
        ),
        "answer_words_not_in_prompt_count": answer_words_not_in_prompt_count,
        "answer_words_not_in_prompt_ratio": get_quotients(
            answer_words_not_in_prompt_count, answer_words_counts
        ),
    }
