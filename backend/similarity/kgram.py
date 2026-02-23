from typing import List, Tuple


def generate_kgrams(tokens: List[str], k: int = 5) -> List[Tuple[str]]:
    """
    Generate k-grams (sliding window of size k).
    """
    if len(tokens) < k:
        return []

    return [tuple(tokens[i:i + k]) for i in range(len(tokens) - k + 1)]