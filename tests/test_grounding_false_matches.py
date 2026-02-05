import unittest
from unittest.mock import patch

from cardio_graph.extraction_utils.guideline_graph_builder import (
    ExtractedConcept,
    GuidelineGraphBuilder,
)


class FakeSnomedExplorer:
    def __init__(self, results, preferred_terms, parent_map):
        self._results = results
        self._preferred_terms = preferred_terms
        self._parent_map = parent_map

    def connect(self):
        return None

    def search_concepts_by_term(self, term, limit=100):
        return self._results

    def get_preferred_term(self, concept_id):
        return self._preferred_terms.get(concept_id)

    def get_relationships(self, concept_id):
        parent_id = self._parent_map.get(concept_id)
        if parent_id is None:
            return []
        return [
            {
                "typeid": 116680003,
                "destinationid": parent_id,
            }
        ]


def _build_builder(fake_explorer):
    with patch(
        "cardio_graph.extraction_utils.guideline_graph_builder.SnomedExplorer",
        return_value=fake_explorer,
    ), patch(
        "cardio_graph.extraction_utils.guideline_graph_builder.create_client_registry",
        return_value=None,
    ):
        return GuidelineGraphBuilder(model="Qwen30b", node="g5")


class GroundingFalseMatchTests(unittest.TestCase):
    def _assert_unmapped(self, term, role, concept_id, preferred_term, parent_id):
        results = [{"conceptid": concept_id, "term": preferred_term}]
        preferred_terms = {concept_id: preferred_term}
        parent_map = {concept_id: parent_id}
        builder = _build_builder(FakeSnomedExplorer(results, preferred_terms, parent_map))

        best_id, best_term, score = builder._search_best_concept(term, role)

        self.assertIsNone(best_id)
        self.assertIsNone(best_term)
        self.assertEqual(score, 0.0)

    def test_complex_cad_not_caries(self):
        self._assert_unmapped(
            term="complex CAD",
            role="Condition",
            concept_id=24531002,
            preferred_term="Complex caries (morphologic abnormality)",
            parent_id=49601007,
        )

    def test_heart_team_consultation_not_acute_pain(self):
        self._assert_unmapped(
            term="Heart Team Consultation",
            role="Procedure",
            concept_id=421946003,
            preferred_term="Consultation for acute pain (procedure)",
            parent_id=71388002,
        )

    def test_heart_team_not_myocardial_infarction(self):
        self._assert_unmapped(
            term="Heart Team",
            role="Condition",
            concept_id=22298006,
            preferred_term="Myocardial infarction (disorder)",
            parent_id=49601007,
        )

    def test_chronic_coronary_syndrome_not_preinfarction(self):
        self._assert_unmapped(
            term="Chronic Coronary Syndrome",
            role="Condition",
            concept_id=4557003,
            preferred_term="Preinfarction syndrome (disorder)",
            parent_id=49601007,
        )

    def test_unmapped_terms_are_retained(self):
        term = "Heart Team Consultation"
        role = "Procedure"
        results = [{"conceptid": 421946003, "term": "Consultation for acute pain"}]
        preferred_terms = {421946003: "Consultation for acute pain (procedure)"}
        parent_map = {421946003: 71388002}
        builder = _build_builder(
            FakeSnomedExplorer(results, preferred_terms, parent_map)
        )
        extracted = [
            ExtractedConcept(
                rule_id=1,
                entity_original=term,
                entity_standardized_candidate=term,
                role=role,
                logic="",
                logic_structured={
                    "strength": "Class I",
                    "level": "C",
                    "direction": "POSITIVE",
                    "operator": None,
                    "threshold": None,
                    "unit": None,
                    "condition_context": None,
                },
            )
        ]

        with patch.object(builder, "extract_concepts", return_value=extracted):
            _, grounded = builder.extract_and_ground(
                "Heart Team Consultation", "text", "Test Guideline"
            )

        self.assertEqual(len(grounded), 1)
        self.assertIsNone(grounded[0].snomed_id)
        self.assertEqual(grounded[0].entity_standardized_candidate, term)
        self.assertEqual(grounded[0].target_label, "Procedure")


if __name__ == "__main__":
    unittest.main()
