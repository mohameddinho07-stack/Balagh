"""Local solo dossier import/export. Only canonical IDs are trusted, never uploaded dialogue/results."""
import json
from game_engine import generate_case,new_investigation,evidence_cards,available_evidence,inspect_evidence,record_answer,finish_investigation

MAX_BYTES=100000

def export_dossier(case,state,notes=''):
    board=state.get('board') or {}
    return json.dumps({'format':'balagh-solo-v1','case_id':case['id'],
       'discovered':state['discovered'],'questions':[a['question_id'] for a in state['interviews']],
       'hints_used':state['hints_used'],'deductions':state.get('deductions',[]),
       'board':{'pins':list(board.get('pins',[])),'theories':[list(t.get('cards',[])) for t in board.get('theories',[])],
                'placed':dict(board.get('placed',{}))},
       'notes':notes[:6000],'finished':state['finished'],
       'verdict':({'suspect':state['result']['suspect'],'evidence':state['result']['submitted_evidence']} if state['finished'] else None)},ensure_ascii=False,indent=2)

def import_dossier(raw):
    if not isinstance(raw,(str,bytes,bytearray)):raise ValueError('ملف الحفظ مش سليم.')
    if len(raw)>MAX_BYTES:raise ValueError('ملف الحفظ أكبر من المسموح.')
    try:d=json.loads(raw)
    except (ValueError,TypeError,RecursionError):raise ValueError('ملف الحفظ مش JSON سليم.') from None
    if not isinstance(d,dict) or d.get('format')!='balagh-solo-v1':raise ValueError('ده مش ملف حفظ بلاغ مدعوم.')
    try:case=generate_case(d.get('case_id'))
    except (KeyError,TypeError):raise ValueError('القضية دي مش موجودة في النسخة الحالية.') from None
    state=new_investigation()
    state['imported_dossier']=True
    for key in ['discovered','questions','deductions']:
        if not isinstance(d.get(key,[]),list) or len(d.get(key,[]))>60 or not all(isinstance(x,str) for x in d.get(key,[])):
            raise ValueError('ملف الحفظ فيه بيانات مش سليمة.')
    pending=set(d.get('discovered',[]))
    while pending:
        unlocked={e['id'] for e in available_evidence(case,state)}&pending
        if not unlocked:raise ValueError('الأدلة في الملف مش ماشية مع قواعد القضية.')
        for eid in unlocked:inspect_evidence(case,state,eid)
        pending-=unlocked
    qs={q['id']:(p['id'],q) for p in case['characters'] for q in p['interviews']}
    for qid in d.get('questions',[]):
        if qid not in qs:raise ValueError('فيه سؤال مش موجود في القضية.')
        pid,q=qs[qid];record_answer(case,state,pid,qid)
    hints=d.get('hints_used',0)
    if not isinstance(hints,int) or isinstance(hints,bool) or not 0<=hints<=100:raise ValueError('عدد التلميحات مش سليم.')
    state['hints_used']=hints
    links={x['id']:x for x in case.get('reasoning',[])}
    for did in d.get('deductions',[]):
        if did not in links or not set(links[did]['evidence'])<=set(state['discovered']):raise ValueError('فيه ربط أدلة مش سليم.')
    state['deductions']=list(dict.fromkeys(d.get('deductions',[])))
    board=d.get('board')
    if board is not None:
        from board import board_action
        if not isinstance(board,dict):raise ValueError('حيطة التحقيق في الملف مش سليمة.')
        pins=board.get('pins',[]);theories=board.get('theories',[]);placed=board.get('placed',{})
        if not isinstance(pins,list) or len(pins)>40 or not all(isinstance(x,str) for x in pins):raise ValueError('حيطة التحقيق في الملف مش سليمة.')
        if not isinstance(theories,list) or len(theories)>30 or not all(isinstance(t,list) and 2<=len(t)<=3 and all(isinstance(x,str) for x in t) for t in theories):raise ValueError('حيطة التحقيق في الملف مش سليمة.')
        if not isinstance(placed,dict) or len(placed)>40 or not all(isinstance(k,str) and isinstance(v,str) for k,v in placed.items()):raise ValueError('حيطة التحقيق في الملف مش سليمة.')
        for card in dict.fromkeys(pins):board_action(case,state,{'do':'pin','card':card})
        for cards in theories:
            try:board_action(case,state,{'do':'link','cards':cards})
            except ValueError:pass  # a pair the current rules reject just does not come back
        for card,slot in placed.items():board_action(case,state,{'do':'place','card':card,'slot':slot})
    notes=d.get('notes','')
    if not isinstance(notes,str) or len(notes)>6000:raise ValueError('النوتة أكبر من المسموح.')
    if not isinstance(d.get('finished',False),bool):raise ValueError('حالة التحقيق مش سليمة.')
    if d.get('finished'):
        v=d.get('verdict')
        if not isinstance(v,dict) or not isinstance(v.get('evidence'),list) or len(v['evidence'])>60 or not isinstance(v.get('suspect'),str) or not all(isinstance(x,str) for x in v['evidence']):raise ValueError('قرار التحقيق مش سليم.')
        finish_investigation(case,state,v.get('suspect'),v['evidence'])
    return case,state,notes
