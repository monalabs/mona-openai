class mockCreateExceptionCommand:
    pass


class mockCreateException(Exception):
    pass


def get_mock_openai_class(original_class, create_responses, acreate_responses):
    """
    Unlike the mock mona clients, the class returned from this function
    makes no assertions about the data being sent, only about the
    number of calls.
    """

    class MockCompletion(original_class):
        _create_count = 0
        _acreate_count = 0

        @classmethod
        def _maybe_raise_exception(cls, current_response):
            if isinstance(current_response, mockCreateExceptionCommand):
                raise mockCreateException(
                    "Some mock exception for testing purposes"
                )

        @classmethod
        def _handle_current_response(cls, responses, count):
            current_response = responses[count - 1]
            cls._maybe_raise_exception(current_response)
            return current_response

        @classmethod
        def create(cls, *args, **kwargs):
            cls._create_count += 1
            assert cls._create_count <= len(
                create_responses
            ), "Too many create calls"
            return cls._handle_current_response(
                create_responses, cls._create_count
            )

        @classmethod
        async def acreate(cls, *args, **kwargs):
            cls._acreate_count += 1
            assert cls._acreate_count <= len(
                acreate_responses
            ), "Too many acreate calls"
            return cls._handle_current_response(
                acreate_responses, cls._acreate_count
            )

    return type(original_class.__name__, (MockCompletion,), {})
