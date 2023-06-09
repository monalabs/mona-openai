from deepdiff import DeepDiff
from mona_sdk.client import Client


def _get_clean_dict(
    input_dict, keys_to_remove=("latency", "stream_start_latency")
):
    # TODO(itai): While we can't really test latency values, we should try to
    #   add a test for these fields' existence when relevant.
    ret = {x: input_dict[x] for x in input_dict if x not in keys_to_remove}
    for choice in ret.get("response", {"choices": ()})["choices"]:
        # We don't support monitoring this field so no need to test for it.
        choice.pop("logprobs", None)
    return ret


def _assert_message_equality(message_1, message_2):
    print(message_1)
    print(message_2)
    message_1 = _get_clean_dict(message_1)
    message_2 = _get_clean_dict(message_2)
    print(DeepDiff(message_1, message_2))
    assert message_1 == message_2


def _assert_export_num(expected_messages, export_num, last_message):
    assert export_num < len(
        expected_messages
    ), f"export called more than expected. Last message is: {last_message}"


def _get_mock_mona_client(expected_export_messages):
    class MockMonaClient(Client):
        def __init__(self, *args, **kwargs):
            self._export_num = 0

        def create_openai_context_class(self, context_class, openai_api_type):
            return {}

        def export(self, message, filter_none_fields=None):
            _assert_export_num(
                expected_export_messages, self._export_num, message
            )

            expected_mona_message = expected_export_messages[self._export_num]

            _assert_message_equality(
                message.message, expected_mona_message["message"]
            )

            assert (
                message.contextClass == expected_mona_message["context_class"]
            )

            if "context_id" in expected_mona_message:
                assert message.contextId == expected_mona_message["context_id"]

            if "export_timestamp" in expected_mona_message:
                assert (
                    message.exportTimestamp
                    == expected_mona_message["export_timestamp"]
                )

            self._export_num += 1

        # We combine the mock sync and async clients as this property has no
        # relevance in testing.
        async def export_async(self, message, filter_none_fields=None):
            return self.export(message, filter_none_fields)

    return MockMonaClient()


def get_mock_mona_clients_getter(
    expected_export_messages, async_expected_export_messages
):
    """
    Returns a getter function that can be used to get a pair of a mock
    "sync" and a mock "async" Mona clients. The given expected export
    messages in the params will be used to assert that relevant
    exporting is done and not more than that by each mock client.
    """

    def mock_get_mona_client(creds):
        return _get_mock_mona_client(
            expected_export_messages
        ), _get_mock_mona_client(async_expected_export_messages)

    return mock_get_mona_client
