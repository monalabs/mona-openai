"""
Utility module for math-related functionality.
"""


class InvalidQuotientssInputError(Exception):
    pass


def get_quotients(iter_1, iter_2):
    """
    For two given iterables of numbers, returns a tuple of the factors
    between each pair of numbers from the two lists.
    """
    iter_1, iter_2 = tuple(iter_1), tuple(iter_2)
    if len(iter_1) != len(iter_2):
        raise InvalidQuotientssInputError()
    return tuple(x / y if y != 0 else None for x, y in zip(iter_1, iter_2))
