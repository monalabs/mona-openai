import time
import logging
from copy import deepcopy
from types import MappingProxyType

from mona_sdk import MonaSingleMessage

from .endpoints.wrapping_getter import get_endpoint_wrapping
from .mona_client import get_mona_clients
from .util.func_util import add_conditional_sampling
from .util.async_util import (
    run_in_an_event_loop,
    call_non_blocking_sync_or_async,
)
from .util.openai_util import get_model_param
from .util.tokens_util import get_usage
from .util.stream_util import ResponseGatheringIterator
from .util.validation_util import validate_and_get_sampling_ratio

EMPTY_DICT = MappingProxyType({})

MONA_ARGS_PREFIX = "MONA_"
CONTEXT_ID_ARG_NAME = MONA_ARGS_PREFIX + "context_id"
EXPORT_TIMESTAMP_ARG_NAME = MONA_ARGS_PREFIX + "export_timestamp"
ADDITIONAL_DATA_ARG_NAME = MONA_ARGS_PREFIX + "additional_data"


def _get_mona_single_message(
    api_name,
    request_input,
    start_time,
    is_exception,
    is_async,
    stream_start_time,
    response,
    analysis_getter,
    context_class,
    message_cleaner,
    additional_data,
    context_id,
    export_timestamp,
):
    """
    Returns a MonaSingleMessage object to be used for data
    exporting to Mona's servers by a Mona client.
    """

    message = {
        "input": request_input,
        "latency": time.time() - start_time,
        "stream_start_latency": stream_start_time - start_time
        if stream_start_time is not None
        else None,
        "is_exception": is_exception,
        "api_name": api_name,
        "is_async": is_async,
    }

    if additional_data:
        message["additional_data"] = additional_data

    if response:
        message["response"] = response
        message["analysis"] = analysis_getter(request_input, response)

    message = message_cleaner(message)

    return MonaSingleMessage(
        message=message,
        contextClass=context_class,
        contextId=context_id,
        exportTimestamp=export_timestamp,
    )


def _init_mona_class(client, context_class_name, openai_endpoint_name):
    response = client.create_openai_context_class(
        context_class_name, openai_endpoint_name
    )
    error_message = response.get("error_message")
    if error_message:
        logging.warning(
            f"Problem initializing Mona context class '{context_class_name}':"
            f" {error_message}"
        )
    else:
        logging.info(
            f"Made sure Mona context class '{context_class_name}' "
            "is initialised"
        )
    return response


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
        mona_creds: Either a dict or pair of Mona API key and secret to
            set up Mona's clients from its SDK
        context_class: The Mona context class name to use for
            monitoring. Use a name of your choice.
        specs: A dictionary of specifications such as monitoring
            sampling ratio.
        mona_clients_getter: Used only for testing purposes
    """
    client, async_client = mona_clients_getter(mona_creds)

    sampling_ratio = validate_and_get_sampling_ratio(specs)

    base_class = get_endpoint_wrapping(
        openai_class.__name__, specs
    ).wrap_class(openai_class)

    _init_mona_class(client, context_class, openai_class.__name__)

    # TODO(itai): Add call to Mona servers to init the context class if it
    #   isn't inited yet once we have the relevant endpoint for this.

    class MonitoredOpenAI(base_class):
        """
        A mona-monitored version of an openai API class.
        """

        @classmethod
        def _get_mona_single_message(
            cls,
            kwargs_param,
            start_time,
            is_exception,
            is_async,
            stream_start_time,
            response,
        ):
            """
            Returns a MonaSingleMessage object to be used for data
            exporting to Mona's servers by a Mona client.
            """
            # Recreate the input dict to avoid manipulating the caller's data,
            # and remove Mona-related data.
            request_input = deepcopy(
                {
                    x: kwargs_param[x]
                    for x in kwargs_param
                    if not x.startswith(MONA_ARGS_PREFIX)
                }
            )

            return _get_mona_single_message(
                api_name=openai_class.__name__,
                request_input=request_input,
                start_time=start_time,
                is_exception=is_exception,
                is_async=is_async,
                stream_start_time=stream_start_time,
                response=response,
                analysis_getter=super()._get_full_analysis,
                context_class=context_class,
                message_cleaner=super()._get_clean_message,
                additional_data=kwargs_param.get(ADDITIONAL_DATA_ARG_NAME),
                context_id=kwargs_param.get(
                    CONTEXT_ID_ARG_NAME, response["id"] if response else None
                ),
                export_timestamp=kwargs_param.get(
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

            is_stream = kwargs.get("stream", False)
            is_async = super_function.__name__ == "acreate"

            response = None

            # will be used only when stream is enabled
            stream_start_time = None

            async def _inner_mona_export(is_exception):
                return await call_non_blocking_sync_or_async(
                    export_function,
                    (
                        cls._get_mona_single_message(
                            kwargs,
                            start_time,
                            is_exception,
                            is_async,
                            stream_start_time,
                            response,
                        ),
                    ),
                )

            mona_export = add_conditional_sampling(
                _inner_mona_export, sampling_ratio
            )

            start_time = time.time()

            async def inner_super_function():
                # Call the actual openai create function without the Mona
                # specific arguments.
                return await call_non_blocking_sync_or_async(
                    super_function,
                    args,
                    {
                        x: kwargs[x]
                        for x in kwargs
                        if not x.startswith(MONA_ARGS_PREFIX)
                    },
                )

            async def inner_handle_exception():
                if not specs.get("avoid_monitoring_exceptions", False):
                    await mona_export(True)

            if not is_stream:
                try:
                    response = await inner_super_function()
                except Exception:
                    await inner_handle_exception()
                    raise

                await mona_export(False)

                return response

            # From here it's stream handling.

            async def _stream_done_callback(
                final_response, actual_stream_start_time
            ):
                nonlocal response
                nonlocal stream_start_time
                # There is no usage data in returned stream responses, so
                # we add it here.
                response = final_response | {
                    "usage": get_usage(
                        model=get_model_param(kwargs),
                        prompt_texts=base_class._get_all_prompt_texts(kwargs),
                        response_texts=base_class._get_all_response_texts(
                            final_response
                        ),
                    )
                }
                stream_start_time = actual_stream_start_time
                await mona_export(False)

            try:
                # Call the actual openai create function without the Mona
                # specific arguments.
                return ResponseGatheringIterator(
                    original_iterator=await inner_super_function(),
                    delta_choice_text_getter=(
                        base_class._get_stream_delta_text_from_choice
                    ),
                    final_choice_getter=base_class._get_final_choice,
                    callback=_stream_done_callback,
                )

            except Exception:
                await inner_handle_exception()
                raise

        @classmethod
        def create(cls, *args, **kwargs):
            """
            A mona-monitored version of the openai base class' "create"
            function.
            """
            return run_in_an_event_loop(
                cls._inner_create(client.export, super().create, args, kwargs)
            )

        @classmethod
        async def acreate(cls, *args, **kwargs):
            """
            An async mona-monitored version of the openai base class'
            "acreate" function.
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


