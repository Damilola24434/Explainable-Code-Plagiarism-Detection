from typing import List, Tuple


def generate_kgrams(tokens: List[str], k: int = 5) -> List[Tuple[str]]:
    """
    Generate k-grams (sliding window of size k consecutive tokens).
    returns a list of k-grams, where each k-gram is represented as a tuple of k consecutive tokens
    """
    if len(tokens) < k:
        return []

    return [
        tuple(tokens[i:i + k]) # slice k tokens and convert to tuple
        for i in range(len(tokens) - k + 1)
    ]