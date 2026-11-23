import unittest
from game_engine import *

class MultiCaseTests(unittest.TestCase):
    def test_complete_paths_and_guess_rejection(self):
        for cid in ['001','002','003']:
            c=generate_case(cid);s=new_investigation()
            with self.assertRaises(ValueError):evaluate_accusation(c,c['truth']['killer'],[],[])
            pending={e['id'] for e in evidence_cards(c)}
            while pending:
                options=[e for e in available_evidence(c,s) if e['id'] in pending]
                self.assertTrue(options,'Unreachable evidence cycle in '+cid)
                for e in options:inspect_evidence(c,s,e['id']);pending.remove(e['id'])
            for p in c['characters']:
                for q in available_questions(p,s['discovered']):record_answer(c,s,p['id'],q['id'])
            self.assertTrue(finish_investigation(c,s,c['truth']['killer'],c['truth']['required_evidence'])['success'])
            with self.assertRaises(ValueError):inspect_evidence(c,s,'E01')
    def test_locks_and_copies(self):
        c=generate_case('003');s=new_investigation()
        with self.assertRaises(ValueError):inspect_evidence(c,s,'E07')
        with self.assertRaises(ValueError):record_answer(c,s,'dalia','b307')
        self.assertNotIn('E07',{e['id'] for e in available_evidence(c,s)})
        c['truth']['killer']='tampered'
        self.assertEqual(generate_case('003')['truth']['killer'],'داليا أمين')
        self.assertNotEqual(new_investigation()['attempt_id'],new_investigation()['attempt_id'])
    def test_all_references_and_unique_topics(self):
        for cid in ['001','002','003']:
            c=generate_case(cid);ids={e['id'] for e in evidence_cards(c)};qids=[]
            self.assertEqual(len(ids),len(evidence_cards(c)))
            for e in evidence_cards(c):self.assertTrue(set(e.get('requires',[]))<=ids)
            for p in c['characters']:
                for q in p['interviews']:
                    qids.append(q['id']);self.assertTrue(set(q.get('requires',[]))<=ids)
            self.assertEqual(len(qids),len(set(qids)))
            self.assertTrue(set(c['truth']['required_evidence'])<=ids)
            self.assertIn(c['truth']['killer'],[p['name'] for p in c['characters']])
            for link in c.get('reasoning',[]):self.assertTrue(set(link['evidence'])<=ids)
    def test_generic_ai_uses_new_case_topics(self):
        from ai_interrogation import build_request,ask_suspect
        for cid in ['002','003']:
            c=generate_case(cid);s=new_investigation()
            for i,p in enumerate(c['characters']):
                question=p['interviews'][0]
                payload=build_request(c,s,question['question'],p['id'])
                self.assertIn(question['id'],payload['response_format']['json_schema']['schema']['properties']['topic']['enum'])
                turn=ask_suspect(c,s,p['id'],question['question'],'test',selector=lambda a,b:question['id'],now=100+i*10)
                self.assertEqual(turn['answer'],question['answer'])
