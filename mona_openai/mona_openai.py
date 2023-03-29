import time
import asyncio
from copy import deepcopy
from types import MappingProxyType

from mona_sdk import MonaSingleMessage

from .exceptions import WrongOpenAIClassException
from .mona_client import get_mona_clients
from .util.func_util import (
    add_conditional_sampling,
    call_non_blocking_sync_or_async,
)
from .endpoints.completion import COMPLETION_CLASS_NAME, get_completion_class
from .util.validation_util import validate_and_get_sampling_ratio

EMPTY_DICT = MappingProxyType({})

MONA_ARGS_PREFIX = "MONA_"
CONTEXT_ID_ARG_NAME = MONA_ARGS_PREFIX + "context_id"
EXPORT_TIMESTAMP_ARG_NAME = MONA_ARGS_PREFIX + "export_timestamp"
ADDITIONAL_DATA_ARG_NAME = MONA_ARGS_PREFIX + "additional_data"

# TODO(Itai): This is essetially a nice-looking "switch" statement. We should
#   try to use the name to find the exact monitoring-enrichment function and
#   filename instead of listing all options here.
ENDPOINT_NAME_TO_WRAPPER = {COMPLETION_CLASS_NAME: get_completion_class}


def _get_monitored_base_class(openai_class):
    """
    Returns a class that wrapps the given api class with that
    api-specific functionality.
    """
    class_name = openai_class.__name__

    if class_name not in ENDPOINT_NAME_TO_WRAPPER:
        raise WrongOpenAIClassException("Class not supported: " + class_name)
    return ENDPOINT_NAME_TO_WRAPPER[class_name](openai_class)


# TODO(itai): Consider creating some sturct (as NamedTuple or dataclass) for
#   the specs param.


def monitor(
    openai_class,
    mona_creds,
    context_class,
    specs=EMPTY_DICT,
    mona_clients_getter=get_mona_clients,
):
    """
    Returns a Wrapped version of a given OpenAI class with mona
    monitoring logic.
    This is the main exposed function of the mona_openai package and
    probably the only thing you need to use from this package.

    You can use the returned class' "create" and "acreate" functions
    exactly as you would the original class, and monitoring will be
    taken care of for you.

    This client will automatically monitor for you things like latency,
    prompt and response lengths, number of tokens, etc., along with any
    endpoint parameter usage (e.g., it tracks the "temperature" and
    "max_tokens" params you use).

    You can also add other named args when calling "create" or
    "acreate" by using a new named argument called
    "MONA_additional_data" and set it to any JSON serializable
    dictionary.
    This allows you to add metadata about the call such as a prompt
    template ID, information about the context in which the API call is
    made, etc...

    Furthermore, you can add to create/acreate functions mona specific
    arguments:
        MONA_context_id: The unique id of the context in which the call
            is made. By using this ID you can export more data to Mona
            to the same context from other places. If not used, the
            "id" field of the OpenAI Endpoint's response will be used.
        MONA_export_timestamp: Can be used to simulate as if the
            current call was made in a different time, as far as Mona
            is concerned.

    The returned monitored class also exposes a new class method called
    "get_mona_clients", which allows you to retrieve the clients and
    use them to export more data or communicate directly with Mona's
    API

    Read more about Mona and how to use it in Mona's docs on
    https://docs.monalabs.io.

    Args:
        openai_class: An OpenAI API class to wrap with monitoring
            capabilties.
        mona_creds: A pair of Mona API key and secret to set up Mona's
            clients from its SDK
        context_class: The Mona context class name to use for
            monitoring. Use a name of your choice.
        specs: A dictionary of specifications such as monitoring
            sampling ratio.
        mona_clients_getter: Used only for testing purposes
    """
    client, async_client = mona_clients_getter(mona_creds)

    sampling_ratio = validate_and_get_sampling_ratio(specs)

    base_class = _get_monitored_base_class(openai_class)

    # TODO(itai): Add call to Mona servers to init the context class if it
    #   isn't inited yet once we have the relevant endpoint for this.

    class MonitoredOpenAI(base_class):
        """
        A mona-monitored version of an openai API class.
        """

        @classmethod
        def _get_mona_single_message(
            cls, kwargs_param, start_time, is_exception, is_async, response
        ):
            """
            Returns a MonaSingleMessage object to be used for data
            exporting to Mona's servers by a Mona client.
            """
            # Recreate the input dict to avoid manipulating the caller's data,
            # and remove Mona-related data.
            new_kwargs = deepcopy(
                {
                    x: kwargs_param[x]
                    for x in kwargs_param
                    if not x.startswith(MONA_ARGS_PREFIX)
                }
            )

            message = {
                "input": new_kwargs,
                "latency": time.time() - start_time,
                "is_exception": is_exception,
                "api_name": COMPLETION_CLASS_NAME,
                "is_async": is_async,
            }

            if ADDITIONAL_DATA_ARG_NAME in kwargs_param:
                message["additional_data"] = kwargs_param[
                    ADDITIONAL_DATA_ARG_NAME
                ]

            if response:
                message["response"] = response
                message["analysis"] = super()._get_analysis_params(
                    new_kwargs, response, specs
                )

            message = super()._get_clean_message(message, specs)

            return MonaSingleMessage(
                message=message,
                contextClass=context_class,
                contextId=kwargs_param.get(
                    CONTEXT_ID_ARG_NAME, response["id"] if response else None
                ),
                exportTimestamp=kwargs_param.get(
                    EXPORT_TIMESTAMP_ARG_NAME, start_time
                ),
            )

        @classmethod
        async def _inner_create(
            cls, export_function, super_function, args, kwargs
        ):
            """
            The main logic for wrapping create functions with mona data
            exporting.
            This internal function porovides a template for both sync
            and async activations (helps with wrapping both "create"
            and "acreate").
            """
            start_time = time.time()

            response = None

            async def _inner_mona_export(is_exception):
                await call_non_blocking_sync_or_async(
                    export_function,
                    (
                        cls._get_mona_single_message(
                            kwargs,
                            start_time,
                            is_exception,
                            super_function.__name__ == "acreate",
                            response,
                        ),
                    ),
                )

            mona_export = add_conditional_sampling(
                _inner_mona_export, sampling_ratio
            )

            try:
                # Call the actual openai create function without the Mona
                # specific arguments.
                response = await call_non_blocking_sync_or_async(
                    super_function,
                    args,
                    {
                        x: kwargs[x]
                        for x in kwargs
                        if not x.startswith(MONA_ARGS_PREFIX)
                    },
                )
            except Exception:
                if not specs.get("avoid_monitoring_exceptions", False):
                    await mona_export(True)
                raise

            await mona_export(False)

            response
            return response

        @classmethod
        def create(cls, *args, **kwargs):
            """
            A mona-monitored version of openai.Completion.create.
            """
            return asyncio.run(
                cls._inner_create(client.export, super().create, args, kwargs)
            )

        @classmethod
        async def acreate(cls, *args, **kwargs):
            """
            An async mona-monitored version of openai.Completion.acreate.
            """
            return await cls._inner_create(
                async_client.export_async, super().acreate, args, kwargs
            )

        @classmethod
        def get_mona_clients(cls):
            """
            Returns the two Mona clients this class works with to allow
            exporting more data or communicating directly with Mona's
            API.
            """
            return (client, async_client)

    return type(base_class.__name__, (MonitoredOpenAI,), {})
