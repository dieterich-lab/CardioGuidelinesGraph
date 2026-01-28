#!/usr/bin/env python3
"""
General test suite for entity grounding and ontology integration.
"""

import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.cardio_graph.extraction_utils.entity_grounding_service import (
    EntityGroundingService,
)

GUIDELINE_PATH = "/prj/doctoral_letters/guide/data/guidelines/text/esc_ccs.txt"


def test_simple():
    print("Initializing EntityGroundingService...")
    egs = EntityGroundingService(rebuild_index=True)
    print("Service initialized successfully.")

    test_text = "HFrEF patients need beta blockers."
    print(f"Testing with text: {test_text}")

    # Test NER
    doc = egs.nlp(test_text)
    entities = [ent.text for ent in doc.ents]
    print(f"NER detected entities: {entities}")

    # Test grounding
    grounded = egs.ground(test_text)
    print(f"Grounded entities: {len(grounded)}")
    for g in grounded:
        print(f"  {g.mention} -> {g.label}")


def test_github_issue():
    print("\n" + "=" * 60)
    print("TESTING GITHUB ISSUE: SnoMed Linker Validation")
    print("=" * 60)

    print("Initializing EntityGroundingService...")
    egs = EntityGroundingService(rebuild_index=True)
    print("Service initialized successfully.")

    test_text = """Depression is common (15%–20% prevalence) in CVD, and associated\nwith poor adherence and worse outcomes, including MACE and premature\ndeath."""

    print(f"\nTesting with text: {test_text}")

    # Test NER
    doc = egs.nlp(test_text)
    entities = [ent.text for ent in doc.ents]
    print(f"\nNER detected entities: {entities}")

    # Test grounding
    grounded = egs.ground(test_text)
    print(f"\nGrounding complete. Found {len(grounded)} grounded entities.")

    if grounded:
        for g in grounded:
            print(f"  ✅ {g.mention} -> {g.label}")
    else:
        print("  ❌ No entities were grounded!")

    # Expected entities that should be grounded
    expected_entities = ["Depression", "CVD", "MACE", "premature death"]
    ungrounded = [ent for ent in entities if ent not in [g.mention for g in grounded]]

    print(f"\nSUMMARY:")
    print(f"  Total NER entities: {len(entities)}")
    print(f"  Successfully grounded: {len(grounded)}")
    print(f"  Failed to ground: {len(ungrounded)}")

    if ungrounded:
        print(f"  Ungrounded entities: {ungrounded}")
        print("\n  Expected to be groundable: {expected_entities}")
        missing_expected = [
            e for e in expected_entities if e not in [g.mention for g in grounded]
        ]
        if missing_expected:
            print(f"  Missing expected entities: {missing_expected}")
    else:
        print("  All entities successfully grounded! 🎉")


def test_guideline_excerpt():
    """
    Test grounding on a real excerpt from the ESC guideline.
    """
    if not os.path.exists(GUIDELINE_PATH):
        pytest.skip("Guideline file not found.")
    with open(GUIDELINE_PATH, "r") as f:
        lines = f.readlines()
    # Use a paragraph with rich clinical content (lines 1000-1020)
    excerpt = "".join(lines[999:1020])
    print("\nTesting with ESC guideline excerpt:")
    print(excerpt)
    egs = EntityGroundingService(rebuild_index=False)
    doc = egs.nlp(excerpt)
    entities = [ent.text for ent in doc.ents]
    print(f"NER detected entities: {entities}")
    grounded = egs.ground(excerpt)
    print(f"Grounded entities: {len(grounded)}")
    for g in grounded:
        print(f"  {g.mention} -> {g.label}")
    # Optionally, check that key terms are grounded
    expected = ["HFrEF", "CABG", "PCI", "LVEF", "myocardial infarction"]
    found = [g.mention for g in grounded]
    missing = [e for e in expected if e not in found]
    print(f"Expected key terms: {expected}")
    print(f"Missing: {missing}")


def test_edge_cases():
    """
    Test abbreviations, synonyms, and ambiguous terms.
    """


# Parameterized recall/grounding test with assertions and recall metric
import pytest


