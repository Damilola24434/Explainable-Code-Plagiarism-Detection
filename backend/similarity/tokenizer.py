import re # import python's regular expression module
from typing import List # import List type 


def normalize_text(text: str) -> str:
    """
    The following lines of code normalize text by:
    1. converting to lowercase
    2. removing punctuation
    3. removing extra white saces
    And then returns a "clean" string
    """
    text = text.lower() # converts all character to lowercase

    text = re.sub(r"[^\w\s]", "", text)  
    # removes any character that is not word character(letters, digits, underscore)
    # removes whitespaces
    # replaces the removed characters with an empty string

    text = re.sub(r"\s+", " ", text).strip()  
    # replace multiple spaces (including tabs and newlines) with a single space
    # strip removes leading and trailing white spaces

    return text


def tokenize(text: str) -> List[str]:
    """
    Convert normalized text into tokens (words).
    """
    normalized = normalize_text(text)
    return normalized.split() 
    #split the normalixed string into words, use whitespace as delimiter
    # returns a list of individual word tokens
