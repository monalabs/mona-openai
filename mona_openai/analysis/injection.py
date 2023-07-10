"""
Logic to create prompt injection probability scores.
"""
from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        TextClassificationPipeline,
    )

# Init the model and tokenizer
HUGGING_FACE_MODEL_PATH = "JasperLS/gelectra-base-injection"
_tokenizer = AutoTokenizer.from_pretrained(HUGGING_FACE_MODEL_PATH)
_text_classification_pipeline = TextClassificationPipeline(
    model=AutoModelForSequenceClassification.from_pretrained(HUGGING_FACE_MODEL_PATH), tokenizer=_tokenizer
)


def get_prompt_injection_prob(text: str) -> float:
    result = _text_classification_pipeline(
        text, truncation=True, max_length=_tokenizer.model_max_length
    )
    print(result)
    return (
        result[0]["score"]
        if result[0]["label"] == "INJECTION"
        else 1 - result[0]["score"]
    )
