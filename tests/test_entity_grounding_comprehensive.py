#!/usr/bin/env python3
"""
Comprehensive test suite for exact matching entity grounding.
Combines all entity grounding tests using exact matching to prevent false positives.
Optimized to run within 10 minutes by focusing on core ontology and essential tests.
"""

import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.cardio_graph.extraction_utils.entity_grounding_service import (
    EntityGroundingService,
)

# Use only core ontology for speed (runs in ~5-7 minutes total)
ONTOLOGY_CONFIGS = [
    {
        "name": "coreonly_c62d4f6b",
        "path": "/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class_coreonly_c62d4f6b.owl",
    },
]

GUIDELINE_PATH = "/prj/doctoral_letters/guide/data/guidelines/text/esc_ccs.txt"


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
    Core exact matching test: verify expected entities are grounded and unwanted matches are avoided.
    This is the primary test that validates exact matching prevents false positives.
    """
    print(f"\n--- Testing exact matching: {text[:50]}... ---")

    # Run NER
    doc = egs_service.nlp(text)
    detected_entities = [ent.text for ent in doc.ents]

    # Run exact-first grounding (the key improvement)
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
    Demonstrate the improvement: exact matching prevents false matches that fuzzy matching allows.
    """
    test_text = "HFrEF patients need beta blockers."

    print(f"\n--- Comparing exact vs fuzzy: {test_text} ---")

    # Fuzzy matching (original - shows the problem)
    grounded_fuzzy = egs_service.ground(test_text)
    fuzzy_mentions = [g.mention for g in grounded_fuzzy]

    # Exact-first matching (the solution)
    grounded_exact = egs_service.ground_exact_first(test_text)
    exact_mentions = [g.mention for g in grounded_exact]

    print(f"Fuzzy grounded: {fuzzy_mentions}")
    print(f"Exact grounded: {exact_mentions}")

    # Exact should ground HFrEF but not "beta blockers"
    assert "HFrEF" in exact_mentions, "HFrEF should be grounded with exact matching"
    assert (
        "beta blockers" not in exact_mentions
    ), "beta blockers should NOT be grounded with exact matching"

    # Fuzzy incorrectly grounds "beta blockers" (demonstrates the problem)
    assert (
        "beta blockers" in fuzzy_mentions
    ), "Fuzzy matching should incorrectly ground 'beta blockers'"

    print("✅ Comparison test passed - exact matching prevents false matches")


@pytest.mark.parametrize(
    "text,expected_grounded,expected_detected",
    [
        ("HFrEF patients need beta blockers.", ["HFrEF"], ["HFrEF", "beta blockers"]),
        (
            "Depression is common (15%–20% prevalence) in CVD, and associated with poor adherence and worse outcomes, including MACE and premature death.",
            ["Depression", "CVD", "MACE"],
            [
                "Depression",
                "prevalence",
                "CVD",
                "poor adherence",
                "worse",
                "outcomes",
                "MACE",
                "premature death",
            ],
        ),
        (
            "HF and MI patients may need PCI or CABG. LV function is key.",
            ["HF", "MI", "PCI", "CABG"],
            ["HF", "MI", "PCI", "CABG", "LV function"],
        ),
    ],
    ids=[
        "simple-HFrEF",
        "github-issue-MACE",
        "edge-cases-HF-MI-PCI-CABG-LV",
    ],
)
def test_full_pipeline_exact_matching(
    egs_service, text, expected_grounded, expected_detected
):
    """
    Full pipeline test with exact matching: NER detection + exact grounding.
    Verifies that exact matching provides precision while maintaining recall for expected terms.
    """
    print(f"\n=== Testing Full Pipeline with Exact Matching ===")

    # Capture detected entities
    doc = egs_service.nlp(text)
    detected_entities = [ent.text for ent in doc.ents]

    # Run exact grounding
    grounded = egs_service.ground_exact_first(text)
    grounded_mentions = [g.mention for g in grounded]

    print("\n--- FULL PIPELINE TEST DIAGNOSTICS ---")
    print(f"Text: {text}")
    print(f"NER Detected: {detected_entities}")
    print(f"Expected Detected: {expected_detected}")
    print(f"Grounded (exact): {grounded_mentions}")
    print(f"Expected Grounded: {expected_grounded}")

    # Test 1: All expected entities should be detected by NER
    for entity in expected_grounded:
        assert (
            entity in detected_entities
        ), f"Expected entity '{entity}' not detected by NER"

    # Test 2: All expected entities should be grounded
    for entity in expected_grounded:
        assert entity in grounded_mentions, f"Expected entity '{entity}' not grounded"

    # Test 3: No unexpected entities should be grounded (precision check)
    unexpected_grounded = [g for g in grounded_mentions if g not in expected_grounded]
    assert (
        not unexpected_grounded
    ), f"Unexpected entities grounded: {unexpected_grounded}"

    # Test 4: Non-groundable entities should be detected but not grounded
    non_groundable = [d for d in detected_entities if d not in expected_grounded]
    grounded_non_groundable = [g for g in grounded_mentions if g in non_groundable]
    assert (
        not grounded_non_groundable
    ), f"Non-groundable entities were incorrectly grounded: {grounded_non_groundable}"

    print("✅ Full pipeline test passed")


