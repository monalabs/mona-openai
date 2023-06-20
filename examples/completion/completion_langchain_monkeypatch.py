from os import environ

from mona_openai import monitor
import openai

from langchain.llms import OpenAI

MONA_API_KEY = environ.get("MONA_API_KEY")
MONA_SECRET = environ.get("MONA_SECRET")
MONA_CREDS = {
    "key": MONA_API_KEY,
    "secret": MONA_SECRET,
}

# This is the name of the monitoring class on Mona.
CONTEXT_CLASS_NAME = "MONITORED_COMPLETION_USE_CASE_NAME"

openai.Completion = monitor(
    openai.Completion,
    MONA_CREDS,
    CONTEXT_CLASS_NAME,
)

# Note that we have to create the LLM object after monkey-patching
# openai.Completion.
llm = OpenAI(openai_api_key=environ.get("OPEN_AI_KEY"))
print(llm.predict("What would be a good company name?"))
