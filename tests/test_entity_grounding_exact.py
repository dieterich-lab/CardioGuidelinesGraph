#!/usr/bin/env python3
"""
Test suite for exact matching entity grounding.
Tests the exact-first grounding approach that prevents false matches.
"""

import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.cardio_graph.extraction_utils.entity_grounding_service import (
    EntityGroundingService,
)

# Test only the core ontology for exact matching
ONTOLOGY_CONFIGS = [
    {
        "name": "coreonly_c62d4f6b",
        "path": "/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class_coreonly_c62d4f6b.owl",
    },
]


@pytest.fixture(
    scope="session", params=ONTOLOGY_CONFIGS, ids=[c["name"] for c in ONTOLOGY_CONFIGS]
)
def egs_service(request):
    """Fixture to initialize EGS once per ontology per session."""
    config = request.param
    print(f"\n=== Initializing EGS for {config['name']} ===")

    # Build index once if it doesn't exist, otherwise reuse
    index_path = f"/prj/doctoral_letters/guide/data/egs_index_{config['name']}"
    rebuild = not os.path.exists(index_path)

    if rebuild:
        print(f"Building index for {config['name']}...")
    else:
        print(f"Reusing existing index for {config['name']}...")

    egs = EntityGroundingService(
        ontology_path=config["path"],
        index_path=index_path,
        rebuild_index=rebuild,
    )

    return egs


@pytest.mark.parametrize(
    "text,expected_grounded",
    [
        ("HFrEF patients need beta blockers.", ["HFrEF"]),
        (
            "Depression is common in CVD, associated with heart disease.",
            ["Depression", "CVD"],
        ),
        (
            "HF and MI patients may need PCI or CABG.",
            ["HF", "MI", "PCI", "CABG"],
        ),
    ],
    ids=[
        "HFrEF-simple",
        "depression-CVD",
        "HF-MI-procedures",
    ],
)
def test_exact_matching_ground_truth(egs_service, text, expected_grounded):
    """
    Test exact-first grounding: verify expected entities are grounded and unwanted matches are avoided.
    """
    print(f"\n--- Testing exact matching: {text[:50]}... ---")

    # Run NER
    doc = egs_service.nlp(text)
    detected_entities = [ent.text for ent in doc.ents]

    # Run exact-first grounding
    grounded = egs_service.ground_exact_first(text)
    grounded_mentions = [g.mention for g in grounded]

    print(f"NER detected: {detected_entities}")
    print(f"Grounded (exact-first): {grounded_mentions}")
    print(f"Expected grounded: {expected_grounded}")

    # Core assertions: expected entities should be grounded
    for entity in expected_grounded:
        assert entity in grounded_mentions, f"Expected entity '{entity}' not grounded"

    # Critical assertion: ONLY expected entities should be grounded
    # This is the key test - exact matching should prevent false matches
    unexpected_grounded = [
        mention for mention in grounded_mentions if mention not in expected_grounded
    ]
    if unexpected_grounded:
        pytest.fail(
            f"Unexpected entities were grounded: {unexpected_grounded}. "
            f"Only {expected_grounded} should be grounded, but got {grounded_mentions}"
        )

    # At least some entities should be detected
    assert len(detected_entities) > 0, "No entities detected by NER"

    print("✅ Exact matching test passed")


def test_exact_vs_fuzzy_comparison(egs_service):
    """
    Compare exact matching vs fuzzy matching to demonstrate the improvement.
    """
    test_text = "HFrEF patients need beta blockers."

    print(f"\n--- Comparing exact vs fuzzy: {test_text} ---")

    # Fuzzy matching (original)
    grounded_fuzzy = egs_service.ground(test_text)
    fuzzy_mentions = [g.mention for g in grounded_fuzzy]

    # Exact-first matching
    grounded_exact = egs_service.ground_exact_first(test_text)
    exact_mentions = [g.mention for g in grounded_exact]

    print(f"Fuzzy grounded: {fuzzy_mentions}")
    print(f"Exact grounded: {exact_mentions}")

    # Exact should ground HFrEF but not "beta blockers"
    assert "HFrEF" in exact_mentions, "HFrEF should be grounded with exact matching"
    assert (
        "beta blockers" not in exact_mentions
    ), "beta blockers should NOT be grounded with exact matching"

    # Fuzzy incorrectly grounds "beta blockers"
    assert (
        "beta blockers" in fuzzy_mentions
    ), "Fuzzy matching should incorrectly ground 'beta blockers'"

    print("✅ Comparison test passed - exact matching prevents false matches")
