"""Runs the real generated SQL on a throwaway local Postgres (opt-in: needs `pip install pgserver`).
Covers every mode on every registered case, plus a test-only extra case that exists
nowhere in the product, proving a new case inherits all modes with no room code."""
import json, tempfile, unittest, uuid
try:
    import pgserver, psycopg2
except ImportError:
    raise unittest.SkipTest('pgserver not installed')
import game_engine
from cases_extra import clue, person, q
from gen_rooms_sql import render

BASE = """
create role anon; create role authenticated;
create table public.rooms(id bigserial primary key, room_code text, status text, max_players int, current_players int default 0);
create table public.players(id bigserial primary key, player_name text, room_code text, role text, is_alive boolean, is_ready boolean);
"""
SHIM = '''create schema if not exists extensions;
create function extensions.gen_random_bytes(n int) returns bytea language sql as $$select decode(substr(md5(random()::text)||md5(random()::text)||md5(random()::text)||md5(random()::text),1,2*n),'hex')$$;
create function extensions.digest(t text, a text) returns bytea language sql as $$select sha256(convert_to(t,'utf8'))$$;'''
TEST_CASE = {'id': 'T99', 'scene': 'hotel', 'public': {'title': 'قضية اختبار', 'location': 'x', 'victim': 'v', 'story': 's', 'timeline': [],
    'tagline': '', 'difficulty': '', 'duration': ''},
    'evidence': [clue('E01', 'أ', 'نص'), clue('E02', 'ب', 'نص', ['E01']), clue('E03', 'ج', 'نص', ['E02'])],
    'verification': clue('E04', 'د', 'نص', ['E01']),
    'characters': [person('p1', 'سامي', 30, 'شغلانة', 'عام', [q('x1', 'سؤال؟', 'جواب')]), person('p2', 'منى', 30, 'شغلانة', 'عام', [q('y1', 'سؤال؟', 'جواب', ['E01'])])],
    'truth': {'killer': 'منى', 'required_evidence': ['E02', 'E03'], 'explanation': 'x'}}
KILLERS = None


