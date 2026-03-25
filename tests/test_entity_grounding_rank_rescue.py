import unittest

from cardio_graph_core.grounding.entity_grounding_service import EntityGroundingService


class _StubBuilder:
    semantic_penalty_evidence_relief_enabled = False
    semantic_penalty_evidence_min_coverage = 0.75
    semantic_penalty_evidence_max_vector_rank = 3
    semantic_penalty_evidence_scale = 0.5
    vector_rank_rescue_enabled = False
    vector_rank_rescue_margin = 0.015
    vector_rank_rescue_max_rank = 3
    vector_rank_rescue_min_coverage = 0.70


class EntityGroundingRankRescueTests(unittest.TestCase):
    def setUp(self):
        self.builder = _StubBuilder()
        self.service = EntityGroundingService(self.builder)

    def test_effective_semantic_penalty_no_relief_when_disabled(self):
        self.assertEqual(
            self.service._effective_semantic_penalty(
                base_penalty=0.06,
                weighted_coverage=0.95,
                vector_rank=1,
            ),
            0.06,
        )

    def test_effective_semantic_penalty_relief_when_evidence_strong(self):
        self.builder.semantic_penalty_evidence_relief_enabled = True
        self.assertEqual(
            self.service._effective_semantic_penalty(
                base_penalty=0.06,
                weighted_coverage=0.90,
                vector_rank=1,
            ),
            0.03,
        )

    def test_should_vector_rank_promote_true_for_near_tie_with_strong_rank(self):
        self.builder.vector_rank_rescue_enabled = True
        top = {
            "final_score": 0.81,
            "coverage": 0.86,
            "lexical": 0.84,
            "vector_rank": None,
        }
        runner = {
            "final_score": 0.80,
            "coverage": 0.88,
            "lexical": 0.83,
            "vector_rank": 1,
        }
        self.assertTrue(self.service._should_vector_rank_promote(top, runner))

    def test_should_vector_rank_promote_false_for_large_gap(self):
        self.builder.vector_rank_rescue_enabled = True
        top = {
            "final_score": 0.84,
            "coverage": 0.86,
            "lexical": 0.84,
            "vector_rank": None,
        }
        runner = {
            "final_score": 0.80,
            "coverage": 0.90,
            "lexical": 0.84,
            "vector_rank": 1,
        }
        self.assertFalse(self.service._should_vector_rank_promote(top, runner))


if __name__ == "__main__":
    unittest.main()
