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
    egs = EntityGroundingService(rebuild_index=False)
    test_text = "HF and MI patients may need PCI or CABG. LV function is key."
    print(f"\nTesting edge cases: {test_text}")
    doc = egs.nlp(test_text)
    entities = [ent.text for ent in doc.ents]
    print(f"NER detected entities: {entities}")
    grounded = egs.ground(test_text)
    print(f"Grounded entities: {len(grounded)}")
    for g in grounded:
        print(f"  {g.mention} -> {g.label}")


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
