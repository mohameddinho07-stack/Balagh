import json, unittest, glob, re
from night import *

def mk(n=5, seed=1, **cfg):
    t = [0.0]
    g = Game(seed=seed, cfg=cfg, clock=lambda: t[0])
    toks = {}
    for i in range(n):
        nm = ['محمد','سارة','أحمد','كريم','منى','هاني','ياسمين','طارق','دينا','عمر'][i]
        toks[nm] = g.join(nm)
    g.start(toks['محمد'])
    return g, toks, t

def killers(g): return list(g.killers)

def run_to_search(g, toks):
    for k in g.killers:
        g.act(toks[k], 'alibi', dict(place=BATH))

class T(unittest.TestCase):
    def test_roles_and_names(self):
        for s in range(30):
            g, toks, _ = mk(5, s)
            self.assertEqual(len(g.killers), 1)
            g8, _, _ = mk(8, s, max_players=10, killers_from=8); self.assertEqual(len(g8.killers), 2)
            g7, _, _ = mk(7, s); self.assertEqual(len(g7.killers), 1)
            for nm, tk in toks.items():
                v = g.view(tk)
                self.assertEqual(v['role'], ROLE_KILLER if nm in g.killers else ROLE_COP)
        self.assertNotIn('محقق', open('night.py', encoding='utf8').read())

    def test_no_secret_leak_to_other_clients(self):
        for s in range(40):
            g, toks, t = mk(6, s)
            run_to_search(g, toks)
            for nm in toks: g.act(toks[nm], 'search', dict(spot=PLACES[1], **({'spoil': PLACES[2]} if nm in g.killers else {})))
            # after resolve, check each view against others' private data
            for nm, tk in toks.items():
                v = g.view(tk); blob = json.dumps(v, ensure_ascii=False)
                if nm not in g.killers:
                    for k in g.killers:
                        # killer identity must not be derivable: name may appear as player, never tagged
                        self.assertNotIn('"partners": ["%s"' % k, blob)
                    self.assertEqual(v['private']['partners'], [])
                    self.assertNotIn(ROLE_KILLER, blob.replace('"killer_count"', ''))  # no role strings except own
                for c in g.cards.values():
                    if c['owner'] != nm and c['id'] not in g.public_cards:
                        self.assertNotIn(c['id'], blob)
                self.assertNotIn('pos', v); self.assertNotIn('truth', blob)
                self.assertIsNone(v['result'])
                other_places = [g.truth['pos'][o] for o in g.truth['pos'] if o != nm]
                self.assertNotIn('"spoil', blob)

    def test_view_shape_identical_across_roles(self):
        g, toks, _ = mk(5, 3)
        shapes = {json.dumps(sorted(g.view(tk).keys())) for tk in toks.values()}
        self.assertEqual(len(shapes), 1)

    def test_token_auth(self):
        g, toks, _ = mk(5, 1)
        for bad in ['', 'x'*64, None, toks['محمد'][:63] + '0' if toks['محمد'][-1] != '0' else toks['محمد'][:63] + '1']:
            with self.assertRaises(GameError): g.view(bad)
        # one player's token cannot act as another: ops use only the token's identity
        k = g.killers[0]; c = next(n for n in toks if n not in g.killers)
        with self.assertRaises(GameError): g.act(toks[c], 'alibi', dict(place=PLACES[0]))
        # same error text for cop and wrong phase: no role oracle
        try: g.act(toks[c], 'alibi', dict(place=PLACES[0]))
        except GameError as e: m1 = str(e)
        run_to_search(g, toks)
        try: g.act(toks[c], 'alibi', dict(place=PLACES[0]))
        except GameError as e: m2 = str(e)
        self.assertEqual(m1, m2)

    def test_cannot_publish_others_cards(self):
        g, toks, _ = mk(5, 2); run_to_search(g, toks)
        for nm in toks: g.act(toks[nm], 'search', dict(spot=PLACES[0]))
        cid = next(c['id'] for c in g.cards.values() if c['owner'] == 'سارة')
        with self.assertRaises(GameError): g.act(toks['محمد'], 'publish', dict(card=cid))
        g.act(toks['سارة'], 'publish', dict(card=cid))
        self.assertIn(cid, [c['id'] for c in g.view(toks['محمد'])['board']])

    def test_phase_flow_and_timeout(self):
        g, toks, t = mk(5, 4)
        self.assertEqual(g.phase, 'alibi')
        t[0] += 100; g.view(toks['محمد'])        # killer never answered: lazy tick advances
        self.assertEqual(g.phase, 'search'); self.assertEqual(g.round, 1)
        t[0] += 100; g.view(toks['محمد']); self.assertEqual(g.phase, 'talk')
        # reconnect: view is read-only and idempotent
        a = json.dumps(g.view(toks['سارة']), sort_keys=True); b = json.dumps(g.view(toks['سارة']), sort_keys=True)
        self.assertEqual(a, b)
        for r in range(1, 4):
            t[0] += 1000; g.view(toks['محمد'])
            t[0] += 1000; g.view(toks['محمد'])
        self.assertEqual(g.phase, 'ended'); self.assertEqual(g.result['winner'], 'القاتل')
        v = g.view(toks['سارة']); self.assertIn('killers', v['result'])   # reveal only at end

    def test_accusation_rules(self):
        wins = fails = 0
        for s in range(200):
            g, toks, t = mk(5, s); k = g.killers[0]
            g.act(toks[k], 'alibi', dict(place=BATH))
            for nm in toks: g.act(toks[nm], 'search', dict(spot=SLOTS and PLACES[0]))
            # publish everything
            for c in list(g.cards.values()):
                g.act(toks[c['owner']], 'publish', dict(card=c['id']))
            m = g.truth['m']
            hits = [c['id'] for c in g.cards.values() if contradicts(c, k, BATH, m)]
            innocent = next(n for n in toks if n not in g.killers)
            if len(hits) >= 2:
                # approvals: proposer + enough others
                voters = [n for n in toks if n != k]
                g.act(toks[voters[0]], 'propose', dict(suspect=k, cards=hits[:2]))
                pr = dict(suspect=k, cards=hits[:2])
                for n in voters[1:]:
                    if g.phase == 'ended': break
                    g.act(toks[n], 'approve', pr)
                self.assertEqual(g.phase, 'ended'); self.assertEqual(g.result['winner'], 'ظابط مباحث'); wins += 1
            else:
                # innocent accused with any cards: fails, uniform message, stays active
                pub = [c['id'] for c in g.cards.values()][:2]
                voters = [n for n in toks if n != innocent]
                g.act(toks[voters[0]], 'propose', dict(suspect=innocent, cards=pub))
                pr = dict(suspect=innocent, cards=pub)
                for n in voters[1:]:
                    if g.chances < 2: break
                    g.act(toks[n], 'approve', pr)
                self.assertEqual(g.chances, 1); self.assertEqual(g.phase, 'talk'); fails += 1
                self.assertNotIn('بريء', ' '.join(g.log))
        self.assertGreater(wins, 0); self.assertGreater(fails, 0)

    def test_killer_cannot_block_alone_and_accused_cannot_vote(self):
        g, toks, _ = mk(5, 7); k = g.killers[0]
        for nm in toks:
            pass
        run_to_search(g, toks)
        for nm in toks: g.act(toks[nm], 'search', dict(spot=PLACES[0]))
        for c in g.cards.values(): g.act(toks[c['owner']], 'publish', dict(card=c['id']))
        ids = list(g.public_cards)[:2]
        voters = [n for n in toks if n != 'محمد' and n != k]
        g.act(toks['محمد'], 'propose', dict(suspect='سارة' if k != 'سارة' else 'أحمد', cards=ids))
        sus = g.proposal['suspect']
        with self.assertRaises(GameError): g.act(toks[sus], 'approve', dict(suspect=sus, cards=ids))
        pr = dict(suspect=sus, cards=ids)
        for n in toks:
            if n in ('محمد', sus, k): continue
            if g.proposal: g.act(toks[n], 'approve', pr)
        self.assertEqual(g.chances, 1)   # resolved without the killer's vote

    def test_no_leak_across_rounds_for_ended_only(self):
        g, toks, t = mk(5, 9)
        for _ in range(8): t[0] += 1000; g.view(toks['محمد'])
        for tk in toks.values():
            self.assertIsNotNone(g.view(tk)['result'])

