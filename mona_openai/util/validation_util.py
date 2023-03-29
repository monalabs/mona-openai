from ..exceptions import (
    WrongOpenAIClassException,
    InvalidSamplingRatioException,
)


def validate_openai_class(openai_class, required_name):
    """
    Validates that the given OpenAI API class' name is the given
    required name.
    """
    class_name = openai_class.__name__
    if class_name != required_name:
        raise WrongOpenAIClassException(
            f"Name is {class_name} and must be {required_name}"
        )


def validate_and_get_sampling_ratio(specs):
    """
    Validates that the sampling ratio in a given specs dict is a valid
    number (between 0 and 1). Returns a default value of 1 if no
    sampling ratio is mentioned.
    """
    sampling_ratio = specs.get("sampling_ratio", 1)
    if sampling_ratio < 0 or sampling_ratio > 1:
        raise InvalidSamplingRatioException(
            f"sampling ratio is {sampling_ratio} but must be a number "
            f"between 0 and 1 (inclusive)"
        )
    return sampling_ratio
