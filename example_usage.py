from os import environ
import asyncio
import openai
import json
from os import environ

from mona_openai import monitor

openai.api_key = environ.get("OPEN_AI_KEY")

monitored_completion = monitor(
    openai.Completion,
    {
        "key": environ.get("MONA_API_KEY"),
        "secret": environ.get("MONA_SECRET"),
    },
    "SOME_MONITORING_CONTEXT_NAME",
)


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
import requests
from mona_openai import get_rest_monitor

# Get Mona logger
mona_logger = get_rest_monitor(
    "Completion",
    {
        "key": environ.get("MONA_API_KEY"),
        "secret": environ.get("MONA_SECRET"),
    },
    "TEST_MONITORING_CONTEXT_NAME",
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
response_logger, exception_logger = mona_logger.log_request(
    data, additional_data={"customer_id": "A531251"}
)

try:
    # Send the request to the API
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Check for HTTP errors
    response.raise_for_status()

    # Log response to Mona
    response_logger(response.json())
    print(response.json()["choices"][0]["text"])

except Exception as err:
    # Log exception to Mona
    exception_logger()
