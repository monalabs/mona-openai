"""
Tests for Completion api Mona wrapping.

NOTE: Many of these tests can be considered more generic than just for
    "Completion", since they test general mona-openai capabilities
    (e.g., sampling ratio, basic flows). We should either keep them
    here (since they do use the "Completion" API after all) or create a
    more generic test module in addition to this one
"""
import asyncio
from copy import deepcopy

import pytest
from openai import Completion

from mona_openai.exceptions import InvalidSamplingRatioException
from mona_openai.mona_openai import (
    CONTEXT_ID_ARG_NAME,
    EXPORT_TIMESTAMP_ARG_NAME,
    monitor,
    get_rest_monitor,
)
from .mocks.mock_openai import (
    mockCreateException,
    mockCreateExceptionCommand,
    get_mock_openai_class,
)
from .mocks.mock_mona_client import get_mock_mona_clients_getter

_DEFAULT_CONTEXT_CLASS = "TEST_CLASS"

_DEFAULT_RESPONSE_TEXT = "\n\nMy name is"

_DEFAULT_RESPONSE_COMMON_VARIABLES = {
    "created": 1679231055,
    "id": "cmpl-6vmzn6DUc2ZNjkyEvAyTf2tAgPl3A",
    "model": "text-ada-001",
    "object": "text_completion",
}

_DEFAULT_RESPONSE = {
    "choices": [
        {
            "finish_reason": "length",
            "index": 0,
            "text": _DEFAULT_RESPONSE_TEXT,
        }
    ],
    "usage": {"completion_tokens": 5, "prompt_tokens": 8, "total_tokens": 13},
} | _DEFAULT_RESPONSE_COMMON_VARIABLES


def _get_response_without_texts(response):
    new_response = deepcopy(response)
    for choice in new_response["choices"]:
        choice.pop("text")
    return new_response


_DEFAULT_EXPORTED_RESPONSE = _get_response_without_texts(_DEFAULT_RESPONSE)

_DEFAULT_INPUT = {
    "prompt": "I want to generate some text about ",
    "model": "text-ada-001",
    "temperature": 0.6,
    "n": 1,
    "max_tokens": 5,
}

# By default we don't export the prompt to Mona
_DEFAULT_EXPORTED_INPUT = {
    x: _DEFAULT_INPUT[x] for x in _DEFAULT_INPUT if x != "prompt"
}

_DEFAULT_ANALYSIS = {
    "privacy": {
        "prompt_phone_number_count": (0,),
        "answer_unknown_phone_number_count": (0,),
        "prompt_email_count": (0,),
        "answer_unknown_email_count": (0,),
    },
    "textual": {
        "prompt_length": (35,),
        "answer_length": (12,),
        "prompt_word_count": (7,),
        "answer_word_count": (3,),
        "prompt_preposition_count": (2,),
        "prompt_preposition_ratio": (0.2857142857142857,),
        "answer_preposition_count": (0,),
        "answer_preposition_ratio": (0.0,),
        "answer_words_not_in_prompt_count": (3,),
        "answer_words_not_in_prompt_ratio": (1.0,),
    },
    "profanity": {
        "prompt_profanity_prob": (0.05,),
        "answer_profanity_prob": (0.05,),
        "prompt_has_profanity": (False,),
        "answer_has_profanity": (False,),
    },
}


def _remove_none_values(dict):
    return {x: y for x, y in dict.items() if y is not None}


def _get_mock_openai_class(*args, **kwargs):
    return get_mock_openai_class(Completion, *args, **kwargs)


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
            "api_name": "Completion",
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


def test_multiple_prompts():
    new_input = deepcopy(_DEFAULT_INPUT)
    new_input["prompt"] = (
        "I want to generate some text about ",
        "I also want to generate some text about ",
    )
    expected_input = deepcopy(new_input)
    expected_input.pop("prompt")

    new_response = deepcopy(_DEFAULT_RESPONSE)
    new_response["choices"] = [
        {
            "finish_reason": "length",
            "index": 0,
            "logprobs": None,
            "text": "\n\nMy name is",
        },
        {
            "finish_reason": "length",
            "index": 1,
            "logprobs": None,
            "text": "\n\nMy thing is",
        },
    ]
    new_expected_response = _get_response_without_texts(new_response)

    new_analysis = {
        "privacy": {
            "prompt_phone_number_count": (0, 0),
            "answer_unknown_phone_number_count": (0, 0),
            "prompt_email_count": (0, 0),
            "answer_unknown_email_count": (0, 0),
        },
        "textual": {
            "prompt_length": (35, 40),
            "answer_length": (12, 13),
            "prompt_word_count": (7, 8),
            "answer_word_count": (3, 3),
            "prompt_preposition_count": (2, 2),
            "prompt_preposition_ratio": (0.2857142857142857, 0.25),
            "answer_preposition_count": (0, 0),
            "answer_preposition_ratio": (0.0, 0.0),
            "answer_words_not_in_prompt_count": (3, 3),
            "answer_words_not_in_prompt_ratio": (1.0, 1.0),
        },
        "profanity": {
            "prompt_profanity_prob": (0.05, 0.05),
            "answer_profanity_prob": (0.05, 0.01),
            "prompt_has_profanity": (False, False),
            "answer_has_profanity": (False, False),
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


def test_rest():
    get_rest_monitor(
        Completion.__name__,
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(),), ()
        ),
    ).log_request(_DEFAULT_INPUT)[0](_DEFAULT_RESPONSE)


