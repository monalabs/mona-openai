"""
A util module for everything related to supporting streams.
"""
import time
from .async_util import run_in_an_event_loop
import inspect


class ResponseGatheringIterator:
    """
    A generator class that takes an original OpenAI stream response generator
    and wraps it with functionality to gather all the stream of responses as
    they come, and create from them a singular reponse object as would have
    been received in non-stream OpenAI usage.

    Once the original generator is done it creates the full response and calls
    a callback with it.

    It acts both as sync and async generator to ease the use of sync/async
    joint code.
    """

    def __init__(
        self,
        delta_choice_text_getter,
        final_choice_getter,
        original_iterator,
        callback,
    ):
        self._original_iterator = original_iterator
        self._delta_choice_text_getter = delta_choice_text_getter
        self._final_choice_getter = final_choice_getter
        self._callback = callback
        self._initial_event_recieved_time = None
        self._common_response_information = None
        self._choices = {}

    def __iter__(self):
        return self

    def __aiter__(self):
        return self

    def __next__(self):
        try:
            return self._add_response(self._original_iterator.__next__())
        except StopIteration:
            self._call_callback()
            raise

    async def __anext__(self):
        try:
            return self._add_response(
                await self._original_iterator.__anext__()
            )
        except StopAsyncIteration:
            await self._a_call_callback()
            raise

    def _add_response(self, event):
        """
        The main and only exposed function of the ResponseGatherer class. Use
        this function to collect stream events.
        """
        if self._initial_event_recieved_time is None:
            self._initial_event_recieved_time = time.time()
            self._common_response_information = {
                x: event[x] for x in event if x != "choices"
            }

        # Gather response events by choice index.
        self._handle_choice(self._get_only_choice(event))
        return event

    def _call_callback(self):
        # We allow an async function as the callback event if this class is
        # used as a sync generator. This code handles this scenario.
        callback_args = (
            self._create_singular_response(),
            self._initial_event_recieved_time,
        )
        if inspect.iscoroutinefunction(self._callback):
            run_in_an_event_loop(self._callback(*callback_args))
            return

        self._callback(*callback_args)

    async def _a_call_callback(self):
        await self._callback(
            self._create_singular_response(),
            self._initial_event_recieved_time,
        )

    def _handle_choice(self, choice):
        index = choice["index"]
        self._choices[index] = self._choices.get(index, []) + [choice]

    def _get_only_choice(self, event):
        # Stream response events have only a single choice that specifies
        # its own index.
        return event["choices"][0]

    def _create_singular_response(self):
        choices = [
            self._get_full_choice(choice) for choice in self._choices.values()
        ]
        return self._common_response_information | {"choices": choices}

    def _get_full_choice(self, choice):
        full_text = "".join(
            self._delta_choice_text_getter(choice_event)
            for choice_event in choice
        )

        return {
            **self._final_choice_getter(full_text),
            "index": choice[0]["index"],
            "finish_reason": choice[-1]["finish_reason"],
        }
