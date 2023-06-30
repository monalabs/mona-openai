"""
Tests for ChatCompletion api Mona wrapping.
"""
from copy import deepcopy

from openai import ChatCompletion

from mona_openai.mona_openai import (
    monitor,
    get_rest_monitor,
)
from .mocks.mock_openai import (
    get_mock_openai_class,
)
from .mocks.mock_mona_client import get_mock_mona_clients_getter

_DEFAULT_CONTEXT_CLASS = "TEST_CLASS"

_DEFAULT_RESPONSE_TEXT = "\n\nMy name is"

_DEFAULT_RESPONSE_COMMON_VARIABLES = {
    "created": 1684827250,
    "id": "chatcmpl-7JGp0PUipNwDQeja4P7SwSLa1I19H",
    "model": "gpt-3.5-turbo-0301",
    "object": "chat.completion",
}

_DEFAULT_RESPONSE = {
    "choices": [
        {
            "finish_reason": "length",
            "index": 0,
            "message": {
                "role": "assistant",
                "content": _DEFAULT_RESPONSE_TEXT,
            },
        }
    ],
    "usage": {
        "completion_tokens": 4,
        "prompt_tokens": 8,
        "total_tokens": 12,
    },
} | _DEFAULT_RESPONSE_COMMON_VARIABLES


def _get_response_without_texts(response):
    new_response = deepcopy(response)
    for choice in new_response["choices"]:
        choice["message"].pop("content")
    return new_response


_DEFAULT_EXPORTED_RESPONSE = _get_response_without_texts(_DEFAULT_RESPONSE)

_DEFAULT_INPUT = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "I want to generate some text about "}
    ],
    "max_tokens": 20,
    "n": 1,
    "temperature": 0.2,
}


# By default we don't export the prompt to Mona
def _remove_text_content_from_input(input):
    new_input = deepcopy(input)
    for message in new_input["messages"]:
        message.pop("content", None)

    return new_input


_DEFAULT_EXPORTED_INPUT = _remove_text_content_from_input(_DEFAULT_INPUT)

_DEFAULT_ANALYSIS = {
    "privacy": {
        "total_prompt_phone_number_count": 0,
        "answer_unknown_phone_number_count": (0,),
        "total_prompt_email_count": 0,
        "answer_unknown_email_count": (0,),
        "last_user_message_phone_number_count": 0,
        "last_user_message_emails_count": 0,
    },
    "textual": {
        "total_prompt_length": 35,
        "answer_length": (12,),
        "total_prompt_word_count": 7,
        "answer_word_count": (3,),
        "total_prompt_preposition_count": 2,
        "total_prompt_preposition_ratio": 0.2857142857142857,
        "answer_preposition_count": (0,),
        "answer_preposition_ratio": (0,),
        "answer_words_not_in_prompt_count": (3,),
        "answer_words_not_in_prompt_ratio": (1,),
        "last_user_message_length": 35,
        "last_user_message_word_count": 7,
        "last_user_message_preposition_count": 2,
        "last_user_message_preposition_ratio": 0.2857142857142857,
    },
    "profanity": {
        "prompt_profanity_prob": (0.05,),
        "prompt_has_profanity": (False,),
        "answer_profanity_prob": (0.05,),
        "answer_has_profanity": (False,),
        "last_user_message_profanity_prob": 0.05,
        "last_user_message_has_profanity": False,
    },
}


def _remove_none_values(dict):
    return {x: y for x, y in dict.items() if y is not None}


def _get_mock_openai_class(*args, **kwargs):
    return get_mock_openai_class(ChatCompletion, *args, **kwargs)


def _get_mona_message(
    input=_DEFAULT_EXPORTED_INPUT,
    is_exception=False,
    is_async=False,
    is_stream=None,
    response=_DEFAULT_EXPORTED_RESPONSE,
    analysis=_DEFAULT_ANALYSIS,
    context_class=_DEFAULT_CONTEXT_CLASS,
    context_id=None,
    export_timestamp=None,
    additional_data=None,
):
    message = {
        "message": {
            "input": input,
            "is_exception": is_exception,
            "api_name": "ChatCompletion",
            "is_async": is_async,
            "response": response,
            "analysis": analysis,
            "additional_data": additional_data,
        },
        "context_class": context_class,
        "context_id": context_id,
        "export_timestamp": export_timestamp,
    }

    message["message"] = _remove_none_values(message["message"])
    return _remove_none_values(message)


def test_basic():
    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(),), ()
        ),
    ).create(**_DEFAULT_INPUT)


