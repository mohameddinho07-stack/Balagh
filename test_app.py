import unittest
from streamlit.testing.v1 import AppTest

def skip_intro(a):
    for b in a.button:
        if b.label=='تخطّى':
            b.click().run();break
    return a


def started():
 a=AppTest.from_file('app.py');a.session_state['entry_phase']='game';a.run();next(x for x in a.button if x.label=='🚔 يلا نحقق').click().run()
 a=skip_intro(a);return a


class AppFlowTests(unittest.TestCase):
    def test_playable_flows(self):
        a=started()
        a.session_state['investigation']['discovered'].extend(['E01','E02','E03']);a.run()
        next(x for x in a.selectbox if x.label=='مين اللي عملها؟').select('يوسف بيومي')
        a.multiselect[0].select('E03')
        a.checkbox[0].check()
        a.button(key='FormSubmitter:accusation-ثبّت الاتهام').click().run()
        assert not a.exception
        assert a.session_state['investigation']['finished']
        assert not any('الحل:' in t.value for t in a.subheader)
        a.checkbox(key='reveal_solution').check().run()
        assert any('الحل: نادين' in t.value for t in a.subheader)
        next(b for b in a.button if b.label=='نجرّب من الأول').click().run()
        assert a.session_state['case']['id']=='001'
        assert not a.session_state['investigation']['discovered']
        assert not a.session_state.get('detective_notes','')
        
        a=started()
        a.session_state['investigation']['discovered'].extend(['E06','E07','E08']);a.run()
        next(x for x in a.selectbox if x.label=='مين اللي عملها؟').select('نادين مراد')
        for e in ['E06','E07','E08']: a.multiselect[0].select(e)
        a.checkbox[0].check()
        a.button(key='FormSubmitter:accusation-ثبّت الاتهام').click().run()
        assert a.session_state['investigation']['result']['success']
        assert not a.exception
        
        a=started();a.radio[0].set_value('🤝 تعاون').run()
        assert not a.exception
        assert any('ربط الأوض مش جاهز' in m.value for m in a.info)
        assert all(x.label=='ارجع لاختيار القضية' for x in a.button)
        print('UI PASS: wrong accusation locks without revealing; opt-in reveal; clean reset; complete evidence win; room configuration safe fallback')


    def test_no_duplicate_legacy_presentations(self):
        a=started()
        a.session_state['investigation']['discovered']=['E01','E02','E03'];a.run()
        assert not any('نسخة نصية' in x.value or 'نسمع أقوالهم' in x.value for x in a.subheader)
        assert not any(x.key.startswith('inspect_') for x in a.button if x.key)
        assert any('اسأل بطريقتك' in x.value for x in a.subheader)
        assert any('نوتة التحقيق' in x.value for x in a.subheader)
        assert any('مين المتهم' in x.value for x in a.subheader)

    def test_solution_reveal_does_not_carry_between_cases(self):
        from game_engine import generate_case,new_investigation
        a=AppTest.from_file('app.py')
        a.session_state['entry_phase']='choose'
        a.session_state['reveal_solution']=True
        a.session_state['case']=generate_case('001')
        a.session_state['investigation']=new_investigation()
        a.run();a.button(key='open_case_002').click().run()
        self.assertFalse(a.session_state.get('reveal_solution',False))
        self.assertEqual(a.session_state['case']['id'],'002')
        self.assertEqual(a.session_state['investigation']['discovered'],[])
        self.assertFalse(a.exception)

    def test_room_switch_preserves_solo_notes(self):
        from unittest.mock import patch
        from game_engine import new_investigation
        a=started();a.session_state['detective_notes']='solo private';a.run()
        a.secrets.update(SUPABASE_URL='https://test.invalid',SUPABASE_KEY='test')
        room={'state':new_investigation(),'code':'TEST01','players':[{'name':'test','id':'p1','unit':'0'},{'name':'test2','id':'p2','unit':'0'}],'me':'p1','revision':0,'mode':'coop','notes':'','status':'active','proposal':None,'approvals':[],'case_id':'001','started':True,'host':'p1','team_count':1,'team_size':1,'max_players':2,'winner_unit':None,'my_unit':'0','unit_size':2,'urev':0,'unit_done':{}}
        with patch('room_client.rpc',return_value=room):
            a.radio(key='mode_choice').set_value('🤝 تعاون').run()
            self.assertEqual(len(a.session_state['solo_snapshot']),3)
            a.session_state['room_token']='test-token';a.run()
            self.assertTrue(a.radio(key='mode_choice').disabled)
            next(b for b in a.button if b.label=='اخرج من الأوضة على الجهاز ده').click().run()
            self.assertFalse(a.radio(key='mode_choice').disabled)
            a.radio(key='mode_choice').set_value('🔍 العب لوحدك').run()
            self.assertEqual(a.session_state['detective_notes'],'solo private')
            self.assertFalse(a.exception)

    def test_room_exit_to_picker_never_archives_room_as_solo(self):
        from unittest.mock import patch
        from game_engine import new_investigation
        a=started();a.session_state['detective_notes']='solo note';a.session_state['investigation']['discovered']=['E01'];a.run()
        a.secrets.update(SUPABASE_URL='https://test.invalid',SUPABASE_KEY='test')
        room={'state':new_investigation(),'code':'TEST02','players':[{'name':'test','id':'p1','unit':'0'},{'name':'test2','id':'p2','unit':'0'}],'me':'p1','revision':0,'mode':'coop','notes':'','status':'active','proposal':None,'approvals':[],'case_id':'001','started':True,'host':'p1','team_count':1,'team_size':1,'max_players':2,'winner_unit':None,'my_unit':'0','unit_size':2,'urev':0,'unit_done':{}}
        room['state']['discovered']=['E02','E03']
        with patch('room_client.rpc',return_value=room):
            a.radio(key='mode_choice').set_value('🤝 تعاون').run()
            a.session_state['room_token']='test-token';a.run()
            next(b for b in a.button if b.label=='اخرج من الأوضة على الجهاز ده').click().run()
            next(b for b in a.button if b.label=='ارجع لاختيار القضية').click().run()
            a.button(key='open_case_001').click().run()
            self.assertEqual(a.session_state['investigation']['discovered'],['E01'])
            self.assertEqual(a.session_state['detective_notes'],'solo note')
            self.assertFalse(a.exception)

    def test_new_attempt_has_no_stale_final_confirmation(self):
        a=started();a.session_state['investigation']['discovered']=['E01','E02','E03'];a.run()
        next(x for x in a.selectbox if x.label=='مين اللي عملها؟').select('يوسف بيومي')
        a.multiselect[0].select('E03');a.checkbox[0].check()
        a.button(key='FormSubmitter:accusation-ثبّت الاتهام').click().run()
        next(b for b in a.button if b.label=='نجرّب من الأول').click().run()
        a.session_state['investigation']['discovered']=['E01','E02','E03'];a.run()
        self.assertIsNone(next(x for x in a.selectbox if x.label=='مين اللي عملها؟').value)
        self.assertFalse(next(x for x in a.checkbox if x.label.startswith('أيوه، ده')).value)
        self.assertEqual(a.multiselect[0].value,[])

    def test_ai_has_equal_choices_and_no_default(self):
        from unittest.mock import patch
        from ai_interrogation import ask_suspect as real_ask
        a = AppTest.from_file('app.py')
        a.secrets['GROQ_API_KEY'] = 'test'
        a.session_state['entry_phase'] = 'game'
        a.run(); next(x for x in a.button if x.label=='🚔 يلا نحقق').click().run(); skip_intro(a)
        a.session_state['investigation']['discovered']=['E01'];a.run()
        selector = a.selectbox(key='ai_suspect')
        assert selector.value is None
        assert selector.options == ['آسر منصور','ليلى الديب','يوسف بيومي','نادين مراد']
        assert a.button(key='FormSubmitter:suspect_ai-اسأل').disabled
        for i, sid in enumerate(['aser','layla','youssef','nadine']):
            a.selectbox(key='ai_suspect').select(sid).run()
            a.text_input[0].set_value('اسمك وشغلك إيه؟')
            def answer(c,s,chosen,q,key):
                return real_ask(c,s,chosen,q,key,selector=lambda p,k:'identity',now=100+i*10)
            with patch('ai_interrogation.ask_suspect', side_effect=answer):
                a.button(key='FormSubmitter:suspect_ai-اسأل').click().run()
            assert not a.exception
        assert {t['suspect_id'] for t in a.session_state['investigation']['ai_interviews']} == {'aser','layla','youssef','nadine'}