if __name__ == '__main__':
    unittest.main()

class T2(unittest.TestCase):
    def test_scene_alibi_rejected_for_killer_only(self):
        g, toks, _ = mk(5, 11); k = g.killers[0]
        with self.assertRaises(GameError): g.act(toks[k], 'alibi', dict(place=g.truth['scene']))
        g.act(toks[k], 'alibi', dict(place=BATH))
        self.assertEqual(g.phase, 'search')
    def test_generator_always_has_witnesses(self):
        import random
        for s in range(300):
            g, _, _ = mk(4, s); m = g.truth['m']
            w = [n for n in g.truth['pos'] if n not in g.killers and g.truth['pos'][n][m] == g.truth['scene']]
            self.assertGreaterEqual(len(w), 2)

def fail_delta(g, toks, sus, ids):
    voters = [n for n in toks if n != sus]
    before = (g.rev, len(g.log), g.chances)
    g.act(toks[voters[0]], 'propose', dict(suspect=sus, cards=ids))
    for n in voters[1:]:
        if g.proposal: g.act(toks[n], 'approve', dict(suspect=sus, cards=ids))
    return g.rev - before[0], len(g.log) - before[1], g.chances - before[2], g.log[-1].replace(sus, 'X'), g.phase

class T3(unittest.TestCase):
    def setup_pub(self, s):
        g, toks, _ = mk(5, s); k = g.killers[0]
        g.act(toks[k], 'alibi', dict(place=BATH))
        for nm in toks: g.act(toks[nm], 'search', dict(spot=PLACES[0]))
        for c in list(g.cards.values()): g.act(toks[c['owner']], 'publish', dict(card=c['id']))
        return g, toks, k
    def test_failed_accusation_side_effects_identical_innocent_vs_killer(self):
        seen = 0
        for s in range(120):
            g1, t1, k = self.setup_pub(s); g2, t2, _ = self.setup_pub(s)
            m = g1.truth['m']
            lst1 = list(g1.cards.values()); lst2 = list(g2.cards.values())
            idx = [i for i, c in enumerate(lst1) if not contradicts(c, k, BATH, m)][:2]
            weak = [lst1[i]['id'] for i in idx]; weak2 = [lst2[i]['id'] for i in idx]
            innocent = next(n for n in t1 if n != k)
            a = fail_delta(g1, t1, k, weak)           # killer, insufficient evidence
            b = fail_delta(g2, t2, innocent, weak2)    # innocent
            self.assertEqual(a, b)
            self.assertEqual(g1.chances, g2.chances); seen += 1
        self.assertGreater(seen, 0)
    def test_private_ids_not_probeable(self):
        g, toks, _ = mk(5, 5); run_to_search(g, toks)
        for nm in toks: g.act(toks[nm], 'search', dict(spot=PLACES[0]))
        priv = next(iter(g.cards)); fake = 'ffffff'
        msgs = []
        for cid in (priv, fake):
            try: g.act(toks['محمد'], 'propose', dict(suspect='سارة', cards=[cid, cid + 'x']))
            except GameError as e: msgs.append(str(e))
        self.assertEqual(len(set(msgs)), 1); self.assertEqual(g.chances, 2)
    def test_one_proposal_per_player_per_round(self):
        g, toks, k = self.setup_pub(3)
        ids = list(g.public_cards)[:2]
        g.act(toks['محمد'], 'propose', dict(suspect='سارة' if k != 'سارة' else 'أحمد', cards=ids))
        with self.assertRaises(GameError):
            g.act(toks['محمد'], 'propose', dict(suspect='كريم', cards=ids))
    def test_killer_alone_cannot_burn_chances(self):
        g, toks, k = self.setup_pub(4)
        ids = list(g.public_cards)[:2]
        sus = next(n for n in toks if n != k)
        g.act(toks[k], 'propose', dict(suspect=sus, cards=ids))
        self.assertEqual(g.chances, 2)   # needs majority; stays pending


