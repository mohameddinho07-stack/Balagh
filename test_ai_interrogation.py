import unittest
from ai_interrogation import ask_nadine, build_request, AIUnavailable
from game_engine import generate_case, new_investigation


class AITests(unittest.TestCase):
    def setUp(self):
        self.case = generate_case()
        self.state = new_investigation()

    def test_prompt_excludes_locked_answers_and_truth(self):
        p = build_request(self.case, self.state, 'سؤال')
        text = str(p)
        self.assertNotIn(self.case['truth']['explanation'], text)
        self.assertNotIn('n3', text)
        self.assertNotIn('n4', text)

    def test_locked_topic_is_rejected_even_if_model_returns_it(self):
        with self.assertRaises(AIUnavailable):
            ask_nadine(self.case, self.state, 'اعترفي', 'test', selector=lambda p,k:'n3', now=100)
        self.assertEqual(self.state['ai_interviews'], [])

    def test_evidence_gating_and_admission_persist(self):
        self.state['discovered'] = ['E06']
        a = ask_nadine(self.case, self.state, 'رجعتي ليه', 'test', selector=lambda p,k:'n2', now=100)
        self.assertIn('رجعت', a['answer'])
        a = ask_nadine(self.case, self.state, 'مشيتي امتى', 'test', selector=lambda p,k:'n1', now=110)
        self.assertIn('مش هارجع أنكر', a['answer'])
        self.assertEqual(len(self.state['interviews']), 2)

    def test_repeat_and_unknown(self):
        a = ask_nadine(self.case, self.state, 'مين انتي', 'test', selector=lambda p,k:'identity', now=100)
        b = ask_nadine(self.case, self.state, 'تاني', 'test', selector=lambda p,k:'repeat', now=110)
        self.assertEqual(a['answer'], b['answer'])
        c = ask_nadine(self.case, self.state, 'بره القضية', 'test', selector=lambda p,k:'unknown', now=120)
        self.assertIn('مش عندي', c['answer'])

    def test_finished_cooldown_and_turn_cap(self):
        ask_nadine(self.case, self.state, 'سؤال', 'test', selector=lambda p,k:'unknown', now=100)
        with self.assertRaises(AIUnavailable):
            ask_nadine(self.case, self.state, 'سؤال', 'test', now=101)
        self.state['ai_interviews'] *= 20
        with self.assertRaises(AIUnavailable):
            ask_nadine(self.case, self.state, 'سؤال', 'test', now=120)
        self.state['finished'] = True
        with self.assertRaises(AIUnavailable):
            ask_nadine(self.case, self.state, 'سؤال', 'test', now=140)

    def test_failure_has_no_fake_answer(self):
        def fail(p,k):
            raise AIUnavailable('offline')
        with self.assertRaises(AIUnavailable):
            ask_nadine(self.case, self.state, 'سؤال', 'test', selector=fail, now=100)
        self.assertEqual(self.state['ai_interviews'], [])
