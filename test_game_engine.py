import unittest
from game_engine import (generate_case, new_investigation, evidence_cards,
                         available_questions, record_answer, evaluate_accusation,
                         finish_investigation)


class CaseTests(unittest.TestCase):
    def setUp(self):
        self.case = generate_case()
        self.state = new_investigation()
        self.ids = [e["id"] for e in evidence_cards(self.case)]

    def test_evidence_ids_are_unique(self):
        self.assertEqual(len(self.ids), len(set(self.ids)))

    def test_case_copies_are_independent(self):
        self.case["characters"][0]["name"] = "changed"
        self.assertNotEqual(generate_case()["characters"][0]["name"], "changed")

    def test_solution_is_a_suspect(self):
        self.assertIn(self.case["truth"]["killer"], [s["name"] for s in self.case["characters"]])

    def test_all_question_dependencies_exist(self):
        for suspect in self.case["characters"]:
            for question in suspect["interviews"]:
                self.assertTrue(set(question.get("requires", [])) <= set(self.ids))

    def test_question_ids_are_unique(self):
        ids = [q["id"] for s in self.case["characters"] for q in s["interviews"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_questions_unlock_only_after_evidence(self):
        nadine = self.case["characters"][3]
        self.assertNotIn("n3", [q["id"] for q in available_questions(nadine, [])])
        self.assertNotIn("n3", [q["id"] for q in available_questions(nadine, ["E06"])])
        self.assertIn("n3", [q["id"] for q in available_questions(nadine, ["E06", "E07"])])

    def test_cannot_invoke_locked_question(self):
        with self.assertRaises(ValueError):
            record_answer(self.case, self.state, "nadine", "n3")

    def test_interview_log_persists_without_duplicates(self):
        record_answer(self.case, self.state, "nadine", "n1")
        record_answer(self.case, self.state, "nadine", "n1")
        record_answer(self.case, self.state, "aser", "a1")
        self.assertEqual(len(self.state["interviews"]), 2)
        self.assertNotEqual(self.state["interviews"][0]["answer"], self.state["interviews"][1]["answer"])

    def test_correct_accusation_requires_full_chain(self):
        for missing in ["E06", "E07", "E08"]:
            selected = [e for e in ["E06", "E07", "E08"] if e != missing]
            self.assertFalse(evaluate_accusation(self.case, "نادين مراد", selected, self.ids)["success"])
        self.assertTrue(evaluate_accusation(self.case, "نادين مراد", ["E06", "E07", "E08"], self.ids)["success"])

    def test_wrong_suspect_never_wins(self):
        for suspect in ["آسر منصور", "ليلى الديب", "يوسف بيومي"]:
            self.assertFalse(evaluate_accusation(self.case, suspect, self.ids, self.ids)["success"])

    def test_cannot_submit_uninspected_or_unknown_evidence(self):
        for evidence, discovered in [(["E06"], []), (["FAKE"], ["FAKE"]), ([], self.ids)]:
            with self.assertRaises(ValueError):
                evaluate_accusation(self.case, "نادين مراد", evidence, discovered)

    def test_unknown_suspect_and_question_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_accusation(self.case, "unknown", ["E01"], self.ids)
        with self.assertRaises(ValueError):
            record_answer(self.case, self.state, "unknown", "a1")

    def test_final_decision_locks_accusations_and_interviews(self):
        self.state["discovered"] = self.ids
        finish_investigation(self.case, self.state, "يوسف بيومي", ["E03"])
        self.assertTrue(self.state["finished"])
        with self.assertRaises(ValueError):
            finish_investigation(self.case, self.state, "نادين مراد", self.ids)
        with self.assertRaises(ValueError):
            record_answer(self.case, self.state, "nadine", "n1")
        self.assertNotIn("killer", self.state["result"])
        self.assertNotIn("explanation", self.state["result"])

    def test_new_attempt_is_clean(self):
        self.state["discovered"].append("E01")
        self.assertEqual(new_investigation()["discovered"], [])


if __name__ == "__main__":
    unittest.main()