def test_multiple_messages_not_ending_with_user_message():
    new_input = deepcopy(_DEFAULT_INPUT)
    new_input["messages"] = (
        [{"role": "system", "content": "you are an assistant"}]
        + new_input["messages"]
        + [{"role": "assistant", "content": "some initial answer"}]
    )

    expected_input = _remove_text_content_from_input(new_input)

    new_analysis = {
        "privacy": {
            "total_prompt_phone_number_count": 0,
            "answer_unknown_phone_number_count": (0,),
            "total_prompt_email_count": 0,
            "answer_unknown_email_count": (0,),
        },
        "textual": {
            "total_prompt_length": 74,
            "answer_length": (12,),
            "total_prompt_word_count": 14,
            "answer_word_count": (3,),
            "total_prompt_preposition_count": 2,
            "total_prompt_preposition_ratio": 0.14285714285714285,
            "answer_preposition_count": (0,),
            "answer_preposition_ratio": (0,),
            "answer_words_not_in_prompt_count": (3,),
            "answer_words_not_in_prompt_ratio": (1,),
        },
        "profanity": {
            "prompt_profanity_prob": (0.05, 0.05, 0.02),
            "prompt_has_profanity": (False, False, False),
            "answer_profanity_prob": (0.05,),
            "answer_has_profanity": (False,),
        },
    }

    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (
                _get_mona_message(
                    input=expected_input,
                    analysis=new_analysis,
                ),
            ),
            (),
        ),
    ).create(**new_input)


def test_multiple_messages():
    new_input = deepcopy(_DEFAULT_INPUT)
    new_input["messages"] = (
        [{"role": "system", "content": "you are an assistant"}]
        + new_input["messages"]
        + [
            {"role": "assistant", "content": "some initial answer"},
            {"role": "user", "content": "some user new prompt"},
        ]
    )

    expected_input = _remove_text_content_from_input(new_input)

    new_analysis = {
        "privacy": {
            "total_prompt_phone_number_count": 0,
            "answer_unknown_phone_number_count": (0,),
            "total_prompt_email_count": 0,
            "answer_unknown_email_count": (0,),
            "last_user_message_phone_number_count": 0,
            "last_user_message_emails_count": 0,
        },
        "textual": {
            "total_prompt_length": 94,
            "answer_length": (12,),
            "total_prompt_word_count": 18,
            "answer_word_count": (3,),
            "total_prompt_preposition_count": 2,
            "total_prompt_preposition_ratio": 0.1111111111111111,
            "answer_preposition_count": (0,),
            "answer_preposition_ratio": (0,),
            "answer_words_not_in_prompt_count": (3,),
            "answer_words_not_in_prompt_ratio": (1,),
            "last_user_message_length": 20,
            "last_user_message_word_count": 4,
            "last_user_message_preposition_count": 0,
            "last_user_message_preposition_ratio": 0,
        },
        "profanity": {
            "prompt_profanity_prob": (0.05, 0.05, 0.02, 0.03),
            "prompt_has_profanity": (False, False, False, False),
            "answer_profanity_prob": (0.05,),
            "answer_has_profanity": (False,),
            "last_user_message_profanity_prob": 0.03,
            "last_user_message_has_profanity": False,
        },
    }

    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (
                _get_mona_message(
                    input=expected_input,
                    analysis=new_analysis,
                ),
            ),
            (),
        ),
    ).create(**new_input)


def test_rest():
    get_rest_monitor(
        ChatCompletion.__name__,
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(),), ()
        ),
    ).log_request(_DEFAULT_INPUT)[0](_DEFAULT_RESPONSE)


def test_rest_exception():
    get_rest_monitor(
        ChatCompletion.__name__,
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (
                _get_mona_message(
                    is_exception=True, response=None, analysis=None
                ),
            ),
            (),
        ),
    ).log_request(_DEFAULT_INPUT)[1]()


def test_export_response_text():
    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        {"export_response_texts": True},
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(response=_DEFAULT_RESPONSE),), ()
        ),
    ).create(**_DEFAULT_INPUT)


def test_export_prompt():
    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        {"export_prompt": True},
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(input=_DEFAULT_INPUT),), ()
        ),
    ).create(**_DEFAULT_INPUT)


