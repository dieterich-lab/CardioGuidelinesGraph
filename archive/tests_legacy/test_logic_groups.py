import unittest
from unittest.mock import patch

from cardio_graph.extraction_utils.guideline_graph_builder import (
    ExtractedConcept,
    GuidelineGraphBuilder,
)


class LogicGroupTests(unittest.TestCase):
    def _assert_verbose(self, query, expected, actual, health_note):
        print("\nQUERY:\n" + query)
        print("EXPECTED:\n" + str(expected))
        print("ACTUAL:\n" + str(actual))
        print("HEALTH NOTE:\n" + health_note)
        self.assertEqual(actual, expected)

    def test_or_condition_is_split_into_groups(self):
        concept = ExtractedConcept(
            rule_id=1,
            entity_original="percutaneous or surgical revascularization",
            entity_standardized_candidate="percutaneous coronary intervention or coronary artery bypass grafting",
            role="Condition",
            logic="patients scheduled for percutaneous or surgical revascularization",
            logic_structured={
                "operator": "PRESENT",
                "direction": "UNKNOWN",
            },
        )

        with (
            patch(
                "cardio_graph.extraction_utils.guideline_graph_builder.create_client_registry",
                return_value=None,
            ),
            patch(
                "cardio_graph.extraction_utils.guideline_graph_builder.SnomedExplorer",
            ),
        ):
            builder = GuidelineGraphBuilder(model="Qwen30b", node="g5")

        expanded = builder._explode_or_conditions([concept])
        query = "_explode_or_conditions([ExtractedConcept(... OR ...)])"
        self._assert_verbose(
            query,
            2,
            len(expanded),
            "OR conditions must be split to preserve logical branching in the graph.",
        )
        logic_types = [c.logic_structured.get("logic_type") for c in expanded]
        self._assert_verbose(
            query + " -> logic_type",
            ["OR", "OR"],
            logic_types,
            "All expanded concepts must carry logic_type=OR for correct grouping.",
        )
        group_flags = [bool(c.logic_structured.get("logic_group")) for c in expanded]
        self._assert_verbose(
            query + " -> logic_group",
            [True, True],
            group_flags,
            "Each expanded concept must have a shared logic_group identifier.",
        )


if __name__ == "__main__":
    unittest.main()
