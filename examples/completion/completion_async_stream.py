from os import environ
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
CONTEXT_CLASS_NAME = "MONITORED_COMPLETION_USE_CASE_NAME"

monitored_completion = monitor(
    openai.Completion,
    MONA_CREDS,
    CONTEXT_CLASS_NAME,
)

async def openAI_logic():
    response = await monitored_completion.acreate(
        stream=True,
        model="text-ada-001",
        prompt="I want to generate some text about ",
        max_tokens=20,
        n=1,
        temperature=0.2,
        # Adding aditional information for monitoring purposes, unrelated to
        # internal OpenAI call.
        MONA_additional_data={"customer_id": "A531251"},
    )
    async for event in response:
        print(event.choices[0].text)

asyncio.run(openAI_logic())