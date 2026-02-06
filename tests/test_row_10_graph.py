import unittest

from neo4j import GraphDatabase

from cardio_graph.neo4j_utils.feedneo4jdb import AUTH, URI


class Row10GraphTests(unittest.TestCase):
    RULE_KEY = "_62_63/table_000.json:row_10::1"
    CONDITION_IDS = {"6121001", "250908004"}
    ACTION_ID = "275227003"

    @classmethod
    def setUpClass(cls):
        cls._driver = GraphDatabase.driver(URI, auth=AUTH)
        cls._driver.verify_connectivity()

    @classmethod
    def tearDownClass(cls):
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
            "RETURN [rec.class, rec.level]"
        )
        rec_props = self._fetch_single_value(query, rule=self.RULE_KEY)
        self._assert_verbose(
            query,
            ["Class I", "A"],
            rec_props,
            "Row_10 class and level must be preserved on the RecommendationNode.",
        )

    def test_decision_nodes_exist(self):
        query = "MATCH (dec:DecisionNode {rule_unique_id: $rule}) " "RETURN count(dec)"
        dec_count = self._fetch_single_value(query, rule=self.RULE_KEY)
        self._assert_verbose(
            query,
            2,
            dec_count,
            "Row_10 has two conditions, so we expect two DecisionNodes.",
        )

    def test_decisions_link_to_conditions(self):
        query = (
            "MATCH (dec:DecisionNode {rule_unique_id: $rule})"
            "-[:CHECKS_FOR|EVALUATES]->(c:Concept) "
            "RETURN DISTINCT c.snomed_id AS snomed_id"
        )
        linked_ids = self._fetch_set(query, "snomed_id", rule=self.RULE_KEY)
        self._assert_verbose(
            query,
            self.CONDITION_IDS,
            linked_ids,
            "Decision nodes must point at the two row_10 condition concepts.",
        )

    def test_recommendation_links_to_action(self):
        query = (
            "MATCH (rec:RecommendationNode {rule_unique_id: $rule})"
            "-[:RECOMMENDS_PROCEDURE]->(a:Concept) "
            "RETURN DISTINCT a.snomed_id AS snomed_id"
        )
        action_ids = self._fetch_set(query, "snomed_id", rule=self.RULE_KEY)
        self._assert_verbose(
            query,
            {self.ACTION_ID},
            action_ids,
            "Row_10 recommendation must link to myocardial revascularization.",
        )

    def test_decisions_result_in_recommendation(self):
        dec_query = (
            "MATCH (dec:DecisionNode {rule_unique_id: $rule}) "
            "RETURN DISTINCT dec.decision_id AS decision_id"
        )
        dec_ids = self._fetch_set(dec_query, "decision_id", rule=self.RULE_KEY)
        path_query = (
            "MATCH (dec:DecisionNode {rule_unique_id: $rule}) "
            "MATCH (rec:RecommendationNode {rule_unique_id: $rule}) "
            "WHERE (dec)-[:RESULTS_IN]->(rec) "
            "   OR (dec)-[:LEADS_TO*1..]->(:DecisionNode)-[:RESULTS_IN]->(rec) "
            "RETURN DISTINCT dec.decision_id AS decision_id"
        )
        results = self._fetch_set(path_query, "decision_id", rule=self.RULE_KEY)
        self._assert_verbose(
            path_query,
            dec_ids,
            results,
            "Each decision should reach the recommendation directly or via LEADS_TO.",
        )

    def test_condition_nodes_have_expected_labels(self):
        query = (
            "UNWIND $ids AS cid "
            "MATCH (c:Concept {snomed_id: cid}) "
            "RETURN cid AS snomed_id, labels(c) AS labels"
        )
        rows = self._fetch_rows(query, ids=list(self.CONDITION_IDS))
        labels_by_id = {row["snomed_id"]: set(row["labels"]) for row in rows}
        expected_keys = self.CONDITION_IDS
        actual_keys = set(labels_by_id.keys())
        self._assert_verbose(
            query,
            expected_keys,
            actual_keys,
            "Condition concepts must be present as Concept nodes.",
        )
        self.assertTrue(
            {"Concept", "ClinicalCondition"}.issubset(labels_by_id["6121001"])
        )
        self.assertTrue(
            {"Concept", "ClinicalParameter"}.issubset(labels_by_id["250908004"])
        )

    def test_action_node_has_expected_labels(self):
        query = "MATCH (c:Concept:Procedure {snomed_id: $cid}) RETURN count(c)"
        label_count = self._fetch_single_value(query, cid=self.ACTION_ID)
        self._assert_verbose(
            query,
            1,
            label_count,
            "Action concept must be labeled as a Procedure concept.",
        )


if __name__ == "__main__":
    unittest.main()