def test_multiple_answers():
    new_input = deepcopy(_DEFAULT_INPUT)
    new_input["n"] = 3
    expected_input = _remove_text_content_from_input(new_input)

    new_response = deepcopy(_DEFAULT_RESPONSE)
    new_response["choices"] = [
        {
            "finish_reason": "length",
            "index": 0,
            "logprobs": None,
            "message": {
                "role": "assistant",
                "content": "\n\nMy name is",
            },
        },
        {
            "finish_reason": "length",
            "index": 1,
            "logprobs": None,
            "message": {
                "role": "assistant",
                "content": "\n\nMy thing is",
            },
        },
        {
            "finish_reason": "length",
            "index": 2,
            "logprobs": None,
            "message": {
                "role": "assistant",
                "content": "\n\nbladf",
            },
        },
    ]

    new_expected_response = _get_response_without_texts(new_response)

    new_analysis = {
        "privacy": {
            "total_prompt_phone_number_count": 0,
            "answer_unknown_phone_number_count": (0, 0, 0),
            "total_prompt_email_count": 0,
            "answer_unknown_email_count": (0, 0, 0),
            "last_user_message_phone_number_count": 0,
            "last_user_message_emails_count": 0,
        },
        "textual": {
            "total_prompt_length": 35,
            "answer_length": (12, 13, 7),
            "total_prompt_word_count": 7,
            "answer_word_count": (3, 3, 1),
            "total_prompt_preposition_count": 2,
            "total_prompt_preposition_ratio": 0.2857142857142857,
            "answer_preposition_count": (0, 0, 0),
            "answer_preposition_ratio": (0, 0, 0),
            "answer_words_not_in_prompt_count": (3, 3, 1),
            "answer_words_not_in_prompt_ratio": (1.0, 1.0, 1.0),
            "last_user_message_length": 35,
            "last_user_message_word_count": 7,
            "last_user_message_preposition_count": 2,
            "last_user_message_preposition_ratio": 0.2857142857142857,
        },
        "profanity": {
            "prompt_profanity_prob": (0.05,),
            "prompt_has_profanity": (False,),
            "answer_profanity_prob": (0.05, 0.01, 0.05),
            "answer_has_profanity": (False, False, False),
            "last_user_message_profanity_prob": 0.05,
            "last_user_message_has_profanity": False,
        },
    }

    monitor(
        _get_mock_openai_class((new_response,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (
                _get_mona_message(
                    response=new_expected_response,
                    input=expected_input,
                    analysis=new_analysis,
                ),
            ),
            (),
        ),
    ).create(**new_input)


def test_stream():
    def response_generator():
        words = _DEFAULT_RESPONSE_TEXT.split(" ")
        last_index = len(words) - 1
        for i, word in enumerate(words):
            choice = {
                "delta": {"content": (word + " ") if i < last_index else word},
                "index": 0,
                "logprobs": None,
                "finish_reason": None if i < last_index else "length",
            }
            yield _DEFAULT_RESPONSE_COMMON_VARIABLES | {"choices": [choice]}

    input = deepcopy(_DEFAULT_INPUT)
    input["stream"] = True

    expected_input = _remove_text_content_from_input(input)

    for _ in monitor(
        _get_mock_openai_class((response_generator(),), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(is_stream=True, input=expected_input),), ()
        ),
    ).create(**input):
        pass


def test_stream_multiple_answers():
    def response_generator():
        words = _DEFAULT_RESPONSE_TEXT.split(" ")
        for i, word in enumerate(words):
            yield _DEFAULT_RESPONSE_COMMON_VARIABLES | {
                "choices": [
                    {
                        "delta": {
                            "content": (word + " ")
                            if i < len(words) - 1
                            else word
                        },
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": None
                        if i < len(words) - 1
                        else "length",
                    }
                ]
            }
            yield _DEFAULT_RESPONSE_COMMON_VARIABLES | {
                "choices": [
                    {
                        "delta": {
                            "content": (word + " ")
                            if i < len(words) - 1
                            else word
                        },
                        "index": 1,
                        "logprobs": None,
                        "finish_reason": None
                        if i < len(words) - 1
                        else "length",
                    }
                ]
            }

    input = deepcopy(_DEFAULT_INPUT)
    input["stream"] = True
    input["n"] = 2

    expected_input = _remove_text_content_from_input(input)

    expected_response = deepcopy(_DEFAULT_EXPORTED_RESPONSE)
    expected_response["choices"] += deepcopy(expected_response["choices"])
    expected_response["choices"][1]["index"] = 1
    expected_response["usage"] = {
        "completion_tokens": 8,
        "prompt_tokens": 8,
        "total_tokens": 16,
    }

    new_analysis = {
        "privacy": {
            "total_prompt_phone_number_count": 0,
            "answer_unknown_phone_number_count": (0, 0),
            "total_prompt_email_count": 0,
            "answer_unknown_email_count": (0, 0),
            "last_user_message_phone_number_count": 0,
            "last_user_message_emails_count": 0,
        },
        "textual": {
            "total_prompt_length": 35,
            "answer_length": (12, 12),
            "total_prompt_word_count": 7,
            "answer_word_count": (3, 3),
            "total_prompt_preposition_count": 2,
            "total_prompt_preposition_ratio": 0.2857142857142857,
            "answer_preposition_count": (0, 0),
            "answer_preposition_ratio": (0, 0),
            "answer_words_not_in_prompt_count": (3, 3),
            "answer_words_not_in_prompt_ratio": (1.0, 1.0),
            "last_user_message_length": 35,
            "last_user_message_word_count": 7,
            "last_user_message_preposition_count": 2,
            "last_user_message_preposition_ratio": 0.2857142857142857,
        },
        "profanity": {
            "prompt_profanity_prob": (0.05,),
            "prompt_has_profanity": (False,),
            "answer_profanity_prob": (0.05, 0.05),
            "answer_has_profanity": (False, False),
            "last_user_message_profanity_prob": 0.05,
            "last_user_message_has_profanity": False,
        },
    }

    for _ in monitor(
        _get_mock_openai_class((response_generator(),), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (
                _get_mona_message(
                    is_stream=True,
                    input=expected_input,
                    response=expected_response,
                    analysis=new_analysis,
                ),
            ),
            (),
        ),
    ).create(**input):
        pass