def get_rest_monitor(
    # TODO(itai): Consider understanding endpoint name from complete url.
    openai_endpoint_name,
    mona_creds,
    context_class,
    specs=EMPTY_DICT,
    mona_clients_getter=get_mona_clients,
):
    """
    Returns a client class for monitoring OpenAI REST calls not done
    using the OpenAI python client (e.g., for Azure users using their
    endpoints directly). This isn't a wrapper for any http requesting
    library and doesn't call the OpenAI API for you - it's just an easy
    logging client to log requests, responses and exceptions.
    """

    client, async_client = mona_clients_getter(mona_creds)

    _init_mona_class(client, context_class, openai_endpoint_name)

    sampling_ratio = validate_and_get_sampling_ratio(specs)

    wrapping_logic = get_endpoint_wrapping(openai_endpoint_name, specs)

    class RestClient:
        """
        This will be the returned Mona logging class. We follow
        OpenAI's way of doing things by using a static classe with
        relevant class methods.
        """

        @classmethod
        def _inner_log_request(
            cls,
            mona_export_function,
            request_dict,
            additional_data=None,
            context_id=None,
            export_timestamp=None,
        ):
            """
            Actual logic for logging requests, responses and exceptions.
            """
            start_time = time.time()

            inner_response = None

            def _inner_mona_export(is_exception):
                return mona_export_function(
                    _get_mona_single_message(
                        api_name=openai_endpoint_name,
                        request_input=request_dict,
                        start_time=start_time,
                        is_exception=is_exception,
                        is_async=False,
                        # TODO(itai): Support stream in REST as well.
                        stream_start_time=None,
                        response=inner_response,
                        analysis_getter=wrapping_logic.get_full_analysis,
                        context_class=context_class,
                        message_cleaner=wrapping_logic.get_clean_message,
                        additional_data=additional_data,
                        context_id=context_id,
                        export_timestamp=export_timestamp,
                    )
                )

            mona_export = add_conditional_sampling(
                _inner_mona_export, sampling_ratio
            )

            def log_response(response):
                """
                Only when this function is called, will data be logged
                out to Mona. This function should be called with a
                response object from the OpenAI API as close as
                possible to when it is received to allow accurate
                latency logging.
                """
                nonlocal inner_response
                inner_response = response
                return mona_export(False)

            def log_exception():
                return mona_export(True)

            return log_response, log_exception

        @classmethod
        def log_request(
            cls,
            request_dict,
            additional_data=None,
            context_id=None,
            export_timestamp=None,
        ):
            """
            Sets up mona logging for OpenAI request/response objects.

            This function should be called with a request data dict,
            for example, what you would use as "json" when using
            "requests" to post.

            It returns a response logging function to be used with the
            response object, as well as an exception logging function in case
            of exceptions.

            Note that this call does not log anything to Mona until one of the
            returned callbacks is called.
            """
            return cls._inner_log_request(
                client.export,
                request_dict,
                additional_data,
                context_id,
                export_timestamp,
            )

        @classmethod
        def async_log_request(
            cls,
            request_dict,
            additional_data=None,
            context_id=None,
            export_timestamp=None,
        ):
            """
            Async version of "log_request". See function's docstring for more
            details.
            """
            return cls._inner_log_request(
                async_client.export_async,
                request_dict,
                additional_data,
                context_id,
                export_timestamp,
            )

        @classmethod
        def get_mona_clients(cls):
            """
            Returns the two Mona client this class works with to allow
            exporting more data or communicating directly with Mona's
            API.
            """
            return client, async_client

    return RestClient