class Scope(unittest.TestCase):
    def test_room_cap_is_seven(self):
        g = Game(seed=1)
        for i in range(7): g.join('لاعب%d' % i)
        with self.assertRaises(GameError): g.join('زيادة')


class Adversarial(unittest.TestCase):
    """Fuzz: random actions by random players; after every step every view is checked."""
    def _flat(self, o, out):
        if isinstance(o, dict):
            for k, v in o.items():
                out.append(('k', k)); self._flat(v, out)
        elif isinstance(o, (list, tuple)):
            for v in o: self._flat(v, out)
        else:
            out.append(('v', o))
        return out

    def test_fuzz_no_cross_player_leak(self):
        import random as R
        for seed in range(60):
            g, toks, t = mk(6, seed)
            rng = R.Random(seed)
            names = list(toks)
            for step in range(60):
                nm = rng.choice(names)
                op = rng.choice(['alibi', 'search', 'publish', 'propose', 'approve', 'next', 'read'])
                payload = {}
                if op == 'alibi': payload = dict(place=rng.choice(PLACES))
                elif op == 'search': payload = dict(spot=rng.choice(PLACES), spoil=rng.choice(PLACES))
                elif op == 'publish': payload = dict(card=rng.choice(list(g.cards) or ['x']))
                elif op == 'propose': payload = dict(suspect=rng.choice(names), cards=list(g.public_cards)[:2])
                try: g.act(toks[nm], op, payload)
                except GameError: pass
                t[0] += rng.choice([0, 10, 50, 200])
                for me, tk in toks.items():
                    v = g.view(tk)
                    flat = self._flat(v, [])
                    keys = {x for k, x in flat if k == 'k'}
                    bad = {'spoil', 'spoiled', 'submitted', 'hash', 'token'} | (set() if g.phase == 'ended' else {'truth', 'pos', 'killers'})
                    self.assertFalse(keys & bad, keys & bad)
                    if g.phase != 'ended':
                        self.assertIsNone(v['result'])
                        # role string appears only as my own role value
                        roles = [x for k, x in flat if k == 'v' and x in (ROLE_KILLER, ROLE_COP)]
                        self.assertEqual(roles, [v['role']])
                    if me not in g.killers:
                        self.assertEqual(v['private']['partners'], [])
                    linked = {i for lid in g.public_cards if g.cards[lid]['kind'] == 'link' for i in (g.cards[lid]['a'], g.cards[lid]['b'])}
                    for c in g.cards.values():
                        if c['owner'] != me and c['id'] not in g.public_cards and c['id'] not in linked:
                            self.assertNotIn(c['id'], [x for k, x in flat if k == 'v'])
                    # others' private position lists must not be present as a whole
                    for o in names:
                        if o != me and g.truth:
                            self.assertNotIn(g.truth['pos'][o], [x for k, x in flat if k == 'v'] )
                    if g.phase in ('alibi', 'search'):
                        self.assertNotIn('i_submitted_by', keys)

    def test_statements_only_after_alibi_phase(self):
        for seed in range(20):
            g, toks, t = mk(5, seed)
            self.assertEqual(g.phase, 'alibi')
            for tk in toks.values():
                self.assertEqual(g.view(tk)['statements'], {})
            k = g.killers[0]
            other = [n for n in toks if n != k][0]
            g.act(toks[other], 'alibi', dict(place=BATH)) if False else None
            g.act(toks[k], 'alibi', dict(place=BATH))
            self.assertNotEqual(g.phase, 'alibi')