def test_guideline_excerpt_exact_matching(egs_service):
    """
    Test exact matching on real guideline excerpts to ensure it works on clinical text.
    """
    print(f"\n=== Testing Guideline Excerpt with Exact Matching ===")

    if not os.path.exists(GUIDELINE_PATH):
        pytest.skip("Guideline file not found.")

    with open(GUIDELINE_PATH, "r") as f:
        lines = f.readlines()

    # Use a paragraph with rich clinical content (lines 1000-1020)
    excerpt = "".join(lines[999:1020])
    print("\nTesting with ESC guideline excerpt:")
    print(excerpt)

    # Test NER
    doc = egs_service.nlp(excerpt)
    entities = [ent.text for ent in doc.ents]
    print(f"NER detected entities: {entities}")

    # Test exact grounding
    grounded = egs_service.ground_exact_first(excerpt)
    grounded_mentions = [g.mention for g in grounded]
    print(f"Grounded entities (exact): {len(grounded)}")
    for g in grounded:
        print(f"  {g.mention} -> {g.label}")

    # Check that key cardiovascular terms are grounded
    expected = ["HFrEF", "CABG", "PCI", "LVEF", "myocardial infarction"]
    found = [g.mention for g in grounded]
    missing = [e for e in expected if e not in found]

    print(f"Expected key terms: {expected}")
    print(f"Found: {found}")
    print(f"Missing: {missing}")

    # At least some key terms should be found
    found_key_terms = [e for e in expected if e in found]
    assert len(found_key_terms) > 0, f"No key cardiovascular terms found. Expected at least one of {expected}"

    print(f"✅ Found {len(found_key_terms)} key terms: {found_key_terms}")


def test_negative_control_exact_matching(egs_service):
    """
    Test that non-cardiology text does not produce false positives with exact matching.
    """
    print(f"\n=== Testing Negative Control with Exact Matching ===")

    test_text = "The cat sat on the mat."
    print(f"Testing negative control: {test_text}")

    grounded = egs_service.ground_exact_first(test_text)
    grounded_mentions = [g.mention for g in grounded]

    print(f"Grounded entities: {len(grounded)} - {grounded_mentions}")

    # Should not ground any entities in non-medical text
    assert len(grounded) == 0, f"Unexpected entities grounded in negative control: {grounded_mentions}"

    print("✅ Negative control passed - no false positives")


def test_ontology_integrity_exact_matching(egs_service):
    """
    Test that key cardiovascular concepts can be grounded correctly with exact matching.
    """
    test_cases = [
        ("Heart failure", "Heart failure"),
        ("Myocardial infarction", "Myocardial infarction"),
        ("Coronary artery disease", "Coronary artery disease"),
    ]

    for text, expected_concept in test_cases:
        print(f"\n--- Testing ontology integrity for: {text} ---")

        grounded = egs_service.ground_exact_first(text)
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


def test_github_issue_scenario_exact_matching(egs_service):
    """
    Test the specific GitHub issue scenario with exact matching.
    """
    print(f"\n=== Testing GitHub Issue Scenario with Exact Matching ===")

    test_text = """Depression is common (15%–20% prevalence) in CVD, and associated
with poor adherence and worse outcomes, including MACE and premature
death."""

    print(f"\nTesting with text: {test_text}")

    # Test NER
    doc = egs_service.nlp(test_text)
    entities = [ent.text for ent in doc.ents]
    print(f"\nNER detected entities: {entities}")

    # Test exact grounding
    grounded = egs_service.ground_exact_first(test_text)
    grounded_mentions = [g.mention for g in grounded]
    print(f"\nGrounding complete. Found {len(grounded)} grounded entities.")

    if grounded:
        for g in grounded:
            print(f"  ✅ {g.mention} -> {g.label}")
    else:
        print("  ❌ No entities were grounded!")

    # Expected entities that should be grounded
    expected_entities = ["Depression", "CVD", "MACE"]
    ungrounded = [ent for ent in entities if ent not in grounded_mentions]

    print(f"\nSUMMARY:")
    print(f"  Total NER entities: {len(entities)}")
    print(f"  Successfully grounded: {len(grounded)}")
    print(f"  Failed to ground: {len(ungrounded)}")

    if ungrounded:
        print(f"  Ungrounded entities: {ungrounded}")
        print(f"  Expected to be groundable: {expected_entities}")
        missing_expected = [
            e for e in expected_entities if e not in grounded_mentions
        ]
        if missing_expected:
            print(f"  Missing expected entities: {missing_expected}")
    else:
        print("  All entities successfully grounded! 🎉")

    # Verify expected entities are grounded
    for expected in expected_entities:
        assert expected in grounded_mentions, f"Expected entity '{expected}' not grounded"

    print("✅ GitHub issue scenario test passed")