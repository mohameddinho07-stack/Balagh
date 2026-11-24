"""Encrypted durable role-game snapshots. No untrusted object deserialization."""
import base64
import hashlib
import hmac
import json
import random
import time
import urllib.request
import urllib.error
from cryptography.fernet import Fernet, InvalidToken
from night import Game, GameError, DEFAULTS


def pack(game):
    state = {k: v for k, v in vars(game).items() if k not in ('rng', 'clock', 'proposed')}
    state['proposed'] = [[a, b, v] for (a, b), v in game.proposed.items()]
    state['_rng'] = game.rng.getstate()
    return json.dumps(state, ensure_ascii=False).encode()


def unpack(data, clock=None):
    state = json.loads(data)
    def tuples(x):
        return tuple(tuples(v) for v in x) if isinstance(x, list) else x
    rng = state.pop('_rng')
    proposed = state.pop('proposed')
    game = Game(clock=clock or time.time)
    vars(game).update(state)
    game.proposed = {(a, b): v for a, b, v in proposed}
    _migrate(game)
    game.rng = random.Random()
    game.rng.setstate(tuples(rng))
    return game


def _migrate(game):
    """Read snapshots saved by the first version of the mode (one claimed place, no card flags).
    Only the in-memory object changes; the stored row is untouched until a normal player action saves it."""
    game.cfg = dict(DEFAULTS, **game.cfg)
    for c in game.cards.values():
        c.setdefault('masked', False)
        c.setdefault('spoiled', False)
    if game.truth and game.statements:
        m = game.truth['m']
        for name, claim in list(game.statements.items()):
            if isinstance(claim, str):
                route = list(game.truth['pos'][name])
                route[m] = claim
                game.statements[name] = route
    if any(c.get('spoiled') for c in game.cards.values()):
        game.forge_used = True


class DurableStore:
    def __init__(self, url, public_key, master, transport=None, clock=None):
        if not isinstance(master, str) or len(master) < 40:
            raise GameError('إعداد حفظ الليلة ناقص')
        self.url, self.public_key, self.master = url, public_key, master.encode()
        self.transport = transport or self._http
        self.clock = clock or time.time

    def _keys(self, code):
        if not isinstance(code, str) or len(code) != 10 or any(c not in '0123456789ABCDEF' for c in code):
            raise GameError('كود الأوضة مش صحيح')
        def derive(label):
            return hmac.new(self.master, (label + ':' + code).encode(), hashlib.sha256).digest()
        return derive('balagh-night-storage-v1').hex(), Fernet(base64.urlsafe_b64encode(derive('balagh-night-encryption-v1')))

    def _http(self, body):
        req = urllib.request.Request(self.url.rstrip('/') + '/rest/v1/rpc/balagh_night_store',
            data=json.dumps(body).encode(), headers={'apikey': self.public_key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except (OSError, ValueError):
            raise GameError('الحفظ مش متاح دلوقتي. آخر خطوة مؤكدة محفوظة؛ جرّب تاني بنفس مفتاحك.') from None

    def load(self, code):
        cap, cipher = self._keys(code)
        out = self.transport(dict(op='read', code=code, capability=cap))
        if not out.get('found'):
            raise GameError('الكود ده مش موجود')
        try:
            game = unpack(cipher.decrypt(out['snapshot'].encode()), self.clock)
        except (InvalidToken, ValueError, KeyError):
            raise GameError('تعذر فتح الحفظ. مفيش بيانات خاصة اتعرضت.') from None
        return game, out['revision']

    def save(self, code, game, expected, create=False):
        cap, cipher = self._keys(code)
        out = self.transport(dict(op='create' if create else 'commit', code=code, capability=cap,
            expected=expected, snapshot=cipher.encrypt(pack(game)).decode()))
        if not out.get('ok'):
            raise GameError('الأوضة اتحدّثت من جهاز تاني. حدّثها وجرّب نفس الخطوة.')
        return out['revision']

    def read(self, code, token):
        game, revision = self.load(code)
        before = game.rev
        view = game.view(token)
        if game.rev != before:
            self.save(code, game, revision)
        return view

    def act(self, code, token, op, payload=None):
        game, revision = self.load(code)
        if op == 'start':
            game.start(token)
            view = game.view(token)
        else:
            view = game.act(token, op, payload)
        self.save(code, game, revision)
        return view
