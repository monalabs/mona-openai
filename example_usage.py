from os import environ
import requests
from mona_openai import get_rest_monitor
import asyncio
import openai

from mona_openai import monitor

openai.api_key = environ.get("OPEN_AI_KEY")

MONA_API_KEY = environ.get("MONA_API_KEY")
MONA_SECRET = environ.get("MONA_SECRET")
MONA_CREDS = {
    "key": MONA_API_KEY,
    "secret": MONA_SECRET,
}
COMPLETION_CONTEXT_CLASS_NAME = "MY_COMPLETION_USAGE"
CHAT_COMPLETION_CONTEXT_CLASS_NAME = "MY_CHAT_USAGE"


monitored_completion = monitor(
    openai.Completion,
    MONA_CREDS,
    COMPLETION_CONTEXT_CLASS_NAME,
)

monitored_chat_completion = monitor(
    openai.ChatCompletion, MONA_CREDS, CHAT_COMPLETION_CONTEXT_CLASS_NAME
)

response = monitored_chat_completion.create(
    messages=[{"role": "user", "content": ""}],
    model="gpt-3.5-turbo",
    max_tokens=100,
    n=1,
    temperature=0.3,
)

print(response.choices[0].message.content)

prompt = "I want to generate some text about "
model = "text-ada-001"
temperature = 0.6
max_tokens = 5
n = 1

# Regular (sync) usage
response = monitored_completion.create(
    engine=model,
    prompt=prompt,
    max_tokens=max_tokens,
    n=n,
    temperature=temperature,
    MONA_additional_data={"customer_id": "A531251"},
)
print(response.choices[0].text)

# Async usage
response = asyncio.run(
    monitored_completion.acreate(
        engine=model,
        prompt=prompt,
        max_tokens=max_tokens,
        n=n,
        temperature=temperature,
        MONA_additional_data={"customer_id": "A531251"},
    )
)

print(response.choices[0].text)

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
    "prompt": prompt,
    "max_tokens": max_tokens,
    "temperature": temperature,
    "model": model,
    "n": n,
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
    response_logger(response.json())
    print(response.json()["choices"][0]["text"])

except Exception:
    # Log exception to Mona
    exception_logger()
