"""
Utility module for math-related functionality.
"""


def get_factors(iter_1, iter_2):
    """
    For two given iterables of numbers, returns a tuple of the factors
    between each pair of numbers from the two lists.
    """
    return tuple(x / y for x, y in zip(iter_1, iter_2))
