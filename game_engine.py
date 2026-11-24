"""Deterministic game rules. No network calls, AI, or paid services."""
from copy import deepcopy
import re
from data import CASE_001
from cases_extra import CASES_EXTRA
import uuid


def egyptian_time(hour, minute):
    """Isolate the LTR clock inside an RTL phrase; keep its daypart attached."""
    hour = int(hour)
    daypart = ("بعد نص الليل" if hour < 5 else "الصبح" if hour < 12
               else "الضهر" if hour < 15 else "العصر" if hour < 18 else "بليل")
    clock = f"{hour % 12 or 12}:{minute}"
    return "\u2067\u2066" + clock + "\u2069\u00a0" + daypart.replace(" ", "\u00a0") + "\u2069"


def display_times(text):
    # Replace explicit ranges first, with words instead of a bidi-ambiguous dash.
    text = re.sub(r"(?<!\d)([01]\d|2[0-3]):([0-5]\d)[–-]([01]\d|2[0-3]):([0-5]\d)(?!\d)",
                  lambda m: "من " + egyptian_time(m[1], m[2]) + " لحد " + egyptian_time(m[3], m[4]), text)
    return re.sub(r"(?<![\d\u2066])([01]\d|2[0-3]):([0-5]\d)(?![\d\u2069])",
                  lambda m: egyptian_time(m[1], m[2]), text)


def _display_copy(value):
    if isinstance(value, str):
        return display_times(value)
    if isinstance(value, list):
        return [_display_copy(item) for item in value]
    if isinstance(value, dict):
        return {key: _display_copy(item) for key, item in value.items()}
    return value


CASE_REGISTRY = {'001': CASE_001, **CASES_EXTRA}
CASE_001.setdefault('scene', 'hotel')
CASE_001.setdefault('reasoning',[
 {'id':'c101','title':'الساعة مش وقت الوفاة','evidence':['E01','E05'],'text':'فحص البطارية وتقدير الوفاة يفصلوا بين ساعة واقفة ومعاد وفاة.'},
 {'id':'c102','title':'الزيارة والكوباية','evidence':['E06','E07'],'text':'زيارة متراجعة وسلسلة حيازة للكوباية. اسأل مين كان ماسكها ومين قدّمها.'},
 {'id':'c103','title':'الخلاف مش كفاية','evidence':['E07','E08','E09'],'text':'الدافع محتاج فرصة ودليل يربط الشخص بالفعل. حجة مستقلة ممكن تبعد الشك.'}])
CASE_001['public'].update(tagline='باب مقفول من جوّه. ساعة واقفة. وكلام محتاج يتراجع.', difficulty='بداية مناسبة', duration='20–30 دقيقة')

def case_catalog():
    return [{'id':cid, **{k:c['public'].get(k,'') for k in ['title','location','tagline','difficulty','duration']},'scene':c['scene']} for cid,c in CASE_REGISTRY.items()]

def generate_case(case_id='001'):
    # Canonical 24-hour facts stay in data.py; only the displayed copy changes.
    return _display_copy(deepcopy(CASE_REGISTRY[case_id]))


def evidence_cards(case):
    return case["evidence"] + [case["verification"]]


def available_evidence(case, state):
    return [e for e in evidence_cards(case) if set(e.get('requires', [])) <= set(state['discovered'])]


def inspect_evidence(case, state, evidence_id):
    if state['finished']:
        raise ValueError('التحقيق خلص.')
    if evidence_id not in {e['id'] for e in available_evidence(case,state)}:
        raise ValueError('افحص الأدلة المطلوبة الأول.')
    if evidence_id not in state['discovered']:
        state['discovered'].append(evidence_id)


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
    return {"attempt_id":uuid.uuid4().hex,"discovered": [], "interviews": [], "finished": False,
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


def link_evidence(case,state,evidence_ids):
    if not isinstance(evidence_ids,list) or len(evidence_ids)>30 or not all(isinstance(x,str) for x in evidence_ids):raise ValueError('اختار أدلة من المحضر.')
    selected=set(evidence_ids)
    if state['finished']:raise ValueError('التحقيق خلص.')
    if len(selected)<2 or not selected<=set(state['discovered']):raise ValueError('اختار دليلين مفحوصين على الأقل.')
    found=[x for x in case.get('reasoning',[]) if set(x['evidence'])==selected]
    if not found:return None
    link=found[0]
    if link['id'] not in state.setdefault('deductions',[]):state['deductions'].append(link['id'])
    return link


# Timeline entries are hand-authored case facts, never inferred by an AI.
TIMELINE_FACTS = {
 '001': [
  ('22:13','الساعة وقفت عشان البطارية خلصت.',['E05']),
  ('22:50','الكوباية وقت التسليم، قبل الزيارة.',['E07']),
  ('22:58','بداية الزيارة اللي اتراجعت في الدفتر والشهادة.',['E06']),
  ('23:18','نهاية الزيارة وتسليم الكوباية الفاضية.',['E06','E07']),
  ('23:24','نادر قال للريسبشن إنه أمّن الباب.',['E05']),
  ('23:42','وقت الوفاة اللي في تقرير المحضر.',['E01'])],
 '002': [
  ('21:35','صورة المعدات بتوضح علامة الجاكيت.',['E06']),
  ('21:42','أحمد بيقول إنه ساب المعسكر. دي رواية، مش مشاهدة منك.',['E04']),
  ('21:45','بداية نافذة الوفاة، نهايتها 21:55.',['E01']),
  ('21:49','دينهو وشخص بجاكيت فاتح دخلوا الممر.',['E02']),
  ('21:50','وقت التسجيل المحلي والمشادة في المحضر.',['E07']),
  ('21:53','مرافق دينهو ظهر خارج من الممر.',['E07']),
  ('22:00','الفانوس اتطفى بالمؤقّت.',['E05']),
  ('22:12','رجوع أحمد حسب شهادة الرجوع.',['E04'])],
 '003': [
  ('20:00','عهدة المفتاح الاحتياطي M2.',['E02']),
  ('20:25','رسالة بخصوص مراجعة الحسابات.',['E08']),
  ('20:44','عادل دخل غرفة الخرائط حي.',['E07']),
  ('20:45','بداية نافذة الوفاة، نهايتها 20:55.',['E01']),
  ('20:48','ملف الاستغاثة اترفع للجدولة.',['E06']),
  ('20:54','الخروج الأخير وقفل غرفة الخرائط.',['E07']),
  ('21:00','إذاعة الصوت، مش مشاهدة عادل حي.',['E03']),
  ('21:06','المفتاح الاحتياطي رجع للمخزن.',['E02'])]
}

def timeline_entries(case,state):
    discovered=set(state['discovered'])
    return [{'time':display_times(time),'sort':time,'text':display_times(text),'evidence':ids}
            for time,text,ids in TIMELINE_FACTS.get(case['id'],[]) if set(ids)<=discovered]
