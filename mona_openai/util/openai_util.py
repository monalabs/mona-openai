"""
Util logic for OpenAI related logic and language (e.g., dealing with API parameter names).
"""

def get_model_param(request):
    """
    Returns the model or engine param (one of them must be there)
    """
    return request.get("model", request.get("engine"))
