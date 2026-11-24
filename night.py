"""Balagh 'قاتل وظابط مباحث' rules engine. Private prototype, pure stdlib, no I/O.
Mirrors the shape of the live room API: one entry point per op, keyed by a player token,
server holds truth, every response is a per-player projection (view)."""
import hashlib, secrets, random, json

ROLE_KILLER = 'قاتل'
ROLE_COP = 'ظابط مباحث'
PLACES = ['الجنينة', 'السطح', 'الصالة', 'الحمام']
BATH = 'الحمام'
SCENES = ['الجنينة', 'السطح', 'الصالة']
SLOTS = ['٩', '١٠', '١١']  # مساءً
ROUNDS = 3

class GameError(Exception):
    pass

DEFAULTS = dict(p_murder_slot=0.34, chances=2, min_witnesses=2, need_contradictions=2,
                search_secs=45, talk_secs=180, killers_from=99, max_players=7, scene_forbidden=True, p_mask=0.35)  # first playable: 4-7 players, one killer

def n_killers(n, cfg):
    return 2 if n >= cfg['killers_from'] else 1

# ---------- night generation (rules + randomness, no model) ----------
def gen_night(rng, names, killers, cfg):
    """Truth: pos[name][slot] -> place. Rejection-sample until playable."""
    for attempt in range(1, 500):
        m = rng.randrange(3)
        scene = rng.choice(SCENES)
        pos = {n: [rng.choice(PLACES) for _ in SLOTS] for n in names}
        for k in killers:
            pos[k][m] = scene
        wit = [n for n in names if n not in killers and pos[n][m] == scene]
        if len(wit) >= min(cfg['min_witnesses'], len(names) - len(killers)):
            return dict(m=m, scene=scene, pos=pos, attempts=attempt)
    raise GameError('night generation failed')

def seen_at(truth, who, slot, place):
    if place == BATH:
        return []
    return sorted(n for n, p in truth['pos'].items() if p[slot] == place and n != who)

def contradicts(card, stmt_owner, stmt_place, m):
    """Does this public card contradict stmt_owner's statement 'I was at stmt_place at slot m'?"""
    if card['slot'] != m or card['owner'] == stmt_owner:
        return False
    if card['place'] == stmt_place and stmt_place != BATH and stmt_owner not in card['seen']:
        return True   # witness stood where he claims and did not see him
    if card['place'] != stmt_place and stmt_owner in card['seen']:
        return True   # seen somewhere else
    return False

