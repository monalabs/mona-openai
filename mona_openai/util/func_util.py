"""
A module with utility (usually higher order) functions for enriching
and extending other functions' functionalities.
"""
from types import MappingProxyType
from random import random
from inspect import iscoroutinefunction

EMPTY_DICT = MappingProxyType({})


async def call_non_blocking_sync_or_async(
    function, func_args=(), func_kwargs=EMPTY_DICT
):
    """
    A higher order function that allows calling both sync and async
    functions as if they were async, avoid blocking when relevant, and
    maintain one code base for both cases.
    """
    if iscoroutinefunction(function):
        return await function(*func_args, **func_kwargs)
    return function(*func_args, **func_kwargs)


def add_conditional_sampling(inner_func, sampling_ratio):
    """
    A higher order function that returns a "sampled" version of the
    given inner function only if needed. This allows for adding
    sampling mechanisms while avoiding conditionals or random number
    creations when either is not necessary.
    """

    async def _sampled_func(*args, **kwargs):
        if random() < sampling_ratio:
            return await inner_func(*args, **kwargs)

    return inner_func if sampling_ratio == 1 else _sampled_func
