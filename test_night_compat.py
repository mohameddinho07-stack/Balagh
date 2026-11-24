"""Snapshots saved by the first version of the mode must still open, read and play on."""
import json, unittest
from night import *
from night_store import unpack


class OldSnapshots(unittest.TestCase):
    def load(self):
        return json.load(open('old_night_snapshots.json', encoding='utf8'))

    def test_every_saved_phase_opens_and_views(self):
        for s in self.load():
            t = [0.0]
            g = unpack(s['snapshot'].encode(), clock=lambda: t[0])
            for nm, tk in s['tokens'].items():
                v = g.view(tk)
                self.assertEqual(v['phase'], s['phase'])
                json.dumps(v, ensure_ascii=False)
                if g.phase != 'lobby':
                    self.assertEqual(v['role'], ROLE_KILLER if nm in s['killers'] else ROLE_COP)

    def test_old_game_plays_on_with_new_rules(self):
        for s in self.load():
            if s['label'] not in ('alibi', 'search', 'talk_r1', 'talk_r1_published'):
                continue
            t = [0.0]
            g = unpack(s['snapshot'].encode(), clock=lambda: t[0])
            toks = s['tokens']
            host = toks['محمد']
            for _ in range(12):
                t[0] += 1000
                g.view(host)
            self.assertEqual(g.phase, 'ended', s['label'])
            self.assertIn('killers', g.view(host)['result'])

    def test_old_statements_become_routes_and_old_cards_keep_working(self):
        s = next(x for x in self.load() if x['label'] == 'talk_r1_published')
        g = unpack(s['snapshot'].encode(), clock=lambda: 0.0)
        m = g.truth['m']
        for n, route in g.statements.items():
            self.assertEqual(len(route), 3)
            diff = [i for i in range(3) if route[i] != g.truth['pos'][n][i]]
            self.assertTrue(diff in ([], [m]))
        v = g.view(s['tokens']['محمد'])
        for c in v['board'] + v['my_cards']:
            self.assertFalse(c['masked'])

    def test_opening_does_not_rewrite_the_stored_snapshot(self):
        from test_night_storage import MemoryRPC
        from night_store import DurableStore
        s = next(x for x in self.load() if x['label'] == 'talk_r1_published')
        rpc = MemoryRPC(); store = DurableStore('x', 'x', 'test-master-for-compat-'*3, transport=rpc, clock=lambda: 0)
        code = 'ABCDEF1234'
        cap, cipher = store._keys(code)
        rpc.rows[code] = dict(cap=cap, revision=7, snapshot=cipher.encrypt(s['snapshot'].encode()).decode())
        before = rpc.rows[code]['snapshot']
        store.read(code, s['tokens']['محمد'])
        self.assertEqual(rpc.rows[code]['snapshot'], before)
        self.assertEqual(rpc.rows[code]['revision'], 7)

if __name__ == '__main__':
    unittest.main()
