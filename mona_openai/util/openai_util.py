"""
Util logic for OpenAI related logic and language (e.g., dealing with API
parameter names).
"""


def get_model_param(request):
    """
    Returns the "model" param in the request, the "engine" param if no
    "model" param is used, and None if neither exists (which isn't expected
    to happen)
    """
    return request.get("model", request.get("engine"))
