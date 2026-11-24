"""حيطة التحقيق: pinned cards, theory links and timeline placement. Pilot: case 001.

Every examined evidence file and every heard answer becomes one card. The same
cards feed the wall (الحيطة), the night timeline (الخط الزمني) and the live
interrogation (الاستجواب). Linking two or three pinned cards records a theory:
authored pairs hold and turn into a confrontation card, anything else stays an
open note with no penalty and no contradiction revealed. Placing cards on the
timeline never judges order; each card carries its own time badge so a clash
stays visible without the game saying "wrong". No timers anywhere.

Deterministic rules only: no network, no AI. The room server mirrors the same
validation through the generated catalog (see room_catalog and rooms_v2.sql).
"""
from game_engine import evidence_cards, TIMELINE_FACTS
import pilot  # attribute lookups stay fresh across app.py's importlib.reload(pilot)

BOARD_CASES = {'001'}

# Ordered night slots for free, tap-friendly placement. Stored raw; display
# copy (Egyptian daypart) is produced at render time, like every other time.
TIMELINE_SLOTS = {
    '001': ['20:00', '21:00', '21:30', '22:00', '22:30', '23:00', '23:30',
            '00:00', '01:00', '02:00'],
}

# What the speaker claims the time was, for statement cards that carry one.
# A claim is shown as a claim, next to evidenced times, never merged with them.
CLAIMED_TIMES = {
    '001': {'n1': '22:00', 'a2': '22:50', 'l2': '22:40', 'y2': '23:22'},
}

# Authored reading of each confrontation pair: why the two cards clash.
CONFRONT_THEORY_TEXT = {
    '001': {
        'n1': ('معاد مشيتها',
               'نادين بتقول إنها مشيت الساعة 22:00، ودفتر الزيارة بإمضتها بيثبت إنها كانت عند نادر 22:58. الكلامين مش بيتفقوا.'),
        'n2': ('الزيارة والكوباية',
               'بعد ما اعترفت إنها رجعت، تحليل الكوباية بيربط المادة بتقديمها هي. الكارت ده يفتح السؤال اللي وراه.'),
        'n3': ('من غير تفسير',
               'ماعندهاش تفسير لنتيجة الكوباية، والرسايل بتورّي إن نادر كان بيهدد شغلها وحياتها الخاصة. الدافع بقى باين.'),
        'n4': ('الخوف والتسلسل',
               'قالت إنها كانت خايفة من التهديد، ورسالة نادر للريسبشن بتثبت إنه أمّن الباب بنفسه بعد الزيارة وقبل موته. التسلسل بيكمّل الصورة.'),
    },
}

MAX_PINS = 40
MAX_THEORIES = 30


def board_supported(case):
    return case['id'] in BOARD_CASES


def board_state(state):
    board = state.setdefault('board', {'pins': [], 'theories': [], 'placed': {}})
    if not isinstance(board.get('pins'), list) or not all(isinstance(x, str) for x in board['pins']):
        raise ValueError('حالة الحيطة مش سليمة.')
    if not isinstance(board.get('theories'), list) or len(board['theories']) > MAX_THEORIES:
        raise ValueError('حالة الحيطة مش سليمة.')
    if not isinstance(board.get('placed'), dict):
        raise ValueError('حالة الحيطة مش سليمة.')
    return board


def case_theories(case):
    """Authored card sets that hold: reasoning deductions + confrontation pairs."""
    theories = []
    for link in case.get('reasoning', []):
        theories.append({'id': link['id'], 'cards': sorted(link['evidence']), 'kind': 'deduction',
                         'title': link['title'], 'text': link['text']})
    for pair in pilot.CONFRONT.get(case['id'], []):
        title, text = CONFRONT_THEORY_TEXT.get(case['id'], {}).get(
            pair['statement'], ('كلام متناقض', 'الكارتين دول مش بيتفقوا مع بعض.'))
        theories.append({'id': 'cf_' + pair['statement'], 'cards': sorted([pair['statement'], pair['evidence']]),
                         'kind': 'confront', 'person': pair['person'], 'statement': pair['statement'],
                         'evidence': pair['evidence'], 'unlocks': pair['unlocks'],
                         'title': title, 'text': text})
    return theories


