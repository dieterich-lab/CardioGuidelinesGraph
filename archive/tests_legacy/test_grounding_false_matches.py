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
    with (
        patch(
            "cardio_graph.extraction_utils.guideline_graph_builder.SnomedExplorer",
            return_value=fake_explorer,
        ),
        patch(
            "cardio_graph.extraction_utils.guideline_graph_builder.create_client_registry",
            return_value=None,
        ),
    ):
        return GuidelineGraphBuilder(model="Qwen30b", node="g5")


class GroundingFalseMatchTests(unittest.TestCase):
    def _assert_verbose(self, query, expected, actual, health_note):
        print("\nQUERY:\n" + query)
        print("EXPECTED:\n" + str(expected))
        print("ACTUAL:\n" + str(actual))
        print("HEALTH NOTE:\n" + health_note)
        self.assertEqual(actual, expected)

    def _assert_unmapped(self, term, role, concept_id, preferred_term, parent_id):
        results = [{"conceptid": concept_id, "term": preferred_term}]
        preferred_terms = {concept_id: preferred_term}
        parent_map = {concept_id: parent_id}
        builder = _build_builder(
            FakeSnomedExplorer(results, preferred_terms, parent_map)
        )

        best_id, best_term, score = builder._search_best_concept(term, role)
        query = (
            "_search_best_concept(term={term}, role={role}) with candidate "
            "{preferred_term} ({concept_id})"
        ).format(
            term=term,
            role=role,
            preferred_term=preferred_term,
            concept_id=concept_id,
        )
        self._assert_verbose(
            query,
            (None, None, 0.0),
            (best_id, best_term, score),
            "False positives must be rejected so noisy SNOMED matches do not pollute the graph.",
        )

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

    def test_stress_imaging_not_occupation(self):
        self._assert_unmapped(
            term="Stress Imaging",
            role="Procedure",
            concept_id=136522006,
            preferred_term="Stressman (occupation)",
            parent_id=272379006,
        )

    def test_operative_mortality_not_perinatal_death(self):
        self._assert_unmapped(
            term="Operative Mortality",
            role="Condition",
            concept_id=10588007,
            preferred_term="Perinatal death (event)",
            parent_id=272379006,
        )

    def test_mid_term_mortality_not_maternal_death(self):
        self._assert_unmapped(
            term="Mid-term mortality",
            role="Condition",
            concept_id=59283008,
            preferred_term="Maternal death (event)",
            parent_id=272379006,
        )

    def test_geriatric_population_not_ethnic_group(self):
        self._assert_unmapped(
            term="Geriatric population",
            role="Condition",
            concept_id=48393004,
            preferred_term="Ethnic group finding (finding)",
            parent_id=404684003,
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
        builder.index.lookup = lambda _: None
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
        query = "extract_and_ground(Heart Team Consultation)"
        self._assert_verbose(
            query + " -> grounded count",
            1,
            len(grounded),
            "Unmapped concepts should still be retained as unresolved graph nodes.",
        )
        self._assert_verbose(
            query + " -> snomed_id",
            None,
            grounded[0].snomed_id,
            "Unmapped concepts must keep snomed_id=None for downstream handling.",
        )
        self._assert_verbose(
            query + " -> standardized",
            term,
            grounded[0].entity_standardized_candidate,
            "Standardized candidate should remain the original term when unmapped.",
        )
        self._assert_verbose(
            query + " -> target_label",
            "Procedure",
            grounded[0].target_label,
            "Role should map to Procedure even when unresolved.",
        )

    def test_other_role_kept_unmapped(self):
        term = "Heart Team"
        results = [{"conceptid": 22298006, "term": "Myocardial infarction"}]
        preferred_terms = {22298006: "Myocardial infarction (disorder)"}
        parent_map = {22298006: 49601007}
        builder = _build_builder(
            FakeSnomedExplorer(results, preferred_terms, parent_map)
        )
        builder.index.lookup = lambda _: None
        extracted = [
            ExtractedConcept(
                rule_id=1,
                entity_original=term,
                entity_standardized_candidate=term,
                role="Other",
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
            _, grounded = builder.extract_and_ground("Heart Team", "text", "Test")
        query = "extract_and_ground(Heart Team)"
        self._assert_verbose(
            query + " -> grounded count",
            1,
            len(grounded),
            "Other-role concepts should remain in the graph for traceability.",
        )
        self._assert_verbose(
            query + " -> snomed_id",
            None,
            grounded[0].snomed_id,
            "Other-role concepts must remain unmapped to avoid incorrect links.",
        )
        self._assert_verbose(
            query + " -> standardized",
            term,
            grounded[0].entity_standardized_candidate,
            "Other-role standardized text should stay unchanged when unmapped.",
        )


if __name__ == "__main__":
    unittest.main()
