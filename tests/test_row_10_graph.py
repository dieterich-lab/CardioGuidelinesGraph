import json
import os
import unittest
from pathlib import Path

from neo4j import GraphDatabase

from cardio_graph_core.neo4j.feedneo4jdb import AUTH as DEFAULT_AUTH
from cardio_graph_core.neo4j.feedneo4jdb import URI as DEFAULT_URI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR = Path(os.environ.get("CARDIO_GRAPH_DATA_DIR", DEFAULT_DATA_DIR))
GRAPH_DIR = Path(os.environ.get("CARDIO_GRAPH_GRAPH_DIR", DATA_DIR / "graph"))
HUMAN_READABLE_PATH = Path(
    os.environ.get(
        "CARDIO_GRAPH_ROW10_HUMAN_READABLE_PATH",
        GRAPH_DIR / "row_10_human_readable.json",
    )
)

URI = os.environ.get("CARDIO_GRAPH_NEO4J_URI", DEFAULT_URI)
AUTH = (
    os.environ.get("CARDIO_GRAPH_NEO4J_USER", DEFAULT_AUTH[0]),
    os.environ.get("CARDIO_GRAPH_NEO4J_PASSWORD", DEFAULT_AUTH[1]),
)


class Row10GraphTests(unittest.TestCase):
    RULE_KEY = "_62_63/table_000.json:row_10"
    EXPECTED_DECISION_COUNT = 3
    EXPECTED_DECISION_IDS = {
        "_62_63/table_000.json:row_10::g1::s1",
        "_62_63/table_000.json:row_10::g1::s2",
        "_62_63/table_000.json:row_10::g1::s3",
    }

    @classmethod
    def setUpClass(cls):
        if not HUMAN_READABLE_PATH.is_file():
            raise unittest.SkipTest(
                "Missing human-readable file: "
                + str(HUMAN_READABLE_PATH)
                + ". Set CARDIO_GRAPH_ROW10_HUMAN_READABLE_PATH."
            )
        try:
            cls._driver = GraphDatabase.driver(URI, auth=AUTH)
            cls._driver.verify_connectivity()
        except Exception as exc:
            raise unittest.SkipTest("Neo4j not available: " + str(exc)) from exc

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "_driver"):
            cls._driver.close()

    def _fetch_single_value(self, query, **params):
        with self._driver.session() as session:
            record = session.run(query, **params).single()
            return record[0] if record else None

    def _fetch_set(self, query, key, **params):
        with self._driver.session() as session:
            records = session.run(query, **params)
            return {row[key] for row in records if row[key] is not None}

    def _fetch_rows(self, query, **params):
        with self._driver.session() as session:
            return [row.data() for row in session.run(query, **params)]

    def _load_expected(self):
        with open(HUMAN_READABLE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _normalize(self, value):
        if value is None:
            return None
        return " ".join(str(value).strip().split()).lower()

    def _assert_verbose(self, query, expected, actual, health_note):
        print("\nQUERY:\n" + query)
        print("EXPECTED:\n" + str(expected))
        print("ACTUAL:\n" + str(actual))
        print("HEALTH NOTE:\n" + health_note)
        self.assertEqual(actual, expected)

    def test_recommendation_node_exists(self):
        query = (
            "MATCH (rec:RecommendationNode {rule_unique_id: $rule}) "
            "RETURN count(rec)"
        )
        rec_count = self._fetch_single_value(query, rule=self.RULE_KEY)
        self._assert_verbose(
            query,
            1,
            rec_count,
            "Row_10 must create exactly one RecommendationNode to anchor the rule.",
        )

    def test_recommendation_class_level(self):
        query = (
            "MATCH (rec:RecommendationNode {rule_unique_id: $rule}) "
            "RETURN [rec.strength, rec.level]"
        )
        rec_props = self._fetch_single_value(query, rule=self.RULE_KEY)
        self._assert_verbose(
            query,
            ["Class I", "A"],
            rec_props,
            "Row_10 class and level must be preserved on the RecommendationNode.",
        )

    def test_decision_nodes_exist(self):
        query = "MATCH (dec:DecisionNode {rule_unique_id: $rule}) RETURN count(dec)"
        dec_count = self._fetch_single_value(query, rule=self.RULE_KEY)
        self._assert_verbose(
            query,
            self.EXPECTED_DECISION_COUNT,
            dec_count,
            "Row_10 should include CCS, LVEF, and three-vessel disease decisions.",
        )

    def test_decisions_link_to_concepts(self):
        query = (
            "MATCH (dec:DecisionNode {rule_unique_id: $rule}) "
            "OPTIONAL MATCH (dec)-[:CHECKS_FOR|EVALUATES]->(c:Concept) "
            "OPTIONAL MATCH (dec)-[:CHECKS_FOR|EVALUATES]->(u:UnresolvedConcept) "
            "RETURN dec.decision_id AS decision_id, "
            "       count(DISTINCT c) + count(DISTINCT u) AS concept_count"
        )
        rows = self._fetch_rows(query, rule=self.RULE_KEY)
        decision_ids = {row["decision_id"] for row in rows}
        self._assert_verbose(
            query,
            self.EXPECTED_DECISION_IDS,
            decision_ids,
            "Row_10 should have the expected DecisionNodes (grounding ignored).",
        )
        for row in rows:
            self.assertGreaterEqual(
                row["concept_count"],
                1,
                "Each DecisionNode should link to at least one Concept node.",
            )

    def test_decision_concept_mapping_matches_expected(self):
        expected = self._load_expected()
        expected_conditions = {
            self._normalize(cond.get("entity_standardized_candidate"))
            for rule in expected.get("rules", [])
            for cond in rule.get("conditions", [])
        }
        expected_roles = {
            self._normalize(cond.get("entity_standardized_candidate")): cond.get("role")
            for rule in expected.get("rules", [])
            for cond in rule.get("conditions", [])
        }
        query = (
            "MATCH (dec:DecisionNode {rule_unique_id: $rule}) "
            "OPTIONAL MATCH (dec)-[r:CHECKS_FOR|EVALUATES]->(c:Concept) "
            "OPTIONAL MATCH (dec)-[ur:CHECKS_FOR|EVALUATES]->(u:UnresolvedConcept) "
            "RETURN dec.decision_id AS decision_id, "
            "       CASE WHEN r IS NOT NULL THEN type(r) ELSE type(ur) END AS rel_type, "
            "       coalesce(c.standardized, c.preferred_term, u.name) AS concept_name"
        )
        rows = [
            row
            for row in self._fetch_rows(query, rule=self.RULE_KEY)
            if row.get("concept_name")
        ]
        names = {self._normalize(row["concept_name"]) for row in rows}
        self._assert_verbose(
            query,
            expected_conditions,
            names,
            "DecisionNode concept names should match expected structure (grounding optional).",
        )
        for row in rows:
            name = self._normalize(row["concept_name"])
            role = expected_roles.get(name)
            if role == "ClinicalParameter":
                self.assertEqual(
                    row.get("rel_type"),
                    "EVALUATES",
                    "ClinicalParameter should use EVALUATES relation.",
                )
            elif role == "ClinicalCondition":
                self.assertEqual(
                    row.get("rel_type"),
                    "CHECKS_FOR",
                    "ClinicalCondition should use CHECKS_FOR relation.",
                )

    def test_decision_chain_reaches_recommendation(self):
        path_query = (
            "MATCH (rec:RecommendationNode {rule_unique_id: $rule}) "
            "MATCH (d1:DecisionNode {decision_id: $d1}) "
            "MATCH (d2:DecisionNode {decision_id: $d2}) "
            "MATCH (d3:DecisionNode {decision_id: $d3}) "
            "RETURN EXISTS((d1)-[:LEADS_TO]->(d2)) AS d1_to_d2, "
            "       EXISTS((d2)-[:LEADS_TO]->(d3)) AS d2_to_d3, "
            "       EXISTS((d3)-[:RESULTS_IN]->(rec)) AS d3_to_rec"
        )
        result = self._fetch_rows(
            path_query,
            rule=self.RULE_KEY,
            d1="_62_63/table_000.json:row_10::g1::s1",
            d2="_62_63/table_000.json:row_10::g1::s2",
            d3="_62_63/table_000.json:row_10::g1::s3",
        )
        self._assert_verbose(
            path_query,
            [{"d1_to_d2": True, "d2_to_d3": True, "d3_to_rec": True}],
            result,
            "DecisionNodes should chain via LEADS_TO and end at RecommendationNode.",
        )

    def test_recommendation_links_to_action(self):
        query = (
            "MATCH (rec:RecommendationNode {rule_unique_id: $rule})"
            "-[:RECOMMENDS_PROCEDURE|RECOMMENDS_USAGE]->(a:Concept) "
            "RETURN count(a)"
        )
        action_count = self._fetch_single_value(query, rule=self.RULE_KEY)
        self._assert_verbose(
            query,
            1,
            action_count,
            "RecommendationNode should link to at least one action Concept.",
        )

    def test_action_concept_matches_expected(self):
        expected = self._load_expected()
        expected_actions = {
            self._normalize(action.get("entity_standardized_candidate"))
            for rule in expected.get("rules", [])
            for action in rule.get("actions", [])
        }
        query = (
            "MATCH (rec:RecommendationNode {rule_unique_id: $rule})"
            "-[:RECOMMENDS_PROCEDURE|RECOMMENDS_USAGE]->(a:Concept) "
            "RETURN coalesce(a.standardized, a.preferred_term, a.name) AS name"
        )
        actual_actions = {
            self._normalize(row["name"])
            for row in self._fetch_rows(query, rule=self.RULE_KEY)
            if row.get("name")
        }
        self._assert_verbose(
            query,
            expected_actions,
            actual_actions,
            "Action concepts should match the human-readable structure.",
        )


if __name__ == "__main__":
    unittest.main()