def board_cards(case, state):
    """Cards earned so far: examined evidence + heard answers. One set for all three tools."""
    discovered = set(state['discovered'])
    heard = {entry['question_id'] for entry in state['interviews']}
    cards = []
    for e in evidence_cards(case):
        if e['id'] in discovered:
            cards.append({'id': e['id'], 'kind': 'evidence', 'title': e['title'], 'text': e['text']})
    for person in case['characters']:
        for q in person['interviews']:
            if q['id'] in heard:
                cards.append({'id': q['id'], 'kind': 'statement', 'title': person['name'],
                              'text': q['answer'], 'person': person['id'],
                              'question': q['question']})
    return cards


def card_times(case, card):
    """Authored time badges for a card: evidenced times, or the speaker's claimed time."""
    if card['kind'] == 'statement':
        claimed = CLAIMED_TIMES.get(case['id'], {}).get(card['id'])
        return [{'time': claimed, 'claim': True}] if claimed else []
    return [{'time': time, 'claim': False}
            for time, _text, ids in TIMELINE_FACTS.get(case['id'], []) if card['id'] in ids]


def theory_lookup(case, entry):
    """The authored theory behind a recorded holds-entry, or None for open ones."""
    theory_id = entry.get('theory_id')
    if entry.get('status') != 'holds' or not theory_id:
        return None
    return next((t for t in case_theories(case) if t['id'] == theory_id), None)


def board_action(case, state, payload):
    """Validate and apply one board action. Returns the matched theory for 'link', else None.

    Raises ValueError with a player-facing Arabic message on any invalid move.
    """
    if not board_supported(case):
        raise ValueError('حيطة التحقيق لسه تجربة في بلاغ الغرفة المغلقة بس.')
    if state['finished']:
        raise ValueError('التحقيق خلص.')
    board = board_state(state)
    if not isinstance(payload, dict):
        raise ValueError('طلب الحيطة مش سليم.')
    do = payload.get('do')
    known = {c['id'] for c in board_cards(case, state)}
    if do == 'pin':
        card = payload.get('card', '')
        if card not in known:
            raise ValueError('الكارت ده لسه مش عندك. افحص الدليل أو اسمع الرد الأول.')
        if card not in board['pins']:
            if len(board['pins']) >= MAX_PINS:
                raise ValueError('الحيطة مليانة. شيل كروت مش محتاجها.')
            board['pins'].append(card)
        return None
    if do == 'unpin':
        card = payload.get('card', '')
        board['pins'] = [p for p in board['pins'] if p != card]
        board['placed'].pop(card, None)
        return None
    if do == 'link':
        cards = sorted(set(payload.get('cards', [])))
        if not 2 <= len(cards) <= 3 or not all(isinstance(x, str) for x in cards):
            raise ValueError('اختار كارتين أو تلاتة.')
        if not set(cards) <= set(board['pins']):
            raise ValueError('اختار كروت مثبتة على الحيطة.')
        if any(sorted(t['cards']) == cards for t in board['theories']):
            raise ValueError('النظرية دي متسجلة على الحيطة خلاص.')
        if len(board['theories']) >= MAX_THEORIES:
            raise ValueError('وصلت لحد النظريات على الحيطة.')
        match = next((t for t in case_theories(case) if t['cards'] == cards), None)
        entry = {'cards': cards, 'status': 'holds' if match else 'open'}
        if match:
            entry['theory_id'] = match['id']
        board['theories'].append(entry)
        return match
    if do == 'unlink':
        index = payload.get('index')
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(board['theories']):
            raise ValueError('النظرية دي مش موجودة.')
        board['theories'].pop(index)
        return None
    if do == 'place':
        card = payload.get('card', '')
        slot = payload.get('slot', '')
        if card not in board['pins']:
            raise ValueError('ثبّت الكارت على الحيطة الأول.')
        if slot not in TIMELINE_SLOTS.get(case['id'], []):
            raise ValueError('الخانة دي مش على خط الليلة.')
        board['placed'][card] = slot
        return None
    if do == 'unplace':
        board['placed'].pop(payload.get('card', ''), None)
        return None
    raise ValueError('طلب الحيطة مش مفهوم.')


def catalog_theories(case):
    """Server-side copy of the authored theory sets (sorted cards for exact matching)."""
    return [{'id': t['id'], 'cards': t['cards'], 'kind': t['kind'], 'title': t['title'], 'text': t['text'],
             **({'person': t['person'], 'unlocks': t['unlocks']} if t['kind'] == 'confront' else {})}
            for t in case_theories(case)]
