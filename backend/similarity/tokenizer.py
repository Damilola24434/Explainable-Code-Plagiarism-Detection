import re
from typing import List


def normalize_text(text: str) -> str:
    """
    Normalize input text:
    - Lowercase
    - Remove punctuation
    - Remove extra whitespace
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()  # remove extra spaces
    return text


def tokenize(text: str) -> List[str]:
    """
    Convert normalized text into tokens (words).
    """
    normalized = normalize_text(text)
    return normalized.split()