#!/usr/bin/env python3
"""
Simple test script to check entity grounding setup.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.cardio_graph.extraction_utils.entity_grounding_service import (
    EntityGroundingService,
)


def test_simple():
    print("Initializing EntityGroundingService...")
    egs = EntityGroundingService()
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
    """
    Test case from GitHub issue: Validate SnoMed Linker for ontology completeness and linking issues.

    Text: Depression is common (15%–20% prevalence) in CVD, and associated
    with poor adherence and worse outcomes, including MACE and premature
    death.

    Expected entities that should be grounded:
    - Depression (should link to SNOMED CT depression concepts)
    - CVD (Cardiovascular Disease)
    - MACE (Major Adverse Cardiovascular Events)
    - premature death (should link to mortality concepts)

    Current issue: None of these entities are being grounded.
    """
    print("\n" + "=" * 60)
    print("TESTING GITHUB ISSUE: SnoMed Linker Validation")
    print("=" * 60)

    print("Initializing EntityGroundingService...")
    egs = EntityGroundingService()
    print("Service initialized successfully.")

    test_text = """Depression is common (15%–20% prevalence) in CVD, and associated
with poor adherence and worse outcomes, including MACE and premature
death."""

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


if __name__ == "__main__":
    test_simple()
    test_github_issue()
