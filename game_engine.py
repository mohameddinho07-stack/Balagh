"""Deterministic game rules. No network calls, AI, or paid services."""
from copy import deepcopy
from data import CASE_001


def generate_case():
    return deepcopy(CASE_001)


def evidence_cards(case):
    return case["evidence"] + [case["verification"]]


def available_questions(suspect, discovered):
    return [q for q in suspect["interviews"] if set(q.get("requires", [])) <= set(discovered)]


def record_answer(case, state, suspect_id, question_id):
    if state["finished"]:
        raise ValueError("التحقيق خلص. جرّب من الأول.")
    suspect = next((s for s in case["characters"] if s["id"] == suspect_id), None)
    if suspect is None:
        raise ValueError("الشخصية دي مش عندنا")
    question = next((q for q in available_questions(suspect, state["discovered"]) if q["id"] == question_id), None)
    if question is None:
        raise ValueError("بصّ على أدلة السؤال ده الأول")
    entry = {"suspect": suspect["name"], "question_id": question_id,
             "question": question["question"], "answer": question["answer"]}
    if not any(x["question_id"] == question_id for x in state["interviews"]):
        state["interviews"].append(entry)
    return entry


def new_investigation():
    return {"discovered": [], "interviews": [], "finished": False,
            "result": None, "hints_used": 0}


def evaluate_accusation(case, suspect_name, submitted_evidence, discovered):
    names = {s["name"] for s in case["characters"]}
    selected = set(submitted_evidence)
    if suspect_name not in names:
        raise ValueError("اختار حد من الناس اللي في القضية")
    if not selected or not selected <= set(discovered):
        raise ValueError("اختار أدلة إنت بصّيت عليها فعلًا")
    valid_ids = {e["id"] for e in evidence_cards(case)}
    if not selected <= valid_ids:
        raise ValueError("الدليل ده مش عندنا")
    killer_correct = suspect_name == case["truth"]["killer"]
    evidence_complete = set(case["truth"]["required_evidence"]) <= selected
    return {"success": killer_correct and evidence_complete,
            "killer_correct": killer_correct, "evidence_complete": evidence_complete,
            "suspect": suspect_name, "submitted_evidence": sorted(selected)}


def finish_investigation(case, state, suspect_name, submitted_evidence):
    if state["finished"]:
        raise ValueError("إنت قلت قرارك الأخير خلاص")
    result = evaluate_accusation(case, suspect_name, submitted_evidence, state["discovered"])
    state["result"] = result
    state["finished"] = True
    return result
