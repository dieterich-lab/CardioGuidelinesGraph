import unittest
from unittest.mock import patch

from cardio_graph.extraction_utils.guideline_graph_builder import (
    ExtractedConcept,
    GuidelineGraphBuilder,
)


class LogicGroupTests(unittest.TestCase):
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

        with patch(
            "cardio_graph.extraction_utils.guideline_graph_builder.create_client_registry",
            return_value=None,
        ), patch(
            "cardio_graph.extraction_utils.guideline_graph_builder.SnomedExplorer",
        ):
            builder = GuidelineGraphBuilder(model="Qwen30b", node="g5")

        expanded = builder._explode_or_conditions([concept])
        self.assertEqual(len(expanded), 2)
        self.assertTrue(all(c.logic_structured.get("logic_type") == "OR" for c in expanded))
        self.assertTrue(all(c.logic_structured.get("logic_group") for c in expanded))


if __name__ == "__main__":
    unittest.main()
