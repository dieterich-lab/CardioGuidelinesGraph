#!/usr/bin/env python3
"""
Fast test suite for entity grounding with ground truth validation.
Optimized to run within 5 minutes by focusing on ground truth tests only.
"""

import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.cardio_graph.extraction_utils.entity_grounding_service import (
    EntityGroundingService,
)

# Test only 2 ontologies for speed (core and curated)
ONTOLOGY_CONFIGS = [
    {
        "name": "coreonly_c62d4f6b",
        "path": "/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class_coreonly_c62d4f6b.owl",
    },
    {
        "name": "curatedsnomed_7318fa4c",
        "path": "/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class_curatedsnomed_7318fa4c.owl",
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
def test_ground_truth_pipeline(egs_service, text, expected_grounded):
    """
    Fast ground truth test: verify expected entities are detected and grounded.
    This is the core test with actual ground truth validation.
    """
    print(f"\n--- Testing: {text[:50]}... ---")

    # Run NER
    doc = egs_service.nlp(text)
    detected_entities = [ent.text for ent in doc.ents]

    # Run grounding
    grounded = egs_service.ground(text)
    grounded_mentions = [g.mention for g in grounded]

    print(f"NER detected: {detected_entities}")
    print(f"Grounded: {grounded_mentions}")
    print(f"Expected grounded: {expected_grounded}")

    # Core assertions: expected entities should be grounded
    for entity in expected_grounded:
        assert entity in grounded_mentions, f"Expected entity '{entity}' not grounded"

    # Critical assertion: ONLY expected entities should be grounded
    # If any unexpected entities are grounded, this is a failure
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

    print("✅ Test passed")


def test_ontology_integrity(egs_service):
    """
    Test that key cardiovascular concepts can be grounded correctly.
    This ensures the ontology contains the necessary concepts for the domain.
    """
    test_cases = [
        ("Heart failure", "Heart failure"),
        ("Myocardial infarction", "Myocardial infarction"),
        ("Coronary artery disease", "Coronary artery disease"),
    ]

    for text, expected_concept in test_cases:
        print(f"\n--- Testing ontology integrity for: {text} ---")

        grounded = egs_service.ground(text)
        grounded_mentions = [g.mention for g in grounded]

        # Should find exactly one grounded entity
        assert (
            len(grounded) == 1
        ), f"Expected 1 grounded entity for '{text}', got {len(grounded)}"

        # The grounded entity should match the input
        assert (
            grounded[0].mention == text
        ), f"Grounded mention '{grounded[0].mention}' doesn't match input '{text}'"

        # Print the actual concept found for verification
        print(f"✅ Found: {grounded[0].label}")
