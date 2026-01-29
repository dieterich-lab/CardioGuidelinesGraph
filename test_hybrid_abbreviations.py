#!/usr/bin/env python3
"""
Test script to verify hybrid abbreviation matching functionality
"""

import difflib
import os
import re


def load_abbreviations() -> dict:
    """Load guideline-internal abbreviations from abbrv.txt file."""
    abbrv_path = "/home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/snomedct_utils/abbrv.txt"
    abbreviations = {}

    try:
        with open(abbrv_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Split by "; " and parse each abbreviation
        entries = content.split("; ")
        for entry in entries:
            entry = entry.strip()
            if not entry or entry.endswith(". a"):  # Skip the trailing ". a"
                continue

            if ", " in entry:
                abbr, full_term = entry.split(", ", 1)
                abbr = abbr.strip()
                full_term = full_term.strip()
                if abbr and full_term:
                    abbreviations[full_term.lower()] = abbr

    except Exception as e:
        print(f"Warning: Could not load abbreviations file: {e}")

    return abbreviations


def normalize_term(term: str) -> str:
    """Normalize a term for better matching."""
    # Convert to lowercase and remove punctuation/parentheses
    normalized = re.sub(r"[^\w\s]", "", term.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Split into words
    words = normalized.split()

    # Handle some common medical term variations
    normalized_words = []
    for word in words:
        # Handle plural/singular (basic rules)
        if word.endswith("ies"):
            word = word[:-3] + "y"  # studies -> study
        elif (
            word.endswith("es")
            and not word.endswith("ses")
            and not word.endswith("zes")
        ):
            word = word[:-2]  # diseases -> disease (but not analyses, diagnoses)
        elif word.endswith("s") and not word.endswith("ss") and not word.endswith("us"):
            word = word[:-1]  # events -> event (but not stress, focus)

        # Skip very short words (likely noise)
        if len(word) > 1:
            normalized_words.append(word)

    # Sort words for order-independent matching
    return " ".join(sorted(normalized_words))


def find_abbreviation_match(term: str, abbreviations: dict) -> tuple[str, str]:
    """Find abbreviation match for a term using hybrid flexible matching.

    Returns:
        Tuple of (abbreviation, method_used) or ("", "") if no match
    """
    term_lower = term.lower()

    # 1. Exact match (fastest)
    if term_lower in abbreviations:
        return abbreviations[term_lower], "exact"

    # 2. Normalized match (handles plurals, punctuation, case)
    normalized_term = normalize_term(term_lower)
    for full_term, abbr in abbreviations.items():
        if normalize_term(full_term) == normalized_term:
            return abbr, "normalized"

    # 3. Fuzzy match (handles minor variations, typos)
    best_match = None
    best_ratio = 0.0

    for full_term in abbreviations.keys():
        ratio = difflib.SequenceMatcher(None, term_lower, full_term.lower()).ratio()
        if ratio > best_ratio and ratio > 0.85:  # 85% similarity threshold
            best_match = full_term
            best_ratio = ratio

    if best_match:
        return abbreviations[best_match], "fuzzy"

    # 4. Token-based match (handles word reordering)
    term_words = set(re.findall(r"\b\w+\b", term_lower))

    for full_term, abbr in abbreviations.items():
        dict_words = set(re.findall(r"\b\w+\b", full_term.lower()))
        if term_words and dict_words:
            # Calculate Jaccard similarity (intersection over union)
            intersection = len(term_words & dict_words)
            union = len(term_words | dict_words)
            if union > 0:
                similarity = intersection / union
                if similarity > 0.8:  # 80% word overlap
                    return abbr, "token-based"

    return "", ""


def test_hybrid_matching():
    """Test the hybrid abbreviation matching."""
    abbreviations = load_abbreviations()
    print(f"Loaded {len(abbreviations)} abbreviations")

    # Test cases with various types of variations
    test_cases = [
        # Exact matches
        ("heart failure", "HF", "exact"),
        ("major adverse cardiovascular events", "MACE", "exact"),
        # Case variations (should match exact)
        ("Heart Failure", "HF", "exact"),
        ("HEART FAILURE", "HF", "exact"),
        # Normalized matches (plural/singular)
        (
            "major adverse cardiovascular event",
            "MACE",
            "normalized",
        ),  # singular vs plural
        ("myocardial infarctions", "MI", "normalized"),  # plural vs singular
        # Fuzzy matches (minor variations)
        # Note: These would need actual fuzzy cases to test
        # Token-based matches (word reordering)
        # Note: These would need reordering cases to test
        # No match cases
        ("completely different term", "", ""),
        ("random words", "", ""),
    ]

    print("\nTesting hybrid abbreviation matching:")
    print("=" * 60)

    for test_term, expected_abbr, expected_method in test_cases:
        result_abbr, result_method = find_abbreviation_match(test_term, abbreviations)
        status = "✅" if result_abbr == expected_abbr else "❌"
        method_status = (
            "✅" if result_method == expected_method else f"❌ (got: {result_method})"
        )

        print(
            f"{status} '{test_term}' -> '{result_abbr}' (expected: '{expected_abbr}')"
        )
        if result_abbr:
            print(f"    Method: {result_method} {method_status}")

        # Show normalization for debugging
        if result_method == "normalized":
            print(f"    Normalized: '{normalize_term(test_term)}'")


if __name__ == "__main__":
    test_hybrid_matching()
