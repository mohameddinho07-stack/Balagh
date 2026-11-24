"""Shared pilot layer: lighter entry, evidence confrontation, place mood.

Every table is keyed by case id and is plain data. A new case adds entries here
and inherits the same screens in every mode. Nothing here holds a solution:
a confrontation only re-opens an interview question that the server already
gates on its own evidence prerequisites.
"""

INTRO = {
 '001': [
  ('الريسبشن', 'يا فندم، الجناح مقفول من جوّه، وأنا مش هفتحه ولو جبتوا لي ترقية.'),
  ('عامل الغرف', 'خبّطت تلات مرات. الرد الوحيد كان صوت التكييف، والتكييف مش شاهد.'),
  ('إنت', 'ساعة واقفة، وباب مقفول، وكلام محتاج يتراجع. تمام، نبدأ.'),
 ],
 '002': [
  ('المخيم', 'البحر بيطلع وينزل من غير ما يهتم. بس محمد دينهو ما رجعش لخيمته.'),
  ('واحد من الصحاب', 'والله إحنا جايين نتفسح! والباقيين بصّوا له بصة تانية خالص.'),
  ('إنت', 'نار نازلة نعسانة، وأربع كوبايات شاي كأنها حجّة. نبدأ بالمكان.'),
 ],
 '003': [
  ('الراديو', 'المركب راسي والنجدة اتبعتت. وعادل بهجت مش بيرد.'),
  ('القبطان', 'مية على مدّ البصر، ولا جيران ولا شبكة ولا مطعم كشري.'),
  ('إنت', 'الهدوء هنا مش راحة، الهدوء هنا بيسمعك وإنت بتفكر. افتح أول ملف.'),
 ],
}

MOOD = {
 '001': dict(color='#d9a441', line='ممرات فندق قديم على النيل. ريحة سجاد، ونور أصفر تعبان، وكل باب وراه حكاية.'),
 '002': dict(color='#e0b25c', line='رمل وجبل وبحر في ضهرهم. الصوت الوحيد موجة بعيدة، والنور بيخفت واحد واحد.'),
 '003': dict(color='#7fb5b0', line='مية ساكنة على مدّ البصر. مفيش حد قريب، ومفيش مكان تهرب له.'),
}

# person id, statement already heard, evidence the player has earned -> question to re-open.
CONFRONT = {
 '002': [
  dict(person='bassem', statement='s204', evidence='E05', unlocks='s205'),
  dict(person='bassem', statement='s205', evidence='E06', unlocks='s206'),
  dict(person='bassem', statement='s206', evidence='E08', unlocks='s207'),
 ],
}
WRONG = 'ده مش بيقول لي حاجة. جرّب دليل تاني على نفس الكلام.'


def confront_only(case_id):
    """Question ids reached only through a confrontation, so they are not plain menu items."""
    return {c['unlocks'] for c in CONFRONT.get(case_id, [])}


def intro_beats(case_id):
    return list(INTRO.get(case_id, []))


def mood(case_id):
    return MOOD.get(case_id)


def confront_people(case, state):
    ids = {c['person'] for c in CONFRONT.get(case['id'], [])}
    return [p for p in case['characters'] if p['id'] in ids]


def heard_statements(case, state, person_id):
    person = next((p for p in case['characters'] if p['id'] == person_id), None)
    if not person:
        return []
    heard = {x['question_id'] for x in state['interviews']}
    used = {c['statement'] for c in CONFRONT.get(case['id'], []) if c['person'] == person_id}
    return [{'id': q['id'], 'answer': q['answer']} for q in person['interviews'] if q['id'] in heard and q['id'] in used]


def resolve_confront(case, state, person_id, statement_id, evidence_id):
    """Return (kind, payload). kind: unlock, wrong, done or error. Does not change state."""
    if state['finished']:
        return 'error', 'التحقيق خلص.'
    if evidence_id not in state['discovered']:
        return 'error', 'اختار دليل إنت فحصته فعلًا.'
    if statement_id not in {x['question_id'] for x in state['interviews']}:
        return 'error', 'اختار كلام سمعته منه.'
    pair = next((c for c in CONFRONT.get(case['id'], []) if c['person'] == person_id and c['statement'] == statement_id and c['evidence'] == evidence_id), None)
    if not pair:
        return 'wrong', WRONG
    person = next(p for p in case['characters'] if p['id'] == person_id)
    q = next((q for q in person['interviews'] if q['id'] == pair['unlocks']), None)
    if q is None or not set(q.get('requires', [])) <= set(state['discovered']):
        return 'wrong', 'الدليل ده في الطريق الصح، بس لسه ناقصك حاجة تسنده. كمّل فحص الأدلة.'
    if any(x['question_id'] == q['id'] for x in state['interviews']):
        return 'done', q
    return 'unlock', q


def next_step(case, state, evidence_cards, available_evidence, available_questions):
    """One clear next action, computed only from what the player may already see.

    It reads the public prerequisites of files and questions, never the truth, so it
    cannot point at the solution. Returns (headline, detail, counts).
    """
    done = set(state['discovered'])
    heard = {x['question_id'] for x in state['interviews']}
    cards = evidence_cards(case)
    hidden = confront_only(case['id'])
    counts = dict(evidence=len(done), evidence_total=len(cards), asked=len(heard))
    if state.get('finished'):
        return None, None, counts
    todo = [e for e in available_evidence(case, state) if e['id'] not in done]
    for c in (case['characters'] if done else []):
        for q in available_questions(c, state['discovered']):
            if q['id'] not in heard and q['id'] not in hidden:
                return ('اسأل ' + c['name'], 'من «الأقوال»: «' + q['question'] + '»', counts)
    if todo:
        more = (' وفيه ' + str(len(todo) - 1) + ' ملف تاني متاح.') if len(todo) > 1 else ''
        return ('افحص «' + todo[0]['title'] + '»',
                'افتحه من «المكان» أو «المحضر»، اقراه، وسجّل إنك فحصته. كل فحص بيفتح أسئلة أو ملفات جديدة.' + more, counts)
    for pair in CONFRONT.get(case['id'], []):
        if pair['statement'] in heard and pair['evidence'] in done and pair['unlocks'] not in heard:
            who = next((p['name'] for p in case['characters'] if p['id'] == pair['person']), '')
            return ('واجه ' + who + ' بدليل', 'افتح «واجهه حد بدليل» تحت، واختار كلامه والدليل اللي فحصته.', counts)
    return ('جمّعت اللي تقدر عليه',
            'قارن أقوالهم بالأدلة، وارجع للأقوال لو حابب. لما تبقى مقتنع، اتهم من آخر الصفحة بالدليل اللي يسنده.', counts)