class Game:
    def __init__(self, seed=None, cfg=None, clock=None):
        self.cfg = dict(DEFAULTS, **(cfg or {}))
        self.rng = random.Random(seed)
        self.clock = clock or (lambda: 0.0)
        self.players = []        # dicts: id, name, hash, role, ...
        self.phase = 'lobby'
        self.round = 0
        self.rev = 0
        self.truth = None
        self.cards = {}          # id -> card (server side, with owner)
        self.public_cards = []   # ids
        self.statements = {}     # name -> place (set at alibi phase end)
        self.submitted = {}      # round-phase submissions: name -> dict
        self.spoiled = None
        self.proposal = None
        self.chances = self.cfg['chances']
        self.caught = []
        self.result = None
        self.deadline = None
        self.log = []            # public log lines
        self.proposed = {}
        self.forge_used = False   # the killers get ONE forged clue per night
        self.refuted = []         # ids of forged cards that players proved fake

    # ----- helpers -----
    def _bump(self):
        self.rev += 1
    def _by_token(self, token):
        if not isinstance(token, str) or len(token) != 64:
            raise GameError('مفتاح الرجوع مش صحيح')
        h = hashlib.sha256(token.encode()).hexdigest()
        for p in self.players:
            if secrets.compare_digest(p['hash'], h):
                return p
        raise GameError('مفتاح الرجوع مش صحيح')
    def _pub(self, line):
        self.log.append(line)
    def _tick(self):
        if self.result is None and self.deadline is not None and self.clock() >= self.deadline:
            self._advance(forced=True)

    # ----- ops -----
    def join(self, name):
        name = (name or '').strip()
        if self.phase != 'lobby':
            raise GameError('اللعبة بدأت خلاص')
        if not 1 <= len(name) <= 30:
            raise GameError('اسم اللاعب من 1 لحد 30 حرف')
        if len(self.players) >= self.cfg['max_players']:
            raise GameError('الأوضة كاملة')
        if any(p['name'] == name for p in self.players):
            raise GameError('الاسم ده مستخدم')
        token = secrets.token_hex(32)
        self.players.append(dict(name=name, hash=hashlib.sha256(token.encode()).hexdigest(),
                                 role=None, host=not self.players))
        self._bump()
        return token

    def start(self, token):
        p = self._by_token(token)
        if self.phase != 'lobby':
            raise GameError('اللعبة بدأت خلاص')
        if not p['host']:
            raise GameError('اللي عمل الأوضة هو اللي يبدأ')
        n = len(self.players)
        if n < 4:
            raise GameError('محتاجين 4 لاعبين على الأقل')
        names = [q['name'] for q in self.players]
        kc = n_killers(n, self.cfg)
        ks = self.rng.sample(names, kc)
        for q in self.players:
            q['role'] = ROLE_KILLER if q['name'] in ks else ROLE_COP
        self.killers = ks
        self.truth = gen_night(self.rng, names, ks, self.cfg)
        self.phase = 'alibi'
        self.round = 0
        self.submitted = {}
        self.deadline = self.clock() + self.cfg['search_secs']
        self._pub('النور قطع في %s، وعم فتحي اتلقى ميت. محدش عارف حصل الساعة كام بالظبط: بين ٩ و١١.' % self.truth['scene'])
        self._bump()

    def act(self, token, op, payload=None):
        payload = payload or {}
        p = self._by_token(token)
        self._tick()
        if op == 'read':
            return self.view(token)
        if self.phase in ('lobby', 'ended'):
            raise GameError('مش وقت الطلب ده')
        if op == 'alibi':
            self._alibi(p, payload)
        elif op == 'search':
            self._search(p, payload)
        elif op == 'publish':
            self._publish(p, payload)
        elif op == 'propose':
            self._propose(p, payload)
        elif op == 'approve':
            self._approve(p, payload)
        elif op == 'challenge':
            self._challenge(p, payload)
        elif op == 'next':
            if not p['host']:
                raise GameError('صاحب الأوضة بس')
            self._advance(forced=True)
        else:
            raise GameError('طلب مش مسموح')
        return self.view(token)

    def _alibi(self, p, payload):
        if self.phase != 'alibi':
            raise GameError('مش وقت الحجة')
        place = payload.get('place')
        if place not in PLACES:
            raise GameError('مكان مش موجود')
        if p['role'] != ROLE_KILLER:
            raise GameError('مش وقت الحجة')   # same text: no role oracle through errors
        if p['name'] in self.submitted:
            raise GameError('حجتك اتسجلت خلاص')
        if place == self.truth['scene'] and self.cfg['scene_forbidden']:
            raise GameError('ده مكان الجريمة، اختار حجة تانية')   # claiming the scene is un-catchable (sim: cop win 1-6%)
        self.submitted[p['name']] = dict(place=place)
        self._bump()
        # a detective-side 'alibi' submission is not needed; phase ends when all killers committed
        if all(k in self.submitted for k in self.killers):
            self._advance()

    def _search(self, p, payload):
        if self.phase != 'search':
            raise GameError('مش وقت التفتيش')
        spot = payload.get('spot')
        if spot not in PLACES:
            raise GameError('مكان مش موجود')
        if p['name'] in self.submitted:
            raise GameError('اختيارك اتسجل خلاص')
        rec = dict(spot=spot)
        if p['role'] == ROLE_KILLER:
            sp = payload.get('spoil')
            if sp is not None:
                if sp not in PLACES:
                    raise GameError('مكان مش موجود')
                rec['spoil'] = sp
        # uniform for all roles: a spoil key from a cop is silently ignored (no role oracle)
        self.submitted[p['name']] = rec
        self._bump()
        if len(self.submitted) == len(self.players):
            self._advance()

    def _publish(self, p, payload):
        cid = payload.get('card')
        c = self.cards.get(cid)
        if c is None or c['owner'] != p['name']:
            raise GameError('الكارت مش موجود')
        if cid not in self.public_cards:
            self.public_cards.append(cid)
            self._pub('%s حط كارت على الترابيزة.' % p['name'])
            self._bump()

    def _propose(self, p, payload):
        if self.phase != 'talk':
            raise GameError('الاتهام وقت الكلام بس')
        names = [q['name'] for q in self.players]
        sus = payload.get('suspect'); ids = payload.get('cards')
        if sus not in names or not isinstance(ids, list) or len(ids) != 2 or len(set(ids)) != 2 \
           or any(i not in self.public_cards for i in ids):
            raise GameError('اختار متهم وكارتين على الترابيزة')
        if any(self.cards[i]['kind'] == 'link' for i in ids):
            raise GameError('اختار متهم وكارتين على الترابيزة')
        if any(i in self.refuted for i in ids):
            raise GameError('الكارت ده اتكشف إنه مزوّر')
        if any(not self._slot_known(self.cards[i]) for i in ids):
            raise GameError('ساعة كارت من دول لسه مش معروفة. حطوا كارت الربط على الترابيزة الأول.')
        if sus == p['name']:
            raise GameError('مينفعش تتهم نفسك')
        key = (p['name'], self.round)
        if self.proposed.get(key):
            raise GameError('اقتراح واحد في الجولة لكل لاعب')   # stops a killer overwriting/stalling proposals
        self.proposed[key] = True
        self.proposal = dict(suspect=sus, cards=list(ids), approvals=[p['name']], by=p['name'])
        self._bump()
        self._maybe_close_proposal()

    def _approve(self, p, payload):
        pr = self.proposal
        if self.phase != 'talk' or pr is None:
            raise GameError('مفيش اتهام مطروح')
        if payload.get('suspect') != pr['suspect'] or payload.get('cards') != pr['cards']:
            raise GameError('الاتهام اتغيّر، راجعه')
        if p['name'] == pr['suspect']:
            raise GameError('المتهم مش بيصوّت')
        if p['name'] in pr['approvals']:
            raise GameError('إنت وافقت خلاص')
        pr['approvals'].append(p['name'])
        self._bump()
        self._maybe_close_proposal()

    def _maybe_close_proposal(self):
        pr = self.proposal
        need = len(self.players) // 2 + 1
        if len(pr['approvals']) < need:
            return
        sus = pr['suspect']
        self.proposal = None
        is_k = sus in self.killers
        hits = [c for c in pr['cards']
                if contradicts(self.cards[c], sus, self.statements[sus][self.cards[c]['slot']], self.cards[c]['slot'])]
        ok = is_k and len(hits) >= self.cfg['need_contradictions'] and sus not in self.caught
        if ok:
            self.caught.append(sus)
            self._pub('اتهام %s اتثبت: تناقض حقيقي في كلامه.' % sus)
            if len(self.caught) >= len(self.killers):
                self._end('ظابط مباحث', 'القاتل اتقفش')
            else:
                self._pub('لسه فيه قاتل تاني.')
        else:
            self.chances -= 1
            # uniform failure message: never reveals whether the accused is innocent or just under-evidenced
            self._pub('اتهام %s ما اتثبتش. فاضل %d محاولة.' % (sus, self.chances))
            if self.chances <= 0:
                self._end('القاتل', 'المحاولات خلصت')
        self._bump()

    def _end(self, winner, why):
        self.phase = 'ended'
        self.deadline = None
        self.result = dict(winner=winner, why=why, killers=list(self.killers),
                           truth=dict(m=SLOTS[self.truth['m']], scene=self.truth['scene'],
                                      pos=self.truth['pos']))
        self._pub('خلصت الليلة: %s كسب.' % winner)

    def _slot_pick(self):
        m = self.truth['m']
        return m if self.rng.random() < self.cfg['p_murder_slot'] else self.rng.choice([i for i in range(3) if i != m])

    def _new_card(self, owner, kind, slot, place, seen, spoiled=False, masked=False):
        cid = secrets.token_hex(3)
        while cid in self.cards:
            cid = secrets.token_hex(3)
        self.cards[cid] = dict(id=cid, owner=owner, kind=kind, slot=slot, place=place, seen=list(seen),
                               round=self.round, spoiled=spoiled, masked=masked)
        return self.cards[cid]

    def _testimony(self, owner, slot=None, masked=None):
        t = self.truth
        slot = self._slot_pick() if slot is None else slot
        place = t['pos'][owner][slot]
        mk = (self.rng.random() < self.cfg['p_mask']) if masked is None else masked
        return self._new_card(owner, 'testimony', slot, place, seen_at(t, owner, slot, place), masked=mk)

    def _slot_known(self, c, visited=None):
        """A card's hour is usable when it is not hidden, or a link card on the table ties it to a card with a known hour."""
        if c['kind'] == 'link' or not c.get('masked'):
            return True
        visited = (visited or set()) | {c['id']}
        for lid in self.public_cards:
            L = self.cards[lid]
            if L['kind'] != 'link' or c['id'] not in (L['a'], L['b']):
                continue
            other = L['b'] if L['a'] == c['id'] else L['a']
            if other in visited or other not in self.public_cards:
                continue
            if self._slot_known(self.cards[other], visited):
                return True
        return False

    def _conflict(self, a, b):
        """True when card b (someone's own testimony) says the opposite of what card a says about the same hour."""
        if a['kind'] == 'link' or b['kind'] != 'testimony' or a['slot'] != b['slot']:
            return False
        return b['owner'] in a['seen'] and b['place'] != a['place']

    def _challenge(self, p, payload):
        if self.phase != 'talk':
            raise GameError('الاعتراض وقت الكلام بس')
        ids = payload.get('cards')
        if not isinstance(ids, list) or len(ids) != 2 or len(set(ids)) != 2 \
           or any(i not in self.public_cards for i in ids):
            raise GameError('اختار كارتين من الترابيزة')
        a, b = self.cards[ids[0]], self.cards[ids[1]]
        if a['kind'] == 'link' or b['kind'] == 'link' or not (self._slot_known(a) and self._slot_known(b)):
            raise GameError('مفيش تناقض واضح بين الكارتين دول')
        for x, y in ((a, b), (b, a)):
            if self._conflict(x, y):
                bad = x if x['spoiled'] else (y if y['spoiled'] else None)
                if bad is not None and bad['id'] not in self.refuted:
                    self.refuted.append(bad['id'])
                    self._pub('كارت %s اتكشف إنه مزوّر. ما ينفعش يتستخدم في اتهام.' % bad['id'])
                    self._bump()
                    return
                if bad is not None:
                    raise GameError('الكارت ده اتكشف قبل كده')
        raise GameError('مفيش تناقض واضح بين الكارتين دول')

    def _advance(self, forced=False):
        t = self.truth
        if self.phase == 'alibi':
            for q in self.players:
                n = q['name']
                route = list(t['pos'][n])
                if q['role'] == ROLE_KILLER:
                    route[t['m']] = self.submitted.get(n, {}).get('place') or self.rng.choice([x for x in PLACES if x != t['scene']])
                self.statements[n] = route
            self._pub('كل واحد قال كان فين الساعة ٩ و١٠ و١١. واحد بس كدب في ساعة من التلاتة.')
            self.round = 1
            self._start_search()
        elif self.phase == 'search':
            self._resolve_search()
            self.phase = 'talk'
            self.proposal = None
            self.deadline = self.clock() + self.cfg['talk_secs']
            self._pub('الجولة %d: اتكلموا بصوتكم. حطوا كروتكم لو عاوزين.' % self.round)
        elif self.phase == 'talk':
            if self.round >= ROUNDS:
                self._end('القاتل', 'الليلة خلصت من غير ما حد يتثبت عليه')
            else:
                self.round += 1
                self._start_search()
        self._bump()

    def _start_search(self):
        self.phase = 'search'
        self.submitted = {}
        self.deadline = self.clock() + self.cfg['search_secs']
        self.spoiled = None

    def _resolve_search(self):
        t = self.truth
        m = t['m']
        names = [q['name'] for q in self.players]
        spoil = None
        for k in self.killers:
            sp = self.submitted.get(k, {}).get('spoil')
            if sp:
                spoil = sp
        new = []
        for q in self.players:
            n = q['name']
            new.append(self._testimony(n))
            spot = self.submitted.get(n, {}).get('spot') or self.rng.choice(PLACES)
            slot = self._slot_pick()
            seen = seen_at(t, None, slot, spot)
            c = self._new_card(n, 'clue', slot, spot, seen, masked=self.rng.random() < self.cfg['p_mask'])
            new.append(c)
            if not self.forge_used and spoil and spot == spoil and q['role'] != ROLE_KILLER and spot != BATH:
                seen_m = seen_at(t, None, m, spot)
                pool = [x for x in names if x not in self.killers and t['pos'][x][m] != spot and x not in seen_m]
                if pool:
                    victim = self.rng.choice(pool)
                    c.update(slot=m, seen=sorted(seen_m + [victim]), spoiled=True, masked=False)
                    self.forge_used = True
                    new.append(self._testimony(victim, slot=m, masked=False))   # the truth that disproves the forgery
        # link cards: tie each hidden-hour card to a card whose hour is plain
        for c in list(new):
            if not c['masked']:
                continue
            plain = [x for x in self.cards.values() if x['kind'] != 'link' and not x['masked'] and x['slot'] == c['slot']]
            if not plain:
                c['masked'] = False
                continue
            d = self.rng.choice(plain)
            owner = self.rng.choice([x for x in names if x != c['owner']])
            L = self._new_card(owner, 'link', None, None, [], masked=False)
            L['a'], L['b'] = c['id'], d['id']
        if self.round >= ROUNDS:
            self._guarantee_evidence()
        self.spoiled = None

    def _guarantee_evidence(self):
        """Fairness floor: by the last round the table can always catch the killer with plain true cards."""
        t = self.truth
        m = t['m']
        need = self.cfg['need_contradictions']
        wit = [n for n in t['pos'] if n not in self.killers and t['pos'][n][m] == t['scene']]
        for k in self.killers:
            claim = self.statements[k][m]
            def hits():
                return [c for c in self.cards.values() if c['kind'] != 'link' and not c['spoiled'] and not c['masked']
                        and c['slot'] == m and contradicts(c, k, claim, m)]
            have = {c['owner'] for c in hits()}
            for w in sorted(wit, key=lambda w: w in have):
                if len(hits()) >= need:
                    break
                self._testimony(w, slot=m, masked=False)

    # ----- projection -----
    def _fmt(self, c, me=None):
        pub = c['id'] in self.public_cards
        owner = c['owner'] if pub else None
        if c['kind'] == 'link':
            return dict(id=c['id'], kind='link', slot=None, place=None, seen=[], owner=owner,
                        a=c['a'] if pub or self.cards[c['a']]['owner'] == me else None,
                        b=c['b'] if pub or self.cards[c['b']]['owner'] == me else None,
                        masked=False, refuted=False)
        known = self._slot_known(c)
        return dict(id=c['id'], slot=SLOTS[c['slot']] if known else '؟', place=c['place'], seen=list(c['seen']),
                    kind=c['kind'], owner=owner, masked=bool(c['masked']) and not known,
                    refuted=c['id'] in self.refuted)

    def view(self, token):
        p = self._by_token(token)
        self._tick()
        me = p['name']
        mine = [self._fmt(c, me) for c in self.cards.values() if c['owner'] == me]
        pub = [self._fmt(self.cards[i]) for i in self.public_cards]
        v = dict(rev=self.rev, phase=self.phase, round=self.round, rounds=ROUNDS, chances=self.chances,
                 me=me, host=p['host'], players=[q['name'] for q in self.players],
                 killer_count=(n_killers(len(self.players), self.cfg) if self.phase != 'lobby' else None),
                 role=p['role'],
                 statements=dict(self.statements) if self.statements else {},
                 board=pub, my_cards=mine, log=list(self.log),
                 submitted_count=len(self.submitted) if self.phase == 'search' else None,
                 i_submitted=(me in self.submitted) if self.phase in ('search', 'alibi') else None,
                 proposal=(dict(suspect=self.proposal['suspect'], cards=self.proposal['cards'],
                                approvals=list(self.proposal['approvals'])) if self.proposal else None),
                 seconds_left=(max(0, int(self.deadline - self.clock())) if self.deadline is not None else None),
                 result=None)
        if self.phase != 'lobby':
            v['scene'] = self.truth['scene']
            v['murder_slot'] = SLOTS[self.truth['m']] if self.phase == 'ended' else None
            if p['role'] == ROLE_KILLER:
                v['private'] = dict(my_places=list(self.truth['pos'][me]),
                                    partners=[k for k in self.killers if k != me],
                                    forge_left=0 if self.forge_used else 1, murder_slot=SLOTS[self.truth['m']])
            else:
                v['private'] = dict(my_places=list(self.truth['pos'][me]), partners=[], forge_left=0, murder_slot=None)
        if self.phase == 'ended':
            v['result'] = json.loads(json.dumps(self.result))
        return v
