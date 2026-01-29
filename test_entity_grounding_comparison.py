#!/usr/bin/env python3
"""
Test script to compare exact vs hybrid matching in entity grounding.
Demonstrates the value of applying ontology generation's matching logic to grounding.
"""

import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from cardio_graph.extraction_utils.entity_grounding_service import (
    EntityGroundingService,
)


def test_matching_comparison():
    """Compare exact vs hybrid matching approaches."""

    # Initialize the grounding service
    egs = EntityGroundingService(
        ontology_path="/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class.owl",
        index_path="/prj/doctoral_letters/guide/data/egs_index",
        rebuild_index=False,  # Use existing index
    )

    # Test cases that should benefit from hybrid matching
    test_cases = [
        {
            "text": "The patient experienced major adverse cardiovascular events during treatment.",
            "expected_entity": "major adverse cardiovascular events",
            "notes": "Plural form should match MACE abbreviation in ontology",
        },
        {
            "text": "Myocardial infarctions are a leading cause of death worldwide.",
            "expected_entity": "myocardial infarctions",
            "notes": "Plural form should match MI abbreviation in ontology",
        },
        {
            "text": "Heart failure with reduced ejection fraction requires specialized treatment.",
            "expected_entity": "heart failure",
            "notes": "Should match HF abbreviation in ontology",
        },
    ]

    print("=== Entity Grounding: Exact vs Hybrid Matching Comparison ===\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['notes']}")
        print(f"Text: \"{test_case['text']}\"\n")

        # Test exact matching (current default)
        print("1. EXACT MATCHING (current approach):")
        try:
            exact_results = egs.ground(test_case["text"])
            if exact_results:
                for entity in exact_results:
                    print(
                        f"   ✅ Grounded: '{entity.mention}' -> '{entity.label}' (score: {entity.score:.2f})"
                    )
            else:
                print("   ❌ No entities grounded")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

        # Test hybrid matching (proposed enhancement)
        print("2. HYBRID MATCHING (proposed enhancement):")
        try:
            hybrid_results = egs.ground_hybrid_matching(
                test_case["text"], enable_fallback=True
            )
            if hybrid_results:
                for entity in hybrid_results:
                    method = getattr(entity, "method", "unknown")
                    print(
                        f"   ✅ Grounded: '{entity.mention}' -> '{entity.label}' (score: {entity.score:.2f}, method: {method})"
                    )
            else:
                print("   ❌ No entities grounded")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print("-" * 80)
        print()


def test_abbreviation_coverage():
    """Test how well the current ontology covers clinical abbreviations."""

    egs = EntityGroundingService(
        ontology_path="/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class.owl",
        index_path="/prj/doctoral_letters/guide/data/egs_index",
        rebuild_index=False,
    )

    # Common clinical abbreviations that should be in the ontology
    abbreviations_to_test = [
        "MACE",  # Major Adverse Cardiovascular Events
        "HF",  # Heart Failure
        "MI",  # Myocardial Infarction
        "CAD",  # Coronary Artery Disease
        "AF",  # Atrial Fibrillation
        "VT",  # Ventricular Tachycardia
        "CHF",  # Congestive Heart Failure
        "CABG",  # Coronary Artery Bypass Grafting
        "PCI",  # Percutaneous Coronary Intervention
        "LVEF",  # Left Ventricular Ejection Fraction
    ]

    print("=== Abbreviation Coverage Test ===")
    print("Testing direct abbreviation matching in ontology synonyms:\n")

    covered = 0
    total = len(abbreviations_to_test)

    for abbr in abbreviations_to_test:
        # Test if abbreviation exists as a synonym
        matches = egs._find_exact_synonym_matches(abbr)
        if matches:
            print(f"✅ '{abbr}' -> '{matches[0]['label']}'")
            covered += 1
        else:
            print(f"❌ '{abbr}' -> No direct match found")

    print(
        f"\nCoverage: {covered}/{total} ({covered/total*100:.1f}%) abbreviations have direct synonym matches"
    )

    # Test what happens with full forms that might be extracted by spaCy
    print("\n=== Full Form Matching Test ===")
    print("Testing what happens when spaCy extracts full forms:\n")

    full_form_tests = [
        ("major adverse cardiovascular events", "MACE"),
        ("heart failure", "HF"),
        ("myocardial infarction", "MI"),
        ("coronary artery disease", "CAD"),
    ]

    for full_form, expected_abbr in full_form_tests:
        # Test exact matching
        exact_matches = egs._find_exact_synonym_matches(full_form)
        exact_result = "✅" if exact_matches else "❌"

        # Test hybrid matching
        hybrid_match = egs._find_hybrid_synonym_match(full_form)
        hybrid_result = "✅" if hybrid_match else "❌"
        hybrid_method = hybrid_match.get("method", "none") if hybrid_match else "none"

        print(f"'{full_form}' -> {expected_abbr}")
        print(f"  Exact: {exact_result} | Hybrid: {hybrid_result} ({hybrid_method})")


if __name__ == "__main__":
    try:
        test_matching_comparison()
        print("\n" + "=" * 80 + "\n")
        test_abbreviation_coverage()
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback

        traceback.print_exc()
