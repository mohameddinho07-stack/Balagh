import json,unittest
from game_engine import *
from dossier import *
from ai_interrogation import ask_suspect,AIUnavailable

class DossierTests(unittest.TestCase):
 def solve(self,cid):
  c=generate_case(cid);s=new_investigation()
  while len(s['discovered'])<len(evidence_cards(c)):
   for e in available_evidence(c,s):
    if e['id'] not in s['discovered']:inspect_evidence(c,s,e['id'])
  for p in c['characters']:
   for q in available_questions(p,s['discovered']):record_answer(c,s,p['id'],q['id'])
  return c,s
 def test_round_trip_canonical_and_budget(self):
  for cid in ['001','002','003']:
   c,s=self.solve(cid)
   for link in c.get('reasoning',[]):self.assertIsNotNone(link_evidence(c,s,link['evidence']))
   s['hints_used']=2
   raw=export_dossier(c,s,'تحقيقي الخاص')
   c2,s2,notes=import_dossier(raw)
   self.assertEqual(c,c2);self.assertEqual(notes,'تحقيقي الخاص')
   for key in ['discovered','interviews','hints_used','deductions']:self.assertEqual(set(s[key]) if key=='discovered' else s[key],set(s2[key]) if key=='discovered' else s2[key])
   self.assertNotEqual(s['attempt_id'],s2['attempt_id'])
   with self.assertRaises(AIUnavailable):ask_suspect(c2,s2,c2['characters'][0]['id'],'مين؟','test')
   finish_investigation(c,s,c['truth']['killer'],c['truth']['required_evidence'])
   _,s3,_=import_dossier(export_dossier(c,s))
   self.assertTrue(s3['finished']);self.assertTrue(s3['result']['success'])
 def test_bad_data(self):
  c=generate_case('002');s=new_investigation();base=json.loads(export_dossier(c,s))
  for patch in [{'case_id':[]},{'discovered':['E07']},{'discovered':['XXX']},{'questions':['s207']},{'deductions':['c201']},{'hints_used':True},{'hints_used':-1},{'notes':123},{'finished':'yes'},{'finished':True,'verdict':{'evidence':[[]],'suspect':[]}}]:
   with self.subTest(patch=patch):
    with self.assertRaises(ValueError):import_dossier(json.dumps(dict(base,**patch)))
  for raw in ['{}','[1]','null','bad',b'\xff', 'x'*100001, '['*2000+']'*2000, None]:
   with self.assertRaises(ValueError):import_dossier(raw)
 def test_links_cannot_unlock_or_duplicate(self):
  c=generate_case('002');s=new_investigation()
  with self.assertRaises(ValueError):link_evidence(c,s,['E01','E05'])
  c,s=self.solve('002');link_evidence(c,s,['E01','E05']);link_evidence(c,s,['E05','E01'])
  self.assertEqual(s['deductions'],['c201'])
  self.assertIsNone(link_evidence(c,s,['E01','E02']))
