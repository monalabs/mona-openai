from mona_sdk.client import Client
from mona_sdk.async_client import AsyncClient

from .exceptions import InvalidMonaCredsException


def _raise_not_strings_exception():
    raise InvalidMonaCredsException(
        "Mona API key and secret should both be strings."
    )


def get_mona_clients(creds):
    """
    Returns both a sync and an async mona client for the given
    credentials.

    creds: A tuple containin API key and secret for Mona's API.
    """
    if len(creds) != 2:
        raise InvalidMonaCredsException(
            "There should be exactly two parts to Mona creds. API key and"
            " secret."
        )
    if isinstance(creds[0], str):
        if not isinstance(creds[1], str):
            _raise_not_strings_exception()
        return Client(creds[0], creds[1]), AsyncClient(creds[0], creds[1])

    # For testing purposes, we allow sending the actual (probably fake) clients
    # instead of the creds.
    if not isinstance(creds[0], Client) or not isinstance(
        creds[1], (Client, AsyncClient)
    ):
        _raise_not_strings_exception()
    return creds
