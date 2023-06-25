from os import environ

from mona_openai import monitor_langchain_llm

from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate


MONA_API_KEY = environ.get("MONA_API_KEY")
MONA_SECRET = environ.get("MONA_SECRET")
MONA_CREDS = {
    "key": MONA_API_KEY,
    "secret": MONA_SECRET,
}

# This is the name of the monitoring class on Mona.
CONTEXT_CLASS_NAME = "MONITORED_LANGCHAIN_LLM"

# Wrap the LLM object with Mona monitoring.
llm = monitor_langchain_llm(
    OpenAI(openai_api_key=environ.get("OPEN_AI_KEY")),
    MONA_CREDS,
    CONTEXT_CLASS_NAME,
)

# Now you can use the llm directly along with additional Mona data.

print(
    llm.predict(
        "What would be a good company name for a company that makes "
        "colorful socks?",
        MONA_additional_data={"customer_id": "A531251"},
        MONA_context_id="some_random_id",
    )
)

# Or you can use the llm as part of a chain or agent.

prompt = PromptTemplate.from_template(
    "What is a good name for a company that makes {product}?"
)

chain = LLMChain(
    llm=llm,
    prompt=prompt,
    llm_kwargs={
        "MONA_additional_data": {"customer_id": "A531251"},
        "MONA_context_id": "fkljdaslfkjasl",
    },
)

print(chain.run("colorful socks"))
