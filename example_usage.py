from os import environ
import asyncio
import openai

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
