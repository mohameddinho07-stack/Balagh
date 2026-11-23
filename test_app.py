import unittest
from streamlit.testing.v1 import AppTest

def started():
 a=AppTest.from_file('app.py').run();a.button[0].click().run();return a


class AppFlowTests(unittest.TestCase):
    def test_playable_flows(self):
        a=started()
        a.button(key='inspect_E03').click().run()
        a.selectbox[0].select('يوسف بيومي')
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
        a.selectbox[0].select('نادين مراد')
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


if __name__ == "__main__":
    unittest.main()