def test_rest_more_additional_data():
    additional_data = {"foo": "bar"}
    more_additional_data = {"foo2": "bar2"}
    total_additional_data = {**additional_data, **more_additional_data}
    get_rest_monitor(
        Completion.__name__,
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(additional_data=total_additional_data),), ()
        ),
    ).log_request(_DEFAULT_INPUT, additional_data=additional_data)[0](
        _DEFAULT_RESPONSE, additional_data=more_additional_data
    )


def test_rest_async():
    asyncio.run(
        get_rest_monitor(
            Completion.__name__,
            (),
            _DEFAULT_CONTEXT_CLASS,
            mona_clients_getter=get_mock_mona_clients_getter(
                (), (_get_mona_message(),)
            ),
        ).async_log_request(_DEFAULT_INPUT)[0](_DEFAULT_RESPONSE)
    )


def test_rest_exception():
    get_rest_monitor(
        Completion.__name__,
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


def test_rest_exception_async():
    asyncio.run(
        get_rest_monitor(
            Completion.__name__,
            (),
            _DEFAULT_CONTEXT_CLASS,
            mona_clients_getter=get_mock_mona_clients_getter(
                (),
                (
                    _get_mona_message(
                        is_exception=True, response=None, analysis=None
                    ),
                ),
            ),
        ).async_log_request(_DEFAULT_INPUT)[1]()
    )


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


def test_bad_sampling_ratios():
    with pytest.raises(InvalidSamplingRatioException):
        monitor(
            _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
            (),
            _DEFAULT_CONTEXT_CLASS,
            {"sampling_ratio": 1.1},
            mona_clients_getter=get_mock_mona_clients_getter(
                (_get_mona_message(),), ()
            ),
        )

    with pytest.raises(InvalidSamplingRatioException):
        monitor(
            _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
            (),
            _DEFAULT_CONTEXT_CLASS,
            {"sampling_ratio": -1},
            mona_clients_getter=get_mock_mona_clients_getter(
                (_get_mona_message(),), ()
            ),
        )


def test_async():
    monitored_completion = monitor(
        _get_mock_openai_class((), (_DEFAULT_RESPONSE,)),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (), (_get_mona_message(is_async=True),)
        ),
    )

    asyncio.run(monitored_completion.acreate(**_DEFAULT_INPUT))


def test_exception():
    monitored_completion = monitor(
        _get_mock_openai_class((mockCreateExceptionCommand(),), ()),
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
    )

    with pytest.raises(mockCreateException):
        monitored_completion.create(**_DEFAULT_INPUT)


def test_exception_without_monitoring():
    monitored_completion = monitor(
        _get_mock_openai_class((mockCreateExceptionCommand(),), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        {"avoid_monitoring_exceptions": True},
        mona_clients_getter=get_mock_mona_clients_getter((), ()),
    )

    with pytest.raises(mockCreateException):
        monitored_completion.create(**_DEFAULT_INPUT)


def test_context_id():
    context_id = "some_context_id"
    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(context_id=context_id),), ()
        ),
    ).create(**{**_DEFAULT_INPUT, CONTEXT_ID_ARG_NAME: context_id})


def test_export_timestamp():
    export_timestamp = 1679244447
    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(export_timestamp=export_timestamp),), ()
        ),
    ).create(**{**_DEFAULT_INPUT, EXPORT_TIMESTAMP_ARG_NAME: export_timestamp})


def test_no_profanity():
    expected_analysis = deepcopy(_DEFAULT_ANALYSIS)
    expected_analysis.pop("profanity")
    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        {"analysis": {"profanity": False}},
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(analysis=expected_analysis),), ()
        ),
    ).create(**_DEFAULT_INPUT)


def test_no_textual_or_privacy():
    expected_analysis = deepcopy(_DEFAULT_ANALYSIS)
    expected_analysis.pop("privacy")
    expected_analysis.pop("textual")
    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        {"analysis": {"privacy": False, "textual": False}},
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(analysis=expected_analysis),), ()
        ),
    ).create(**_DEFAULT_INPUT)


