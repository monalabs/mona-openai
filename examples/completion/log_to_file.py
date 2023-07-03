from os import environ
import openai
from mona_openai.loggers import FileLogger

from mona_openai import monitor_with_logger

openai.api_key = environ.get("OPEN_AI_KEY")

logger = FileLogger("temp.txt")
monitored_completion = monitor_with_logger(
    openai.Completion,
    logger,
)

response = monitored_completion.create(
    model="text-ada-001",
    prompt="I want to generate some text about ",
    max_tokens=20,
    n=1,
    temperature=0.2,
    # Adding additional information for monitoring purposes, unrelated to
    # internal OpenAI call.
    MONA_additional_data={"customer_id": "A531251"},
)
