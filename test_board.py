"""Investigation board pilot: pure rules, dossier roundtrip, catalog export, solo UI."""
import json
import unittest
from unittest.mock import patch

from game_engine import generate_case, new_investigation, inspect_evidence, record_answer, finish_investigation
import board as wall
from pilot import resolve_confront


def played():
    """Case 001 with E06+E07 examined and nadine's first answer heard."""
    case = generate_case('001')
    state = new_investigation()
    for e in ['E06', 'E07']:
        inspect_evidence(case, state, e)
    record_answer(case, state, 'nadine', 'n1')
    return case, state


class BoardRules(unittest.TestCase):
    def test_pilot_gate(self):
        self.assertTrue(wall.board_supported(generate_case('001')))
        self.assertFalse(wall.board_supported(generate_case('002')))
        case, state = generate_case('002'), new_investigation()
        with self.assertRaises(ValueError):
            wall.board_action(case, state, {'do': 'pin', 'card': 'E01'})

    def test_cards_come_from_earned_progress_only(self):
        case, state = played()
        ids = {c['id'] for c in wall.board_cards(case, state)}
        self.assertIn('E06', ids)
        self.assertIn('n1', ids)
        self.assertNotIn('E05', ids)
        self.assertNotIn('n2', ids)
        with self.assertRaises(ValueError):
            wall.board_action(case, state, {'do': 'pin', 'card': 'E05'})
        with self.assertRaises(ValueError):
            wall.board_action(case, state, {'do': 'pin', 'card': 'n2'})

    def test_pin_unpin_and_placement_cleanup(self):
        case, state = played()
        wall.board_action(case, state, {'do': 'pin', 'card': 'E06'})
        wall.board_action(case, state, {'do': 'place', 'card': 'E06', 'slot': '22:30'})
        wall.board_action(case, state, {'do': 'unpin', 'card': 'E06'})
        board = wall.board_state(state)
        self.assertEqual(board['pins'], [])
        self.assertEqual(board['placed'], {})

    def test_place_needs_pin_and_known_slot(self):
        case, state = played()
        with self.assertRaises(ValueError):
            wall.board_action(case, state, {'do': 'place', 'card': 'E06', 'slot': '22:30'})
        wall.board_action(case, state, {'do': 'pin', 'card': 'E06'})
        with self.assertRaises(ValueError):
            wall.board_action(case, state, {'do': 'place', 'card': 'E06', 'slot': '25:99'})
        wall.board_action(case, state, {'do': 'place', 'card': 'E06', 'slot': '23:00'})
        self.assertEqual(wall.board_state(state)['placed'], {'E06': '23:00'})
        wall.board_action(case, state, {'do': 'unplace', 'card': 'E06'})
        self.assertEqual(wall.board_state(state)['placed'], {})

    def test_link_holds_open_and_dedupe(self):
        case, state = played()
        for c in ['E06', 'E07', 'n1']:
            wall.board_action(case, state, {'do': 'pin', 'card': c})
        # Unpinned cards cannot be linked.
        case2, state2 = played()
        with self.assertRaises(ValueError):
            wall.board_action(case2, state2, {'do': 'link', 'cards': ['E06', 'E07']})
        # Authored deduction holds.
        match = wall.board_action(case, state, {'do': 'link', 'cards': ['E07', 'E06']})
        self.assertEqual(match['id'], 'c102')
        self.assertEqual(match['kind'], 'deduction')
        # Authored confrontation pair holds.
        match = wall.board_action(case, state, {'do': 'link', 'cards': ['n1', 'E06']})
        self.assertEqual(match['kind'], 'confront')
        self.assertEqual(match['unlocks'], 'n2')
        # Same pair twice is refused.
        with self.assertRaises(ValueError):
            wall.board_action(case, state, {'do': 'link', 'cards': ['E06', 'n1']})
        # A pair with no authored reading stays open, nothing lost.
        match = wall.board_action(case, state, {'do': 'link', 'cards': ['n1', 'E07']})
        self.assertIsNone(match)
        board = wall.board_state(state)
        self.assertEqual([t['status'] for t in board['theories']], ['holds', 'holds', 'open'])
        self.assertEqual(board['theories'][1]['theory_id'], 'cf_n1')
        # Unlink removes by index.
        wall.board_action(case, state, {'do': 'unlink', 'index': 2})
        self.assertEqual(len(wall.board_state(state)['theories']), 2)
        with self.assertRaises(ValueError):
            wall.board_action(case, state, {'do': 'unlink', 'index': 9})

    def test_three_card_deduction_holds(self):
        case, state = played()
        for e in ['E08', 'E09']:
            inspect_evidence(case, state, e)
        for c in ['E07', 'E08', 'E09']:
            wall.board_action(case, state, {'do': 'pin', 'card': c})
        match = wall.board_action(case, state, {'do': 'link', 'cards': ['E09', 'E07', 'E08']})
        self.assertEqual(match['id'], 'c103')

    def test_theory_card_unlocks_the_payoff_answer(self):
        case, state = played()
        for c in ['E06', 'n1']:
            wall.board_action(case, state, {'do': 'pin', 'card': c})
        wall.board_action(case, state, {'do': 'link', 'cards': ['n1', 'E06']})
        entry = wall.board_state(state)['theories'][0]
        theory = wall.theory_lookup(case, entry)
        self.assertEqual(theory['person'], 'nadine')
        kind, out = resolve_confront(case, state, theory['person'], theory['statement'], theory['evidence'])
        self.assertEqual(kind, 'unlock')
        record_answer(case, state, 'nadine', out['id'])
        self.assertIn('n2', {x['question_id'] for x in state['interviews']})
        kind, out = resolve_confront(case, state, theory['person'], theory['statement'], theory['evidence'])
        self.assertEqual(kind, 'done')

    def test_open_theory_costs_nothing(self):
        case, state = played()
        for c in ['E07', 'n1']:
            wall.board_action(case, state, {'do': 'pin', 'card': c})
        wall.board_action(case, state, {'do': 'link', 'cards': ['n1', 'E07']})
        before = json.dumps(state, sort_keys=True, ensure_ascii=False)
        kind, out = resolve_confront(case, state, 'nadine', 'n1', 'E07')
        self.assertEqual(kind, 'wrong')
        self.assertEqual(json.dumps(state, sort_keys=True, ensure_ascii=False), before)

    def test_finished_blocks_board_actions(self):
        case, state = played()
        inspect_evidence(case, state, 'E08')
        finish_investigation(case, state, 'نادين مراد', ['E06', 'E07', 'E08'])
        with self.assertRaises(ValueError):
            wall.board_action(case, state, {'do': 'pin', 'card': 'E06'})

    def test_time_badges_split_claims_from_records(self):
        case, state = played()
        cards = {c['id']: c for c in wall.board_cards(case, state)}
        claim = wall.card_times(case, cards['n1'])
        self.assertEqual(claim, [{'time': '22:00', 'claim': True}])
        record = wall.card_times(case, cards['E07'])
        self.assertEqual([t['time'] for t in record], ['22:50', '23:18'])
        self.assertTrue(all(not t['claim'] for t in record))


