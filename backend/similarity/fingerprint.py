import hashlib
from typing import List, Tuple


def hash_kgram(kgram: Tuple[str]) -> str:
    """
    Convert a k-gram tuple into a hash string.
    """
    kgram_string = " ".join(kgram)
    return hashlib.sha256(kgram_string.encode()).hexdigest()


def generate_fingerprints(kgrams: List[Tuple[str]]) -> List[str]:
    """
    Generate hash fingerprints for all k-grams.
    """
    return [hash_kgram(k) for k in kgrams]