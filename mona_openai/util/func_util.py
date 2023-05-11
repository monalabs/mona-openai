"""
A module with utility (usually higher order) functions for enriching
and extending other functions' functionalities.
"""
from random import random


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