class CatalogAndDossier(unittest.TestCase):
    def test_catalog_carries_theories_and_slots(self):
        from room_catalog import build_catalog
        cat = build_catalog()
        one, two = cat['001'], cat['002']
        self.assertEqual(len(one['theories']), 7)
        self.assertTrue(one['slots'])
        self.assertEqual(two['slots'], [])
        kinds = {t['kind'] for t in one['theories']}
        self.assertEqual(kinds, {'deduction', 'confront'})
        for t in one['theories']:
            self.assertEqual(t['cards'], sorted(t['cards']))
            if t['kind'] == 'confront':
                self.assertIn('person', t)
                self.assertIn('unlocks', t)
        # No solution leaks through the board data.
        self.assertNotIn('killer', json.dumps(one['theories'], ensure_ascii=False))

    def test_dossier_roundtrip_keeps_the_wall(self):
        from dossier import export_dossier, import_dossier
        case, state = played()
        for c in ['E06', 'E07', 'n1']:
            wall.board_action(case, state, {'do': 'pin', 'card': c})
        wall.board_action(case, state, {'do': 'link', 'cards': ['E06', 'E07']})
        wall.board_action(case, state, {'do': 'link', 'cards': ['n1', 'E06']})
        wall.board_action(case, state, {'do': 'place', 'card': 'n1', 'slot': '22:00'})
        raw = export_dossier(case, state, 'notes')
        _case, loaded, _notes = import_dossier(raw)
        board = wall.board_state(loaded)
        self.assertEqual(sorted(board['pins']), ['E06', 'E07', 'n1'])
        self.assertEqual([t['status'] for t in board['theories']], ['holds', 'holds'])
        self.assertEqual(board['placed'], {'n1': '22:00'})

    def test_dossier_rejects_broken_board(self):
        from dossier import export_dossier, import_dossier
        case, state = played()
        raw = json.loads(export_dossier(case, state, ''))
        raw['board'] = {'pins': ['E06', 5], 'theories': [], 'placed': {}}
        with self.assertRaises(ValueError):
            import_dossier(json.dumps(raw, ensure_ascii=False))
        raw['board'] = {'pins': ['E06'], 'theories': [['E06']], 'placed': {}}
        with self.assertRaises(ValueError):
            import_dossier(json.dumps(raw, ensure_ascii=False))


