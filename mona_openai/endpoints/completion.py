"""
The Mona wrapping code for OpenAI's Completion API.
"""
from copy import deepcopy
from functools import wraps

from ..analysis.privacy import get_privacy_analyzers
from ..analysis.profanity import get_profanity_prob, get_has_profanity
from ..analysis.textual import get_textual_analyzers
from .endpoint_wrapping import OpenAIEndpointWrappingLogic

COMPLETION_CLASS_NAME = "Completion"


def _get_choices_texts(response):
    return tuple((choice["text"] for choice in response["choices"]))


def _get_texts(func):
    def wrapper(self, input, response):
        return func(self, input["prompt"], _get_choices_texts(response))

    return wrapper


def _get_analyzers(analyzers_getter):
    def decorator(func):
        @wraps(func)
        def wrapper(self, prompt, answers):
            return func(
                self, analyzers_getter((prompt,))[0], analyzers_getter(answers)
            )

        return wrapper

    return decorator


class CompletionWrapping(OpenAIEndpointWrappingLogic):
    def _get_endpoint_name(self):
        return COMPLETION_CLASS_NAME

    def get_clean_message(self, message):
        """
        Returns a copy of the given message with relevant data removed, for
        example the actual texts, to avoid sending such information, that
        is sometimes sensitive, to Mona.
        """
        new_message = deepcopy(message)
        if not self._specs.get("export_prompt", False):
            new_message["input"].pop("prompt")

        if "response" in message and not self._specs.get(
            "export_response_texts", False
        ):
            for choice in new_message["response"]["choices"]:
                choice.pop("text")

        return new_message

    @_get_texts
    @_get_analyzers(get_privacy_analyzers)
    def _get_full_privacy_analysis(
        self, prompt_privacy_analyzer, answers_privacy_analyzers
    ):
        return {
            "prompt_phone_number_count": prompt_privacy_analyzer.get_phone_numbers_count(),
            "answer_unknown_phone_number_count": tuple(
                answer_analyzer.get_previously_unseen_phone_numbers_count(
                    (prompt_privacy_analyzer,)
                )
                for answer_analyzer in answers_privacy_analyzers
            ),
            "prompt_email_count": prompt_privacy_analyzer.get_emails_count(),
            "answer_unkown_email_count": tuple(
                answer_analyzer.get_previously_unseen_emails_count(
                    (prompt_privacy_analyzer,)
                )
                for answer_analyzer in answers_privacy_analyzers
            ),
        }

    @_get_texts
    @_get_analyzers(get_textual_analyzers)
    def _get_full_textual_analysis(
        self, prompt_textual_analyzer, answers_textual_analyzers
    ):
        return {
            "prompt_length": prompt_textual_analyzer.get_length(),
            "answer_length": tuple(
                analyzer.get_length() for analyzer in answers_textual_analyzers
            ),
            "prompt_word_count": prompt_textual_analyzer.get_word_count(),
            "answer_word_count": tuple(
                analyzer.get_word_count()
                for analyzer in answers_textual_analyzers
            ),
            "prompt_preposition_count": prompt_textual_analyzer.get_preposition_count(),
            "prompt_preposition_ratio": prompt_textual_analyzer.get_preposition_ratio(),
            "answer_preposition_count": tuple(
                analyzer.get_preposition_count()
                for analyzer in answers_textual_analyzers
            ),
            "answer_preposition_ratio": tuple(
                analyzer.get_preposition_ratio()
                for analyzer in answers_textual_analyzers
            ),
            "answer_words_not_in_prompt_count": tuple(
                analyzer.get_words_not_in_others_count(
                    (prompt_textual_analyzer,)
                )
                for analyzer in answers_textual_analyzers
            ),
            "answer_words_not_in_prompt_ratio": tuple(
                analyzer.get_words_not_in_others_count(
                    (prompt_textual_analyzer,)
                )
                / analyzer.get_word_count()
                for analyzer in answers_textual_analyzers
            ),
        }

    @_get_texts
    def _get_full_profainty_analysis(self, prompt, answers):
        return {
            "prompt_profanity_prob": get_profanity_prob((prompt,))[0],
            "prompt_has_profanity": get_has_profanity((prompt,))[0],
            "answer_profanity_prob": get_profanity_prob(answers),
            "answer_has_profanity": get_has_profanity(answers),
        }
