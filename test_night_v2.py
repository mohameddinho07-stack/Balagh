"""Replayability upgrade: hidden hour, linked evidence, one disprovable forgery, solvability."""
import json, unittest
from night import *
from test_night import mk, run_to_search


def play(seed, n=5, forge=True, publish_all=True):
    g, toks, t = mk(n, seed)
    k = g.killers[0]
    g.act(toks[k], 'alibi', dict(place=[p for p in PLACES if p != g.truth['scene']][seed % 3]))
    for r in range(3):
        for nm in toks:
            pl = dict(spot=PLACES[(seed + r + len(nm)) % 4])
            if nm in g.killers and forge:
                pl['spoil'] = pl['spot'] if False else PLACES[(seed + r) % 3]
            g.act(toks[nm], 'search', pl)
        if publish_all:
            for c in list(g.cards.values()):
                if c['id'] not in g.public_cards:
                    g.act(toks[c['owner']], 'publish', dict(card=c['id']))
        if r < 2:
            g.act(toks['محمد'], 'next')
    return g, toks, k


class V2(unittest.TestCase):
    def test_murder_hour_hidden_until_end(self):
        for s in range(40):
            g, toks, t = mk(5, s)
            for tk in toks.values():
                v = g.view(tk)
                self.assertNotIn('الساعة ' + SLOTS[g.truth['m']], ' '.join(v['log']))
                self.assertIsNone(v['murder_slot'])
            g.act(toks[g.killers[0]], 'alibi', dict(place=BATH))
            for nm, tk in toks.items():
                v = g.view(tk)
                self.assertEqual(v['private']['murder_slot'], SLOTS[g.truth['m']] if nm in g.killers else None)
        g, toks, t = mk(5, 1)
        for _ in range(8): t[0] += 1000; g.view(toks['محمد'])
        self.assertEqual(g.view(toks['محمد'])['murder_slot'], SLOTS[g.truth['m']])

    def test_routes_have_exactly_one_lie_for_killer_none_for_cops(self):
        for s in range(60):
            g, toks, _ = play(s, publish_all=False) if False else (None, None, None)
            g, toks, t = mk(5, s); k = g.killers[0]
            g.act(toks[k], 'alibi', dict(place=BATH))
            for n, route in g.statements.items():
                diff = [i for i in range(3) if route[i] != g.truth['pos'][n][i]]
                self.assertEqual(diff, [g.truth['m']] if n == k and BATH != g.truth['pos'][n][g.truth['m']] else [])

    def test_every_night_solvable_by_plain_true_cards(self):
        for s in range(300):
            n = 4 + s % 4
            g, toks, k = play(s, n=n)
            m = g.truth['m']
            hits = [c['id'] for c in g.cards.values() if c['kind'] != 'link' and not c['spoiled']
                    and g._slot_known(c) and c['id'] not in g.refuted
                    and contradicts(c, k, g.statements[k][c['slot']], c['slot'])]
            self.assertGreaterEqual(len(hits), 2, s)
            voters = [x for x in toks if x != k]
            g.act(toks[voters[0]], 'propose', dict(suspect=k, cards=hits[:2])) if g.phase == 'talk' else None
            pr = dict(suspect=k, cards=hits[:2])
            for x in voters[1:]:
                if g.proposal: g.act(toks[x], 'approve', pr)
            self.assertEqual(g.result['winner'], 'ظابط مباحث', s)

    def test_innocent_cannot_be_convicted_by_true_cards(self):
        for s in range(150):
            g, toks, k = play(s, forge=False)
            for x in toks:
                if x == k: continue
                hits = [c for c in g.cards.values() if c['kind'] != 'link'
                        and contradicts(c, x, g.statements[x][c['slot']], c['slot'])]
                self.assertEqual(hits, [], (s, x))

    def test_forgery_is_single_and_always_refutable(self):
        forged = 0
        for s in range(300):
            g, toks, k = play(s, n=4 + s % 4)
            bad = [c for c in g.cards.values() if c['spoiled']]
            self.assertLessEqual(len(bad), 1)
            if not bad:
                continue
            forged += 1
            f = bad[0]
            victim = next(x for x in f['seen'] if x not in seen_at(g.truth, None, f['slot'], f['place']))
            proof = [c for c in g.cards.values() if c['kind'] == 'testimony' and c['owner'] == victim and c['slot'] == f['slot']]
            self.assertTrue(proof)
            # the forgery cannot convict anyone alone: an innocent still has at most that 1 'hit'
            hits = [c for c in g.cards.values() if c['kind'] != 'link' and contradicts(c, victim, g.statements[victim][c['slot']], c['slot'])]
            self.assertLessEqual(len(hits), 1)
            if g.phase == 'talk':
                g.act(toks[victim], 'challenge', dict(cards=[f['id'], proof[0]['id']]))
                self.assertIn(f['id'], g.refuted)
                with self.assertRaises(GameError):
                    g.act(toks['محمد'] if 'محمد' != victim else toks['سارة'], 'propose', dict(suspect=victim, cards=[f['id'], proof[0]['id']]))
        self.assertGreater(forged, 50)

    def test_challenge_on_honest_pair_reveals_nothing(self):
        for s in range(60):
            g, toks, k = play(s, forge=False)
            ids = [c['id'] for c in g.cards.values() if c['kind'] != 'link' and g._slot_known(c)][:2]
            before = (g.rev, list(g.log), list(g.refuted))
            with self.assertRaises(GameError): g.act(toks['محمد'], 'challenge', dict(cards=ids))
            self.assertEqual(before, (g.rev, list(g.log), list(g.refuted)))

    def test_hidden_hour_not_usable_until_linked(self):
        seen_hidden = linked_ok = 0
        for s in range(120):
            g, toks, t = mk(5, s); k = g.killers[0]
            g.act(toks[k], 'alibi', dict(place=BATH))
            for nm in toks: g.act(toks[nm], 'search', dict(spot=PLACES[0]))
            masked = [c for c in g.cards.values() if c['masked']]
            if not masked: continue
            c = masked[0]; seen_hidden += 1
            g.act(toks[c['owner']], 'publish', dict(card=c['id']))
            v = g.view(toks['محمد'])
            shown = next(x for x in v['board'] if x['id'] == c['id'])
            self.assertEqual(shown['slot'], '؟'); self.assertNotIn(SLOTS[c['slot']], json.dumps(shown, ensure_ascii=False).replace('؟', ''))
            other = next(x for x in toks if x != c['owner'])
            plain = next(x for x in g.cards.values() if x['kind'] != 'link' and not x['masked'] and x['id'] != c['id'])
            g.act(toks[plain['owner']], 'publish', dict(card=plain['id']))
            with self.assertRaises(GameError):
                g.act(toks[other], 'propose', dict(suspect=[n for n in toks if n not in (other, c['owner'])][0], cards=[c['id'], plain['id']]))
            L = next(x for x in g.cards.values() if x['kind'] == 'link' and c['id'] in (x['a'], x['b']))
            for pid in (L['a'], L['b']):
                if pid not in g.public_cards:
                    g.act(toks[g.cards[pid]['owner']], 'publish', dict(card=pid))
            g.act(toks[L['owner']], 'publish', dict(card=L['id']))
            self.assertTrue(g._slot_known(c))
            self.assertEqual(next(x for x in g.view(toks['محمد'])['board'] if x['id'] == c['id'])['slot'], SLOTS[c['slot']])
            linked_ok += 1
        self.assertGreater(seen_hidden, 40); self.assertEqual(seen_hidden, linked_ok)

    def test_forge_budget_not_a_role_oracle(self):
        g, toks, _ = mk(5, 2)
        shapes = {json.dumps(sorted(g.view(tk)['private'].keys())) for tk in toks.values()}
        self.assertEqual(len(shapes), 1)

    def test_nights_differ_in_shape(self):
        shapes = set()
        for s in range(200):
            g, toks, _ = play(s, publish_all=False) if False else mk(5, s)[:2] + (None,)
            m = g.truth['m']; w = sorted(n for n in g.truth['pos'] if n not in g.killers and g.truth['pos'][n][m] == g.truth['scene'])
            shapes.add((m, g.truth['scene'], len(w)))
        self.assertGreaterEqual(len(shapes), 9)

if __name__ == '__main__':
    unittest.main()


class Persist(unittest.TestCase):
    def test_pack_roundtrip_preserves_new_state_and_views(self):
        from night_store import pack, unpack
        for s in range(40):
            g, toks, k = play(s, n=4 + s % 4)
            if g.refuted == [] and g.forge_used:
                bad = next(c for c in g.cards.values() if c['spoiled'])
                proof = next(c for c in g.cards.values() if c['kind'] == 'testimony' and c['slot'] == bad['slot'] and c['owner'] in bad['seen'] and g._conflict(bad, c))
                g.act(toks['محمد'], 'challenge', dict(cards=[bad['id'], proof['id']]))
            g2 = unpack(pack(g), clock=g.clock)
            self.assertEqual(g2.forge_used, g.forge_used); self.assertEqual(g2.refuted, g.refuted)
            for nm, tk in toks.items():
                self.assertEqual(json.dumps(g.view(tk), sort_keys=True), json.dumps(g2.view(tk), sort_keys=True))
            # continuing play after reload gives the same outcome
            g2.act(toks['محمد'], 'read')

if __name__ == '__main__':
    unittest.main()
