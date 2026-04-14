# ============================================================
# test_threshold_tuning.py
# Threshold testing and tuning for token-based Jaccard similarity.
#
# Tests 5 plagiarism scenarios:
#   1. Identical code (direct copy)
#   2. Renamed variables
#   3. Added comments and whitespace
#   4. Reordered statements
#   5. Genuinely different code
#
# Supports both hardcoded pairs and .py file pairs.
# ============================================================

import os
from typing import List, Dict, Any
from similarity.tokenizer import tokenize
from similarity.kgram import generate_kgrams
from similarity.fingerprint import generate_fingerprints
from similarity.similarity import compute_jaccard_similarity
from similarity.thresholds import (
    SIMILARITY_THRESHOLD_MIN,
    SIMILARITY_THRESHOLD_SUSPICIOUS,
    SIMILARITY_THRESHOLD_HIGH,
)


# ============================================================
# CONFIGURATION
# Adjust k during tuning -- use 3,5,7
# ============================================================

K = 3  # k-gram window size 


# ============================================================
# HARDCODED TEST PAIRS
# Each entry is a dict with:
#   - label:       name of the test case
#   - code_a:      first submission
#   - code_b:      second submission
#   - expected:    expected verdict ('low', 'moderate', 'suspicious', 'high')
# ============================================================

