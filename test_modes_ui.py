import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from game_engine import new_investigation, CASE_REGISTRY
from gen_rooms_sql import render


def room(**kw):
    base = {'state': new_investigation(), 'code': 'T1', 'players': [{'name': 'أ', 'id': 1, 'unit': 't1'}, {'name': 'ب', 'id': 2, 'unit': 't2'}],
            'me': 1, 'revision': 0, 'mode': 'team', 'notes': '', 'status': 'playing', 'proposal': None, 'approvals': [], 'case_id': '002',
            'started': False, 'host': 1, 'team_count': 2, 'team_size': 2, 'max_players': 4, 'winner_unit': None, 'my_unit': 't1',
            'unit_size': 2, 'urev': 0, 'unit_done': {}}
    base.update(kw)
    return base


def app(mode):
    a = AppTest.from_file('app.py'); a.session_state['entry_phase'] = 'choose'; a.run()
    a.button(key='open_case_002').click().run()
    a.secrets.update(SUPABASE_URL='https://test.invalid', SUPABASE_KEY='k')
    a.radio(key='mode_choice').set_value(mode).run()
    return a


class ModesUI(unittest.TestCase):
    def test_generated_sql_is_current(self):
        with open('rooms_v2.sql', encoding='utf-8') as f:
            self.assertEqual(f.read(), render())  # run gen_rooms_sql.py after adding a case

    def test_new_case_can_pick_every_mode(self):
        for mode in ['🤝 تعاون', '🏁 سباق فردي', '⚔️ سباق فرق']:
            a = app(mode)
            self.assertFalse(a.exception)
            self.assertFalse(a.radio(key='mode_choice').disabled)

    def test_team_lobby_and_start(self):
        a = app('⚔️ سباق فرق')
        with patch('room_client.rpc', return_value=room()):
            a.session_state['room_token'] = 'x'; a.run()
            self.assertFalse(a.exception)
            self.assertTrue(any(b.label == 'ابدأ السباق' for b in a.button))
            self.assertTrue(any('الفريق ١' in m.value for m in a.markdown))
            self.assertEqual(a.session_state['case']['id'], '002')

    def test_waiting_player_has_no_start_and_case_follows_room(self):
        a = app('🏁 سباق فردي')
        with patch('room_client.rpc', return_value=room(mode='race', me=2, my_unit='t2', case_id='003')):
            a.session_state['room_token'] = 'x'; a.run()
            self.assertFalse(any(b.label == 'ابدأ السباق' for b in a.button))
            self.assertEqual(a.session_state['case']['id'], '003')

    def test_started_team_room_plays_with_team_approval_ui(self):
        a = app('⚔️ سباق فرق')
        r = room(started=True, proposal={'suspect': 'باسم', 'evidence': ['E06']}, approvals=[2])
        r['state']['discovered'] = ['E06']
        with patch('room_client.rpc', return_value=r):
            a.session_state['room_token'] = 'x'; a.run()
            self.assertFalse(a.exception)
            self.assertTrue(any('موافقات' in c.value for c in a.caption))

if __name__ == '__main__':
    unittest.main()