class Mode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.srv = pgserver.get_server(cls.dir)
        game_engine.CASE_REGISTRY['T99'] = TEST_CASE
        cls.conn = psycopg2.connect(cls.srv.get_uri()); cls.conn.autocommit = True
        cur = cls.conn.cursor()
        cur.execute(BASE)
        cur.execute(SHIM)  # local Postgres has no pgcrypto; Supabase does
        with open('rooms.sql', encoding='utf-8') as f:
            cur.execute(f.read().replace('create extension if not exists pgcrypto with schema extensions;', ''))  # earlier version first: migration path
        cur.execute(render())
        cur.execute(render())  # idempotent
        cls.cases = {cid: game_engine.generate_case(cid) for cid in game_engine.CASE_REGISTRY}

    @classmethod
    def tearDownClass(cls):
        game_engine.CASE_REGISTRY.pop('T99', None)
        cls.conn.close(); cls.srv.cleanup()

    def call(self, op, token='', code='', **payload):
        cur = self.conn.cursor()
        cur.execute('select public.balagh_room(%s,%s,%s,%s::jsonb)', (op, code, token, json.dumps(payload)))
        return cur.fetchone()[0]

    def fail(self, op, token='', code='', **payload):
        with self.assertRaises(psycopg2.Error):
            self.call(op, token, code, **payload)

    def play(self, case, tok, upto=None):
        """Inspect every evidence in prerequisite order for one unit."""
        for e in case['evidence'] + [case['verification']]:
            self.call('inspect', tok, revision=self.call('read', tok)['urev'], evidence=e['id'])

    def win_payload(self, case):
        return dict(suspect=case['truth']['killer'], evidence=case['truth']['required_evidence'])

    def test_every_case_every_mode(self):
        for cid, case in self.cases.items():
            with self.subTest(case=cid):
                self.coop(cid, case); self.race(cid, case); self.team(cid, case, 2, 2); self.team(cid, case, 2, 4); self.team(cid, case, 3, 2); self.team(cid, case, 2, 1)

    def coop(self, cid, case):
        a = self.call('create', name='أ', mode='coop', case=cid, max_players=3)
        toks = [a['token']] + [self.call('join', code=a['code'], name=n)['token'] for n in ['ب', 'ج']]
        self.fail('join', code=a['code'], name='د')
        self.call('inspect', toks[0], revision=self.call('read', toks[0])['urev'], evidence='E01')
        views = [self.call('read', t) for t in toks]
        assert all(v['state']['discovered'] == ['E01'] and v['case_id'] == cid for v in views)
        self.fail('inspect', toks[1], revision=0, evidence='E02')  # stale revision
        for e in case['evidence'][1:] + [case['verification']]:
            self.call('inspect', toks[1], revision=self.call('read', toks[1])['urev'], evidence=e['id'])
        self.fail('accuse', toks[0], **self.win_payload(case))  # shared units must use propose
        self.call('propose', toks[0], **self.win_payload(case))
        pr = self.call('read', toks[1])['proposal']
        self.call('approve', toks[1], proposal=pr)
        self.fail('approve', toks[1], proposal=pr)
        assert self.call('read', toks[2])['status'] == 'playing'
        done = self.call('approve', toks[2], proposal=pr)
        assert done['status'] == 'finished' and done['state']['result']['success']

    def race(self, cid, case):
        a = self.call('create', name='س1', mode='race', case=cid, max_players=5)
        toks = [a['token']] + [self.call('join', code=a['code'], name='س%d' % i)['token'] for i in range(2, 6)]
        self.fail('inspect', toks[0], revision=0, evidence='E01')  # not started
        self.fail('start', toks[1])  # only the host starts
        started = self.call('start', toks[0])
        self.fail('join', code=a['code'], name='متأخر')
        self.call('inspect', toks[2], revision=0, evidence='E01'); self.call('notes', toks[2], notes='PRIVATE')
        for i, t in enumerate(toks):
            v = self.call('read', t)
            assert (v['state']['discovered'] == ['E01']) == (i == 2) and ('PRIVATE' in json.dumps(v)) == (i == 2)
        for t in toks[:2]:
            self.play(case, t)
        bad = self.call('accuse', toks[1], suspect=case['characters'][0]['name'], evidence=['E01'])
        assert bad['state']['finished'] and not bad['state']['result']['success'] and bad['winner_unit'] is None
        self.fail('inspect', toks[1], revision=0, evidence='E01')
        self.call('inspect', toks[3], revision=0, evidence='E01')
        win = self.call('accuse', toks[0], **self.win_payload(case))
        assert win['winner_unit'] == win['my_unit'] and win['status'] == 'finished'
        assert self.call('read', toks[4])['winner_unit'] == win['my_unit']
        self.fail('accuse', toks[2], **self.win_payload(case))

    def team(self, cid, case, teams, size):
        a = self.call('create', name='م1', mode='team', case=cid, team_count=teams, team_size=size, team=1)
        toks = [a['token']]
        for i in range(2, teams * size + 1):
            toks.append(self.call('join', code=a['code'], name='م%d' % i)['token'])
        self.fail('join', code=a['code'], name='زيادة')
        views = [self.call('read', t) for t in toks]
        counts = {}
        for v in views:
            counts[v['my_unit']] = counts.get(v['my_unit'], 0) + 1
        assert sorted(counts) == ['t%d' % i for i in range(1, teams + 1)] and set(counts.values()) == {size}, counts
        self.call('start', toks[0])
        by_team = {}
        for t, v in zip(toks, views):
            by_team.setdefault(v['my_unit'], []).append(t)
        t1, t2 = by_team['t1'], by_team['t2']
        # Shared inside a team, invisible to other teams.
        self.call('inspect', t1[0], revision=0, evidence='E01'); self.call('notes', t1[0], notes='TEAM1 PRIVATE')
        if size > 1:
            assert self.call('read', t1[-1])['state']['discovered'] == ['E01']
            assert 'TEAM1 PRIVATE' not in json.dumps(self.call('read', t1[-1]))
        for other in toks:
            if other not in t1:
                assert self.call('read', other)['state']['discovered'] == []
        # Team 2 plays everything and wins; one wrong team is eliminated first.
        for e in case['evidence'] + [case['verification']]:
            self.call('inspect', t2[0], revision=self.call('read', t2[0])['urev'], evidence=e['id'])
        if teams > 2:
            t3 = by_team['t3']
            self.call('inspect', t3[0], revision=0, evidence='E01')
            if size > 1:
                self.call('propose', t3[0], suspect=case['characters'][0]['name'], evidence=['E01'])
                pr = self.call('read', t3[0])['proposal']
                for m in t3[1:]:
                    out = self.call('approve', m, proposal=pr)
            else:
                out = self.call('accuse', t3[0], suspect=case['characters'][0]['name'], evidence=['E01'])
            assert out['unit_done']['t3'] and out['status'] == 'playing' and out['winner_unit'] is None
        if size > 1:
            self.call('propose', t2[0], **self.win_payload(case))
            pr = self.call('read', t2[0])['proposal']
            for m in t2[1:-1]:
                assert self.call('approve', m, proposal=pr)['status'] == 'playing'
            res = self.call('approve', t2[-1], proposal=pr)
        else:
            res = self.call('accuse', t2[0], **self.win_payload(case))
        assert res['status'] == 'finished' and res['winner_unit'] == 't2'
        for t in toks:
            v = self.call('read', t)
            assert v['status'] == 'finished' and v['winner_unit'] == 't2'
        self.fail('inspect', t1[0], revision=0, evidence='E02')

    def test_board_op(self):
        a = self.call('create', name='أ', mode='coop', case='001', max_players=2)
        toks = [a['token'], self.call('join', code=a['code'], name='ب')['token']]
        urev = lambda t: self.call('read', t)['urev']
        # Cards must be earned before they can be pinned.
        self.fail('board', toks[0], revision=0, **{'do': 'pin', 'card': 'E06'})
        self.call('inspect', toks[0], revision=urev(toks[0]), evidence='E06')
        self.call('interview', toks[0], revision=urev(toks[0]), suspect='nadine', topic='n1')
        self.call('board', toks[0], revision=urev(toks[0]), **{'do': 'pin', 'card': 'E06'})
        mate = self.call('read', toks[1])
        assert mate['state']['board']['pins'] == ['E06'], mate['state'].get('board')
        self.fail('board', toks[1], revision=0, **{'do': 'pin', 'card': 'n1'})  # stale revision
        self.call('board', toks[1], revision=urev(toks[1]), **{'do': 'pin', 'card': 'n1'})
        # An authored confrontation pair holds, a random pair stays open, duplicates are refused.
        r = self.call('board', toks[0], revision=urev(toks[0]), **{'do': 'link', 'cards': ['n1', 'E06']})
        assert r['state']['board']['theories'][0]['status'] == 'holds'
        assert r['state']['board']['theories'][0]['theory_id'] == 'cf_n1'
        self.fail('board', toks[0], revision=urev(toks[0]), **{'do': 'link', 'cards': ['E06', 'n1']})
        self.call('inspect', toks[0], revision=urev(toks[0]), evidence='E07')
        self.call('board', toks[0], revision=urev(toks[0]), **{'do': 'pin', 'card': 'E07'})
        r = self.call('board', toks[0], revision=urev(toks[0]), **{'do': 'link', 'cards': ['n1', 'E07']})
        assert r['state']['board']['theories'][1]['status'] == 'open'
        # Timeline placement with slot validation.
        self.fail('board', toks[0], revision=urev(toks[0]), **{'do': 'place', 'card': 'n1', 'slot': '25:00'})
        r = self.call('board', toks[0], revision=urev(toks[0]), **{'do': 'place', 'card': 'n1', 'slot': '22:00'})
        assert r['state']['board']['placed'] == {'n1': '22:00'}
        # Board actions never clear a pending accusation proposal.
        self.call('propose', toks[0], suspect='نادين مراد', evidence=['E06', 'E07'])
        self.call('board', toks[1], revision=urev(toks[1]), **{'do': 'unplace', 'card': 'n1'})
        assert self.call('read', toks[0])['proposal'] is not None
        # Unpin removes the card from the wall and the line; the theory log stays.
        r = self.call('board', toks[0], revision=urev(toks[0]), **{'do': 'unpin', 'card': 'n1'})
        assert r['state']['board']['pins'] == ['E06', 'E07'] and 'n1' not in r['state']['board']['placed']
        assert len(r['state']['board']['theories']) == 2

    def test_server_rules(self):
        a = self.call('create', name='أ', mode='coop', case='T99')
        self.fail('create', name='أ', mode='coop', case='NOPE')
        self.fail('create', name='أ', mode='team', case='T99', team_count=4, team_size=5)
        self.fail('create', name='أ', mode='race', case='T99', max_players=11)
        self.fail('inspect', a['token'], revision=0, evidence='E03')  # prerequisite enforced server-side
        self.fail('interview', a['token'], revision=0, suspect='p2', topic='y1')
        self.call('inspect', a['token'], revision=0, evidence='E01')
        self.call('interview', a['token'], revision=1, suspect='p2', topic='y1')


if __name__ == '__main__':
    unittest.main()