HARDCODED_PAIRS = [
    {
        "label": "Case 1: Identical Code (Direct Copy)",
        "expected": "high",
        "code_a": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
""",
        "code_b": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
""",
    },
    {
        "label": "Case 2: Renamed Variables",
        "expected": "high",
        "code_a": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
""",
        "code_b": """
def compute_total(values):
    result = 0
    for val in values:
        result += val
    return result
""",
    },
    {
        "label": "Case 3: Added Comments and Whitespace",
        "expected": "high",
        "code_a": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
""",
        "code_b": """
# This function adds up all numbers in a list
def calculate_sum(numbers):

    total = 0  # initialize total

    for num in numbers:
        total += num  # accumulate

    return total  # return final result
""",
    },
    {
        "label": "Case 4: Reordered Statements",
        "expected": "suspicious",
        "code_a": """
def process(data):
    data = data.strip()
    data = data.lower()
    data = data.replace(' ', '_')
    return data
""",
        "code_b": """
def process(data):
    data = data.lower()
    data = data.strip()
    data = data.replace(' ', '_')
    return data
""",
    },
    {
        "label": "Case 5: Genuinely Different Code (Should Score Low)",
        "expected": "low",
        "code_a": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
""",
        "code_b": """
def find_longest_word(sentence):
    words = sentence.split()
    longest = ''
    for word in words:
        if len(word) > len(longest):
            longest = word
    return longest
""",
    },
]


# ============================================================
# PIPELINE HELPER
# Runs the full tokenize → k-gram → fingerprint → score pipeline on a pair of code strings.
# ============================================================

def run_pipeline(code_a: str, code_b: str, k: int) -> Dict[str, Any]:
    """
    Run the full similarity pipeline on two raw code strings.

    Args:
        code_a: Source code of submission A
        code_b: Source code of submission B
        k:      k-gram window size

    Returns:
        Result dictionary from compute_jaccard_similarity()
    """
    tokens_a = tokenize(code_a)
    tokens_b = tokenize(code_b)

    kgrams_a = generate_kgrams(tokens_a, k=k)
    kgrams_b = generate_kgrams(tokens_b, k=k)

    fp_a = generate_fingerprints(kgrams_a)
    fp_b = generate_fingerprints(kgrams_b)

    return compute_jaccard_similarity(fp_a, fp_b)


# ============================================================
# FILE-BASED TEST LOADER
# Loads pairs of .py files from a given folder.
# Files are matched in alphabetical order: file1↔file2,
# file3↔file4, etc.
# Place sample files in: similarity/test_samples/
# ============================================================

def load_file_pairs(folder: str) -> List[Dict[str, Any]]:
    """
    Load pairs of .py files from a folder for comparison.
    Files are sorted alphabetically and paired sequentially.

    Args:
        folder: Path to the folder containing .py sample files

    Returns:
        List of dicts with keys: label, code_a, code_b, expected
    """
    if not os.path.exists(folder):
        print(f"  [!] Sample folder not found: {folder}")
        print(f"      Create it and add .py file pairs to test with real code.\n")
        return []

    files = sorted([
        f for f in os.listdir(folder) if f.endswith(".py")
    ])

    if len(files) < 2:
        print(f"  [!] Need at least 2 .py files in {folder} for file-based tests.\n")
        return []

    pairs = []
    for i in range(0, len(files) - 1, 2):
        file_a = os.path.join(folder, files[i])
        file_b = os.path.join(folder, files[i + 1])
        with open(file_a, "r") as fa, open(file_b, "r") as fb:
            pairs.append({
                "label": f"File Pair: {files[i]}  vs  {files[i + 1]}",
                "expected": "unknown",  # no ground truth for file pairs
                "code_a": fa.read(),
                "code_b": fb.read(),
            })

    return pairs


# ============================================================
# RESULT PRINTER
# Prints a formatted result block for each test case.
# Flags PASS/FAIL based on expected vs actual label.
# ============================================================

def print_result(label: str, result: Dict[str, Any], expected: str) -> None:
    """
    Print a formatted result block for a single test case.

    Args:
        label:    Test case name
        result:   Output from compute_jaccard_similarity()
        expected: Expected verdict label string (or 'unknown')
    """
    actual = result["label"]
    matches = len(result["matching_fingerprints"])

    if expected == "unknown":
        verdict = "  (no expected label — file pair)"
    elif actual == expected:
        verdict = "  ✓ PASS"
    else:
        verdict = f"  ✗ FAIL  (expected '{expected}', got '{actual}')"

    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    print(f"  Score:               {result['score']}")
    print(f"  Percentage:          {result['percentage']}%")
    print(f"  Label:               {actual}")
    print(f"  Matching fingerprints: {matches} / {result['total_unique']}")
    print(f"  Result:             {verdict}")


# ============================================================
# THRESHOLD SUMMARY
# After all tests, prints the active threshold values so
# you can log what settings produced what results during tuning.
# ============================================================

def print_threshold_summary() -> None:
    print(f"\n{'=' * 60}")
    print("  ACTIVE THRESHOLD SETTINGS")
    print(f"{'=' * 60}")
    print(f"  K (k-gram size):         {K}")
    print(f"  Min threshold:           {SIMILARITY_THRESHOLD_MIN}")
    print(f"  Suspicious threshold:    {SIMILARITY_THRESHOLD_SUSPICIOUS}")
    print(f"  High threshold:          {SIMILARITY_THRESHOLD_HIGH}")
    print(f"{'=' * 60}\n")


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("  TOKEN-BASED SIMILARITY — THRESHOLD TUNING TESTS")
    print("=" * 60)

    # --- Hardcoded tests ---
    print("\n[ HARDCODED TEST PAIRS ]\n")
    for pair in HARDCODED_PAIRS:
        result = run_pipeline(pair["code_a"], pair["code_b"], k=K)
        print_result(pair["label"], result, pair["expected"])

    # --- File-based tests ---
    print("\n\n[ FILE-BASED TEST PAIRS ]\n")
    sample_folder = os.path.join(os.path.dirname(__file__), "test_samples")
    file_pairs = load_file_pairs(sample_folder)

    if file_pairs:
        for pair in file_pairs:
            result = run_pipeline(pair["code_a"], pair["code_b"], k=K)
            print_result(pair["label"], result, pair["expected"])

    # --- Threshold summary ---
    print_threshold_summary()


if __name__ == "__main__":
    main()