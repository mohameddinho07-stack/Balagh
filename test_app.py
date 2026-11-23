import unittest
from streamlit.testing.v1 import AppTest

def started():
 a=AppTest.from_file('app.py').run();a.button[0].click().run();return a


class AppFlowTests(unittest.TestCase):
    def test_playable_flows(self):
        a=started()
        a.button(key='inspect_E03').click().run()
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
        assert a.session_state['case'] is None
        assert 'detective_notes' not in a.session_state
        
        a=started()
        for e in ['E06','E07','E08']: a.button(key='inspect_'+e).click().run()
        next(x for x in a.selectbox if x.label=='مين اللي عملها؟').select('نادين مراد')
        for e in ['E06','E07','E08']: a.multiselect[0].select(e)
        a.checkbox[0].check()
        a.button(key='FormSubmitter:accusation-ثبّت الاتهام').click().run()
        assert a.session_state['investigation']['result']['success']
        assert not a.exception
        
        a=started();a.radio[0].set_value('🎮 العب مع صحابك').run()
        assert not a.exception
        assert any('لسه مش شغّال' in m.value for m in a.info)
        assert len(a.button)==0
        print('UI PASS: wrong accusation locks without revealing; opt-in reveal; clean reset; complete evidence win; multiplayer honest unavailable message')


    def test_ai_has_equal_choices_and_no_default(self):
        from unittest.mock import patch
        from ai_interrogation import ask_suspect as real_ask
        a = AppTest.from_file('app.py')
        a.secrets['GROQ_API_KEY'] = 'test'
        a.run(); a.button[0].click().run()
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
