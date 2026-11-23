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

class AllSuspectsTests(unittest.TestCase):
    def test_every_suspect_really_answers(self):
        from ai_interrogation import ask_suspect
        case = generate_case()
        for suspect in case['characters']:
            with self.subTest(suspect=suspect['id']):
                state = new_investigation()
                first = suspect['interviews'][0]
                turn = ask_suspect(case, state, suspect['id'], 'سؤال', 'test',
                                   selector=lambda p,k: first['id'], now=100)
                self.assertEqual(turn['answer'], first['answer'])
                self.assertEqual(turn['suspect'], suspect['name'])
                self.assertEqual(state['interviews'][0]['suspect'], suspect['name'])

    def test_all_gates_and_other_suspect_topics(self):
        from ai_interrogation import ask_suspect
        case = generate_case()
        for suspect in case['characters']:
            state = new_investigation()
            p = build_request(case, state, 'سؤال', suspect['id'])
            allowed = p['response_format']['json_schema']['schema']['properties']['topic']['enum']
            for other in case['characters']:
                if other['id'] != suspect['id']:
                    self.assertTrue(set(q['id'] for q in other['interviews']).isdisjoint(allowed))
            for question in suspect['interviews']:
                if question.get('requires'):
                    self.assertNotIn(question['id'], allowed)
                    state = new_investigation()
                    state['discovered'] = question['requires']
                    result = ask_suspect(case,state,suspect['id'],'سؤال','test',
                                         selector=lambda p,k:question['id'],now=100)
                    self.assertEqual(result['answer'], question['answer'])

    def test_history_repeat_and_context_are_separate(self):
        from ai_interrogation import ask_suspect
        case = generate_case(); state = new_investigation()
        a = ask_suspect(case,state,'aser','سؤال آسر','test',selector=lambda p,k:'a1',now=100)
        b = ask_suspect(case,state,'layla','سؤال ليلى','test',selector=lambda p,k:'l1',now=110)
        text = str(build_request(case,state,'كرر','aser'))
        self.assertIn('سؤال آسر',text); self.assertNotIn('سؤال ليلى',text)
        repeated = ask_suspect(case,state,'aser','كرر','test',selector=lambda p,k:'repeat',now=120)
        self.assertEqual(repeated['answer'], a['answer'])
        self.assertNotEqual(repeated['answer'], b['answer'])
