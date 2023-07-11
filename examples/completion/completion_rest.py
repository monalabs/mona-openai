from os import environ
import requests
from mona_openai import get_rest_monitor
import openai

openai.api_key = environ.get("OPEN_AI_KEY")

MONA_API_KEY = environ.get("MONA_API_KEY")
MONA_SECRET = environ.get("MONA_SECRET")
MONA_CREDS = {
    "key": MONA_API_KEY,
    "secret": MONA_SECRET,
}

# This is the name of the monitoring class on Mona
CONTEXT_CLASS_NAME = "MONITORED_COMPLETION_USE_CASE_NAME"


# Direct REST usage, without OpenAI client

# Get Mona logger
mona_logger = get_rest_monitor(
    "Completion",
    MONA_CREDS,
    CONTEXT_CLASS_NAME,
)

# Set up the API endpoint URL and authentication headers
url = "https://api.openai.com/v1/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {environ.get('OPEN_AI_KEY')}",
}

# Set up the request data
data = {
    "prompt": "I want to generate some text about ",
    "max_tokens": 20,
    "temperature": 0.2,
    "model": "text-ada-001",
    "n": 1,
}

# The log_request function returns two other function for later logging
# the response or the exception. When we later do that, the logger will
# actually calculate all the relevant metrics and will send them to
# Mona.
response_logger, exception_logger = mona_logger.log_request(
    data, additional_data={"customer_id": "A531251"}
)

try:
    # Send the request to the API
    response = requests.post(url, headers=headers, json=data)

    # Check for HTTP errors
    response.raise_for_status()

    # Log response to Mona
    response_logger(response.json(), additional_data={"some_other_data": True})
    print(response.json()["choices"][0]["text"])

except Exception:
    # Log exception to Mona
    exception_logger()
