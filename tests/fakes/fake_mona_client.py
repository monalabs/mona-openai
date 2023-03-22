from deepdiff import DeepDiff
from mona_sdk.client import Client


def _copy_dict_without_latency(input_dict):
    return {x: input_dict[x] for x in input_dict if x != "latency"}


def _assert_message_equality(message_1, message_2):
    print(DeepDiff(message_1, message_2))
    assert _copy_dict_without_latency(message_1) == _copy_dict_without_latency(
        message_2
    )


def _assert_export_num(expected_export_messages, client, message):
    assert client._export_num < len(
        expected_export_messages
    ), f"export called more than expected. Last message is: {message}"


def get_fake_mona_client(expected_export_messages):
    class FakeMonaClient(Client):
        def __init__(self, *args, **kwargs):
            self._export_num = 0

        def export(self, message, filter_none_fields=None):
            _assert_export_num(expected_export_messages, self, message)

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

        # We combine the fake sync and async clients as this property has no
        # relevance in testing.
        async def export_async(self, message, filter_none_fields=None):
            return self.export(message, filter_none_fields)

    return FakeMonaClient()