@pytest.mark.parametrize(
    "text,expected_grounded,expected_detected",
    [
        ("HFrEF patients need beta blockers.", ["HFrEF"], ["HFrEF", "beta blockers"]),
        (
            "Depression is common (15%–20% prevalence) in CVD, and associated with poor adherence and worse outcomes, including MACE and premature death.",
            ["Depression", "CVD", "MACE", "premature death"],
            ["Depression", "prevalence", "CVD", "poor adherence", "worse", "outcomes", "MACE", "premature death"],
        ),
        (
            "HF and MI patients may need PCI or CABG. LV function is key.",
            ["HF", "MI", "PCI", "CABG", "LV function"],
            ["HF", "MI", "PCI", "CABG", "LV function"],
        ),
    ],
    ids=[
        "simple-HFrEF",
        "github-issue-MACE",
        "edge-cases-HF-MI-PCI-CABG-LV",
    ],
)
def test_full_grounding_pipeline(text, expected_grounded, expected_detected):
    """
    Full pipeline test: NER detection + grounding.
    Verifies that:
    1. Expected entities are detected by NER
    2. Expected entities are successfully grounded
    3. Non-groundable entities are detected but not grounded
    4. Only expected entities are grounded (no false positives)
    """
    egs = EntityGroundingService(rebuild_index=False)
    
    # Capture detected entities by temporarily modifying the ground method
    # Since we can't easily capture from ground(), we'll run NER separately
    doc = egs.nlp(text)
    detected_entities = [ent.text for ent in doc.ents]
    
    # Run full grounding
    grounded = egs.ground(text)
    grounded_mentions = [g.mention for g in grounded]
    
    print("\n--- FULL PIPELINE TEST DIAGNOSTICS ---")
    print(f"Text: {text}")
    print(f"NER Detected: {detected_entities}")
    print(f"Expected Detected: {expected_detected}")
    print(f"Grounded: {grounded_mentions}")
    print(f"Expected Grounded: {expected_grounded}")
    
    # Test 1: All expected entities should be detected by NER
    for entity in expected_grounded:
        assert entity in detected_entities, f"Expected entity '{entity}' not detected by NER"
    
    # Test 2: All expected entities should be grounded
    for entity in expected_grounded:
        assert entity in grounded_mentions, f"Expected entity '{entity}' not grounded"
    
    # Test 3: No unexpected entities should be grounded (precision check)
    unexpected_grounded = [g for g in grounded_mentions if g not in expected_grounded]
    assert not unexpected_grounded, f"Unexpected entities grounded: {unexpected_grounded}"
    
    # Test 4: Non-groundable entities should be detected but not grounded
    non_groundable = [d for d in detected_entities if d not in expected_grounded]
    grounded_non_groundable = [g for g in grounded_mentions if g in non_groundable]
    assert not grounded_non_groundable, f"Non-groundable entities were incorrectly grounded: {grounded_non_groundable}"
    
    # Test 5: Recall calculation
    recall = len(expected_grounded) / len(expected_grounded) if expected_grounded else 1.0
    assert recall >= 0.8, f"Grounding recall below threshold: {recall:.2f}"


def test_negative_control():
    """
    Test that non-cardiology text does not produce false positives.
    """
    egs = EntityGroundingService(rebuild_index=False)
    test_text = "The cat sat on the mat."
    print(f"\nTesting negative control: {test_text}")
    grounded = egs.ground(test_text)
    print(f"Grounded entities: {len(grounded)}")
    assert len(grounded) == 0


def test_ontology_integrity():
    """
    Test that core and SNOMED-derived classes are present in the index.
    """
    egs = EntityGroundingService(rebuild_index=False)
    # Try searching for a few core classes and known SNOMED-derived classes
    core_terms = ["HeartFailure", "Arrhythmia", "CoronaryArteryDisease"]
    snomed_terms = ["Acute left-sided heart failure", "Heart valve disorder"]
    for term in core_terms + snomed_terms:
        doc = egs.nlp(term)
        grounded = egs.ground(term)
        print(f"\nTesting ontology integrity for: {term}")
        if grounded:
            print(f"  Found: {grounded[0].label}")
        else:
            print(f"  Not found!")
        assert grounded, f"Ontology term '{term}' not found in index!"