if __name__ == "__main__":
    unittest.main()


class PilotTests(unittest.TestCase):
    def test_intro_is_short_skippable_and_has_no_scene_until_done(self):
        a=AppTest.from_file('app.py');a.session_state['entry_phase']='game';a.run()
        next(x for x in a.button if x.label=='🚔 يلا نحقق').click().run()
        self.assertTrue(any(b.label=='تخطّى' for b in a.button))
        self.assertTrue(any(b.label=='كمّل' for b in a.button))
        next(b for b in a.button if b.label=='كمّل').click().run()
        next(b for b in a.button if b.label=='كمّل').click().run()
        self.assertTrue(any(b.label=='ابدأ التحقيق' for b in a.button))
        next(b for b in a.button if b.label=='ابدأ التحقيق').click().run()
        self.assertFalse(any(b.label=='تخطّى' for b in a.button))
        self.assertFalse(a.exception)

    def test_confrontation_rule_is_server_data_not_a_shortcut(self):
        import pilot, game_engine as g, cases_extra as c
        case=c.CASE_002;st=g.new_investigation()
        self.assertEqual(pilot.resolve_confront(case,st,'bassem','s204','E05')[0],'error')
        for e in ('E01','E05'):g.inspect_evidence(case,st,e)
        g.record_answer(case,st,'bassem','s204')
        self.assertEqual(pilot.resolve_confront(case,st,'bassem','s204','E01')[0],'wrong')
        kind,q=pilot.resolve_confront(case,st,'bassem','s204','E05')
        self.assertEqual((kind,q['id']),('unlock','s205'))
        g.record_answer(case,st,'bassem','s205')
        self.assertEqual(pilot.resolve_confront(case,st,'bassem','s204','E05')[0],'done')
        # Missing prerequisite evidence cannot be bypassed by the pairing.
        st2=g.new_investigation();g.inspect_evidence(case,st2,'E01');g.inspect_evidence(case,st2,'E02');g.inspect_evidence(case,st2,'E03')
        g.record_answer(case,st2,'bassem','s204')
        for e in ('E06',):g.inspect_evidence(case,st2,e)
        st2['interviews'].append(dict(suspect='باسم',question_id='s205',question='',answer=''))
        self.assertEqual(pilot.resolve_confront(case,st2,'bassem','s205','E06')[0],'unlock')

    def test_every_case_has_intro_and_mood(self):
        import pilot
        for cid in ('001','002','003'):
            self.assertTrue(2<=len(pilot.intro_beats(cid))<=4)
            self.assertTrue(pilot.mood(cid))

    def test_confrontation_targets_are_not_plain_menu_items(self):
        import pilot
        self.assertEqual(pilot.confront_only('002'),{'s205','s206','s207','s214'})
        self.assertEqual(pilot.confront_only('001'),set())


class NextStepTests(unittest.TestCase):
    def test_guide_walks_every_case_and_never_quotes_the_solution(self):
        import game_engine as g, pilot
        for cid in ['001', '002', '003']:
            c = g.generate_case(cid); st = g.new_investigation()
            seen = []
            for _ in range(60):
                h, d, n = pilot.next_step(c, st, g.evidence_cards, g.available_evidence, g.available_questions)
                self.assertNotIn(c['truth']['explanation'][:30], h + d)
                seen.append(h)
                if h.startswith('افحص'):
                    ev = [e for e in g.available_evidence(c, st) if e['id'] not in st['discovered']]
                    g.inspect_evidence(c, st, ev[0]['id']); continue
                hit = False
                for ch in c['characters']:
                    for q in g.available_questions(ch, st['discovered']):
                        if q['id'] not in {x['question_id'] for x in st['interviews']} and q['id'] not in pilot.confront_only(cid):
                            g.record_answer(c, st, ch['id'], q['id']); hit = True; break
                    if hit: break
                if not hit: break
            self.assertTrue(seen[0].startswith('افحص'))
            self.assertEqual(len(st['discovered']), len(g.evidence_cards(c)))
