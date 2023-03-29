from mona_sdk.client import Client
from mona_sdk.async_client import AsyncClient

from .exceptions import InvalidMonaCredsException


def _raise_not_strings_exception():
    raise InvalidMonaCredsException(
        "Mona API key and secret should both be strings."
    )

MONA_API_KEY_KEY = "key"
MONA_API_SECRET_KEY = "secret"


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
    if isinstance(creds, dict):
        if MONA_API_KEY_KEY not in creds or MONA_API_SECRET_KEY not in creds:
            raise InvalidMonaCredsException(f"Mona creds dict should hold keys: {MONA_API_KEY_KEY}, {MONA_API_SECRET_KEY}")
        return Client(creds[MONA_API_KEY_KEY], creds[MONA_API_SECRET_KEY]), AsyncClient(creds[MONA_API_KEY_KEY], creds[MONA_API_SECRET_KEY])

    if not isinstance(creds[0], str) or not isinstance(creds[1], str):
        _raise_not_strings_exception()

    return Client(creds[0], creds[1]), AsyncClient(creds[0], creds[1])
