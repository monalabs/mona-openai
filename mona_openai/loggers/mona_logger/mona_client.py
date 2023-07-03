from mona_sdk.client import Client
from mona_sdk.async_client import AsyncClient

from ...exceptions import InvalidMonaCredsException


MONA_API_KEY_KEY = "key"
MONA_API_SECRET_KEY = "secret"


def get_mona_clients(creds):
    """
    Returns both a sync and an async mona client for the given
    credentials.

    creds: Either a tuple or a dict containing API key and secret for
        Mona's API.
    """
    if len(creds) != 2:
        raise InvalidMonaCredsException(
            "There should be exactly two parts to Mona creds. API key and"
            " secret."
        )

    # Creds could be in a dict.
    if isinstance(creds, dict):
        if MONA_API_KEY_KEY not in creds or MONA_API_SECRET_KEY not in creds:
            raise InvalidMonaCredsException(
                f"Mona creds dict should hold keys:"
                f"{MONA_API_KEY_KEY}, {MONA_API_SECRET_KEY}"
            )
        return Client(
            creds[MONA_API_KEY_KEY], creds[MONA_API_SECRET_KEY]
        ), AsyncClient(creds[MONA_API_KEY_KEY], creds[MONA_API_SECRET_KEY])

    # If creds are not in a dict, they are in a tuple (pair).
    if not isinstance(creds[0], str) or not isinstance(creds[1], str):
        raise InvalidMonaCredsException(
            "Mona API key and secret should both be strings."
        )

    return Client(creds[0], creds[1]), AsyncClient(creds[0], creds[1])
