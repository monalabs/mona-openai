"""
The Mona wrapping code for OpenAI's Completion API.
"""
from copy import deepcopy
from functools import wraps

from ..analysis.privacy import get_privacy_analyzers
from ..analysis.profanity import get_profanity_prob, get_has_profanity
from ..analysis.textual import get_textual_analyzers
from .endpoint_wrapping import OpenAIEndpointWrappingLogic

CHAT_COMPLETION_CLASS_NAME = "ChatCompletion"


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


class ChatCompletionWrapping(OpenAIEndpointWrappingLogic):
    def _get_endpoint_name(self):
        return CHAT_COMPLETION_CLASS_NAME

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
        self,
        last_user_message_privacy_analyzer,
        messages_privacy_analyzers,
        answers_privacy_analyzers,
    ):
        ret = {
            "total_prompt_phone_number_count": sum(
                analyzer.get_phone_numbers_count()
                for analyzer in messages_privacy_analyzers
            ),
            "answer_unknown_phone_number_count": tuple(
                answer_analyzer.get_previously_unseen_phone_numbers_count(
                    messages_privacy_analyzers
                )
                for answer_analyzer in answers_privacy_analyzers
            ),
            "total_prompt_email_count": sum(
                analyzer.get_emails_count()
                for analyzer in messages_privacy_analyzers
            ),
            "answer_unkown_email_count": tuple(
                answer_analyzer.get_previously_unseen_emails_count(
                    messages_privacy_analyzers
                )
                for answer_analyzer in answers_privacy_analyzers
            ),
        }
        if last_user_message_privacy_analyzer is not None:
            ret.update(
                {
                    "last_user_message_phone_number_count": last_user_message_privacy_analyzer.get_phone_numbers_count(),
                    "last_user_message_emails_count": last_user_message_privacy_analyzer.get_emails_count(),
                }
            )
        return ret

    @_get_texts
    @_get_analyzers(get_textual_analyzers)
    def _get_full_textual_analysis(
        self,
        last_user_message_textual_analyzer,
        messages_textual_analyzers,
        answers_textual_analyzers,
    ):
        total_prompt_word_count = sum(
            analyzer.get_word_count()
            for analyzer in messages_textual_analyzers
        )
        total_prompt_preposition_count = sum(
            analyzer.get_preposition_count()
            for analyzer in messages_textual_analyzers
        )

        ret = {
            "total_prompt_length": sum(
                analyzer.get_length()
                for analyzer in messages_textual_analyzers
            ),
            "answer_length": tuple(
                analyzer.get_length() for analyzer in answers_textual_analyzers
            ),
            "total_prompt_word_count": total_prompt_word_count,
            "answer_word_count": tuple(
                analyzer.get_word_count()
                for analyzer in answers_textual_analyzers
            ),
            "total_prompt_preposition_count": total_prompt_preposition_count,
            "total_prompt_preposition_ratio": total_prompt_preposition_count
            / total_prompt_word_count
            if total_prompt_word_count != 0
            else None,
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
                    messages_textual_analyzers
                )
                for analyzer in answers_textual_analyzers
            ),
            "answer_words_not_in_prompt_ratio": tuple(
                analyzer.get_words_not_in_others_count(
                    messages_textual_analyzers
                )
                / analyzer.get_word_count()
                for analyzer in answers_textual_analyzers
            ),
        }

        if last_user_message_textual_analyzer != None:
            ret.update(
                {
                    "last_user_message_length": last_user_message_textual_analyzer.get_length(),
                    "last_user_message_word_count": last_user_message_textual_analyzer.get_word_count(),
                    "last_user_message_preposition_count": last_user_message_textual_analyzer.get_preposition_count(),
                    "last_user_message_preposition_ratio": last_user_message_textual_analyzer.get_preposition_ratio(),
                }
            )

        return ret

    @_get_texts
    def _get_full_profainty_analysis(
        self, last_user_message, messages, answers
    ):
        ret = {
            "prompt_profanity_prob": get_profanity_prob(messages),
            "prompt_has_profanity": get_has_profanity(messages),
            "answer_profanity_prob": get_profanity_prob(answers),
            "answer_has_profanity": get_has_profanity(answers),
        }

        if last_user_message is not None:
            ret.update(
                {
                    "last_user_message_profanity_prob": get_profanity_prob(
                        (last_user_message,)
                    )[0],
                    "last_user_message_has_profanity": get_has_profanity(
                        (last_user_message,)
                    )[0],
                }
            )

        return ret
