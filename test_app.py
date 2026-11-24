import unittest
from streamlit.testing.v1 import AppTest

def started():
 a=AppTest.from_file('app.py');a.session_state['entry_phase']='game';a.run();next(x for x in a.button if x.label=='🚔 يلا نحقق').click().run();return a


class AppFlowTests(unittest.TestCase):
    def test_playable_flows(self):
        a=started()
        a.session_state['investigation']['discovered'].append('E03');a.run()
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
        
        a=started();a.radio[0].set_value('🎮 العب مع صحابك').run()
        assert not a.exception
        assert any('ربط الأوض مش جاهز' in m.value for m in a.info)
        assert all(x.label=='ارجع لاختيار القضية' for x in a.button)
        print('UI PASS: wrong accusation locks without revealing; opt-in reveal; clean reset; complete evidence win; room configuration safe fallback')


    def test_no_duplicate_legacy_presentations(self):
        a=started()
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
        room={'state':new_investigation(),'code':'TEST01','players':[{'name':'test','id':'p1'},{'name':'test2','id':'p2'}],'me':'p1','revision':0,'mode':'coop','notes':'','status':'active','proposal':None,'approvals':[]}
        with patch('room_client.rpc',return_value=room):
            a.radio(key='mode_choice').set_value('🎮 العب مع صحابك').run()
            self.assertEqual(len(a.session_state['solo_snapshot']),3)
            a.session_state['room_token']='test-token';a.run()
            self.assertTrue(a.radio(key='mode_choice').disabled)
            next(b for b in a.button if b.label=='اخرج من الأوضة على الجهاز ده').click().run()
            self.assertFalse(a.radio(key='mode_choice').disabled)
            a.radio(key='mode_choice').set_value('🔍 العب لوحدك').run()
            self.assertEqual(a.session_state['detective_notes'],'solo private')
            self.assertFalse(a.exception)

    def test_ai_has_equal_choices_and_no_default(self):
        from unittest.mock import patch
        from ai_interrogation import ask_suspect as real_ask
        a = AppTest.from_file('app.py')
        a.secrets['GROQ_API_KEY'] = 'test'
        a.session_state['entry_phase'] = 'game'
        a.run(); next(x for x in a.button if x.label=='🚔 يلا نحقق').click().run()
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