def test_multiple_answers():
    new_input = deepcopy(_DEFAULT_INPUT)
    new_input["n"] = 3
    expected_input = deepcopy(new_input)
    expected_input.pop("prompt")

    new_response = deepcopy(_DEFAULT_RESPONSE)
    new_response["choices"] = [
        {
            "finish_reason": "length",
            "index": 0,
            "logprobs": None,
            "text": "\n\nMy name is",
        },
        {
            "finish_reason": "length",
            "index": 1,
            "logprobs": None,
            "text": "\n\nMy thing is",
        },
        {
            "finish_reason": "length",
            "index": 2,
            "logprobs": None,
            "text": "\n\nbladf",
        },
    ]

    new_expected_response = _get_response_without_texts(new_response)

    new_analysis = {
        "privacy": {
            "prompt_phone_number_count": (0,),
            "answer_unknown_phone_number_count": (0, 0, 0),
            "prompt_email_count": (0,),
            "answer_unknown_email_count": (0, 0, 0),
        },
        "textual": {
            "prompt_length": (35,),
            "answer_length": (12, 13, 7),
            "prompt_word_count": (7,),
            "answer_word_count": (3, 3, 1),
            "prompt_preposition_count": (2,),
            "prompt_preposition_ratio": (0.2857142857142857,),
            "answer_preposition_count": (0, 0, 0),
            "answer_preposition_ratio": (0.0, 0.0, 0.0),
            "answer_words_not_in_prompt_count": (3, 3, 1),
            "answer_words_not_in_prompt_ratio": (1.0, 1.0, 1.0),
        },
        "profanity": {
            "prompt_profanity_prob": (0.05,),
            "answer_profanity_prob": (0.05, 0.01, 0.05),
            "prompt_has_profanity": (False,),
            "answer_has_profanity": (False, False, False),
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


def test_additional_data():
    new_input = deepcopy(_DEFAULT_INPUT)
    additional_data = {"foo": "bar", "foo2": 2}
    new_input["MONA_additional_data"] = additional_data

    monitor(
        _get_mock_openai_class((_DEFAULT_RESPONSE,), ()),
        (),
        _DEFAULT_CONTEXT_CLASS,
        mona_clients_getter=get_mock_mona_clients_getter(
            (_get_mona_message(additional_data=additional_data),), ()
        ),
    ).create(**new_input)


def test_stream():
    def response_generator():
        words = _DEFAULT_RESPONSE_TEXT.split(" ")
        last_index = len(words) - 1
        for i, word in enumerate(words):
            choice = {
                "text": (word + " ") if i < last_index else word,
                "index": 0,
                "logprobs": None,
                "finish_reason": None if i < last_index else "length",
            }
            yield _DEFAULT_RESPONSE_COMMON_VARIABLES | {"choices": [choice]}

    input = deepcopy(_DEFAULT_INPUT)
    input["stream"] = True

    expected_input = deepcopy(input)
    expected_input.pop("prompt")

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
                        "text": (word + " ") if i < len(words) - 1 else word,
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
                        "text": (word + " ") if i < len(words) - 1 else word,
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

    expected_input = deepcopy(input)
    expected_input.pop("prompt")

    expected_response = deepcopy(_DEFAULT_EXPORTED_RESPONSE)
    expected_response["choices"] += deepcopy(expected_response["choices"])
    expected_response["choices"][1]["index"] = 1
    expected_response["usage"] = {
        "completion_tokens": 10,
        "prompt_tokens": 8,
        "total_tokens": 18,
    }

    new_analysis = {
        "privacy": {
            "prompt_phone_number_count": (0,),
            "answer_unknown_phone_number_count": (0, 0),
            "prompt_email_count": (0,),
            "answer_unknown_email_count": (0, 0),
        },
        "textual": {
            "prompt_length": (35,),
            "answer_length": (12, 12),
            "prompt_word_count": (7,),
            "answer_word_count": (3, 3),
            "prompt_preposition_count": (2,),
            "prompt_preposition_ratio": (0.2857142857142857,),
            "answer_preposition_count": (0, 0),
            "answer_preposition_ratio": (0.0, 0.0),
            "answer_words_not_in_prompt_count": (3, 3),
            "answer_words_not_in_prompt_ratio": (1.0, 1.0),
        },
        "profanity": {
            "prompt_profanity_prob": (0.05,),
            "answer_profanity_prob": (0.05, 0.05),
            "prompt_has_profanity": (False,),
            "answer_has_profanity": (False, False),
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


def test_stream_async():
    async def response_generator():
        words = _DEFAULT_RESPONSE_TEXT.split(" ")
        for i, word in enumerate(words):
            choice = {
                "text": (word + " ") if i < len(words) - 1 else word,
                "index": 0,
                "logprobs": None,
                "finish_reason": None if i < len(words) - 1 else "length",
            }
            yield _DEFAULT_RESPONSE_COMMON_VARIABLES | {"choices": [choice]}

    input = deepcopy(_DEFAULT_INPUT)
    input["stream"] = True

    expected_input = deepcopy(input)
    expected_input.pop("prompt")

    async def iterate_gen():
        async for _ in await monitor(
            _get_mock_openai_class((), (response_generator(),)),
            (),
            _DEFAULT_CONTEXT_CLASS,
            mona_clients_getter=get_mock_mona_clients_getter(
                (),
                (
                    _get_mona_message(
                        is_stream=True, is_async=True, input=expected_input
                    ),
                ),
            ),
        ).acreate(**input):
            pass

    asyncio.run(iterate_gen())