class BoardUI(unittest.TestCase):
    def started(self):
        from streamlit.testing.v1 import AppTest
        a = AppTest.from_file('app.py')
        a.session_state['entry_phase'] = 'game'
        a.run()
        next(x for x in a.button if x.label == '🚔 يلا نحقق').click().run()
        for b in a.button:
            if b.label == 'تخطّى':
                b.click().run()
                break
        return a

    def test_solo_wall_to_payoff(self):
        a = self.started()
        inv = a.session_state['investigation']
        inv['discovered'].extend(['E06', 'E07'])
        inv['interviews'].append({'suspect': 'نادين مراد', 'question_id': 'n1',
                                  'question': 'مشيتي من الفندق إمتى؟',
                                  'answer': 'الساعة 22:00 بالظبط. كلمته قبلها في موضوع شغل، وبعد كده ما شفتوش.'})
        a.run()
        self.assertFalse(a.exception)
        self.assertTrue(any('ملف القضية' in s.value for s in a.subheader))
        for card in ['E06', 'n1']:
            a.selectbox(key='board_pick').set_value(card).run()
            a.button(key='board_pin').click().run()
            self.assertFalse(a.exception)
        self.assertEqual(a.session_state['investigation']['board']['pins'], ['E06', 'n1'])
        ms = next(m for m in a.multiselect if 'تناقض' in m.label)
        ms.select('E06').select('n1')
        a.button(key='FormSubmitter:board_link-سجّل النظرية').click().run()
        self.assertFalse(a.exception)
        theory = a.session_state['investigation']['board']['theories'][0]
        self.assertEqual(theory['status'], 'holds')
        self.assertEqual(theory['theory_id'], 'cf_n1')
        a.button(key='play_cf_n1').click().run()
        self.assertFalse(a.exception)
        self.assertIn('n2', {x['question_id'] for x in a.session_state['investigation']['interviews']})
        # Timeline is automatic: no manual placement controls, pinned n1 appears itself.
        self.assertEqual([x for x in a.selectbox if x.key in ('tl_card', 'tl_slot')], [])
        self.assertEqual([x for x in a.button if x.key == 'tl_place'], [])
        self.assertTrue(any('بيقول' in w.value for w in a.markdown if hasattr(w, 'value')) or any('بيقول' in str(w.value) for w in a.get('text')))

    def test_board_hidden_for_other_cases_and_race(self):
        from streamlit.testing.v1 import AppTest
        from game_engine import new_investigation
        a = AppTest.from_file('app.py')
        a.session_state['entry_phase'] = 'choose'
        a.run()
        a.button(key='open_case_002').click().run()
        for b in a.button:
            if b.label == 'تخطّى':
                b.click().run()
                break
        a.session_state['investigation']['discovered'].extend(['E01', 'E02'])
        a.run()
        self.assertFalse(any('ملف القضية' in s.value for s in a.subheader))
        # Race rooms keep the classic flow even on case 001.
        room = {'state': new_investigation(), 'code': 'R1', 'players': [{'name': 'أ', 'id': 1, 'unit': 'p1'}, {'name': 'ب', 'id': 2, 'unit': 'p2'}],
                'me': 1, 'revision': 0, 'mode': 'race', 'notes': '', 'status': 'playing', 'proposal': None, 'approvals': [],
                'case_id': '001', 'started': True, 'host': 1, 'team_count': 1, 'team_size': 1, 'max_players': 2,
                'winner_unit': None, 'my_unit': 'p1', 'unit_size': 1, 'urev': 0, 'unit_done': {}}
        room['state']['discovered'] = ['E01', 'E02']
        a = self.started()
        a.secrets.update(SUPABASE_URL='https://test.invalid', SUPABASE_KEY='k')
        with patch('room_client.rpc', return_value=room):
            a.radio(key='mode_choice').set_value('🏁 سباق فردي').run()
            self.assertFalse(a.exception)
            self.assertFalse(any('ملف القضية' in s.value for s in a.subheader))

    def test_coop_wall_actions_go_through_the_room(self):
        from streamlit.testing.v1 import AppTest
        from game_engine import new_investigation
        calls = []
        state = new_investigation()
        state['discovered'] = ['E06']
        room = {'state': state, 'code': 'C1', 'players': [{'name': 'أ', 'id': 1, 'unit': '0'}, {'name': 'ب', 'id': 2, 'unit': '0'}],
                'me': 1, 'revision': 0, 'mode': 'coop', 'notes': '', 'status': 'playing', 'proposal': None, 'approvals': [],
                'case_id': '001', 'started': True, 'host': 1, 'team_count': 1, 'team_size': 1, 'max_players': 2,
                'winner_unit': None, 'my_unit': '0', 'unit_size': 2, 'urev': 0, 'unit_done': {}}

        def fake_rpc(url, key, op, token='', code='', payload=None):
            calls.append(op)
            if op == 'board':
                wall.board_action(a.session_state['case'], room['state'], payload)
                room['urev'] += 1
            return room

        a = self.started()
        a.secrets.update(SUPABASE_URL='https://test.invalid', SUPABASE_KEY='k')
        with patch('room_client.rpc', side_effect=fake_rpc):
            a.radio(key='mode_choice').set_value('🤝 تعاون').run()
            a.session_state['room_token'] = 'x'
            a.run()
            self.assertFalse(a.exception)
            self.assertTrue(any('ملف القضية' in s.value for s in a.subheader))
            a.selectbox(key='board_pick').set_value('E06').run()
            a.button(key='board_pin').click().run()
            self.assertFalse(a.exception)
        self.assertIn('board', calls)
        self.assertEqual(room['state']['board']['pins'], ['E06'])


if __name__ == '__main__':
    unittest.main()
