import asyncio
from types import MappingProxyType
from inspect import iscoroutinefunction


def run_in_an_event_loop(coroutine):
    """
    A light wrapper around asyncio.run to avoid crushing when trying to run a
    coroutine in an environment where an event loop is already in place and
    asyncio.run doesn't work.
    """
    try:
        return asyncio.run(coroutine)
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(coroutine)


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
