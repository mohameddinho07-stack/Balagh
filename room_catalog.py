"""Builds the server-side case catalog from the case registry.

Every registered case is exported automatically, so a new case inherits solo,
co-op, individual race and team race without any per-case room code. The server
holds answers and the winning verdict; the browser never receives either.
"""
import json
from game_engine import CASE_REGISTRY, generate_case
from ai_interrogation import CONTINUITY
from board import catalog_theories, TIMELINE_SLOTS


def build_catalog(registry=None, generate=None):
    registry = CASE_REGISTRY if registry is None else registry
    generate = generate or generate_case
    out = {}
    for cid in registry:
        case = generate(cid)
        cards = case['evidence'] + [case['verification']]
        names = {c['name'] for c in case['characters']}
        assert case['truth']['killer'] in names, cid
        out[cid] = {
            'evidence': {e['id']: list(e.get('requires', [])) for e in cards},
            'characters': [{'id': c['id'], 'name': c['name'], 'job': c['job'],
                            'interviews': [{'id': q['id'], 'question': q['question'], 'answer': q['answer'],
                                            'requires': list(q.get('requires', []))} for q in c['interviews']]}
                           for c in case['characters']],
            'killer': case['truth']['killer'],
            'required': list(case['truth']['required_evidence']),
            'continuity': [r for r in CONTINUITY + list(case.get('continuity', [])) if r.get('case', cid) == cid],
            # Investigation board pilot: authored theory sets and timeline slots.
            'theories': catalog_theories(case),
            'slots': list(TIMELINE_SLOTS.get(cid, [])),
        }
    return out


def catalog_json(registry=None, generate=None):
    text = json.dumps(build_catalog(registry, generate), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    assert '$' not in text
    return text
