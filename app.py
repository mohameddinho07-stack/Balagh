import streamlit as st
from game_engine import (generate_case, new_investigation, evidence_cards,
                         available_questions, record_answer, finish_investigation, case_catalog, available_evidence, inspect_evidence, link_evidence, timeline_entries)

st.set_page_config(page_title="بلاغ", page_icon="🚨", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"] {direction:rtl;text-align:right;}
[data-testid="stSidebar"] {direction:rtl;}
.stButton button, .stSelectbox, .stMultiSelect, textarea {direction:rtl;}
[data-testid="stMarkdownContainer"] p, .stButton button p {direction:rtl;unicode-bidi:plaintext;text-align:right;}
h1, h2, h3, [data-testid="stCaptionContainer"] {text-align:right;direction:rtl;}
[data-testid="stMainBlockContainer"] {max-width:1100px;}

@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
html,body,[data-testid="stAppViewContainer"],[data-testid="stHeader"],.stApp{background:#101b19!important;color:#eee5cf!important;font-family:Cairo,Tahoma,sans-serif!important;color-scheme:dark;}
[data-testid="stMainBlockContainer"]{padding-top:4.4rem;}
h1,h2,h3,h4,[data-testid="stCaptionContainer"],label,[data-testid="stMetricValue"]{color:#e7d5ae!important;}
button,[data-baseweb="select"]>div,textarea,input,[data-testid="stExpander"]{background:#21372e!important;color:#eee5cf!important;border-color:#6c8067!important;font-family:Cairo,Tahoma,sans-serif!important;}
[data-testid="stAlert"],[data-testid="stForm"]{background:#1a2d26!important;color:#eee5cf!important;border-color:#6c8067!important;}
[data-testid="stMarkdownContainer"],summary{color:#eee5cf;}
</style>""", unsafe_allow_html=True)
from pathlib import Path
import streamlit.components.v1 as components
_entry_component = components.declare_component('balagh_entry', path=str(Path(__file__).parent/'entry_frontend'/'entry_frontend'))
phase = st.session_state.get('entry_phase', 'landing')
entry_event = _entry_component(stage=phase, scene_id=(st.session_state.get('case') or {}).get('scene','hotel'), key='balagh_entry_persistent', default=None)
if phase in ('landing','choose'):
    st.markdown('<style>[data-testid="stAppViewContainer"]{background:#101b19;color:#eee5cf;}header[data-testid="stHeader"]{background:#101b19;}[data-testid="stMainBlockContainer"]{padding-top:4.4rem;}[data-testid="stMainBlockContainer"] h1,[data-testid="stMainBlockContainer"] h3,[data-testid="stCaptionContainer"]{color:#e7d5ae;}</style>', unsafe_allow_html=True)
if phase == 'landing':
    if entry_event == 'start':
        st.session_state.entry_phase = 'choose'
        st.rerun()
    st.stop()
def archive_solo():
    current=st.session_state.get('case')
    if current and not st.session_state.get('room_token') and st.session_state.get('previous_mode','🔍 العب لوحدك')=='🔍 العب لوحدك':
        st.session_state.setdefault('case_saves',{})[current['id']] = {
            'case':current,'state':st.session_state.get('investigation'),
            'notes':st.session_state.get('detective_notes','')}

if phase == 'choose':
    with st.expander('عندك ملف حفظ؟ كمّل من مكانك'):
        upload=st.file_uploader('ملف حفظ بلاغ للفردي، مش مفتاح أوضة',type=['json'],max_upload_size=1)
        if st.button('افتح ملف الحفظ',disabled=upload is None):
            try:
                from dossier import import_dossier
                c,saved_state,saved_notes=import_dossier(upload.getvalue())
                st.session_state.case=c;st.session_state.investigation=saved_state
                st.session_state.detective_notes=saved_notes;st.session_state.entry_phase='game'
                for k in ['mode_choice','previous_mode','ai_suspect','focus_person','solo_snapshot','last_scene_nonce','link_feedback','reveal_solution']:
                    st.session_state.pop(k,None)
                st.rerun()
            except (ValueError,TypeError) as e:st.warning(str(e))
    st.title('اختار البلاغ')
    st.caption('٣ حكايات من خيالنا. كل واحدة مكان، وناس، وحقيقة مختلفة. اختار، وافتح عينك.')
    for item in case_catalog():
        with st.container(border=True):
            st.subheader('بلاغ '+item['id']+' • '+item['title'])
            st.write(item['location'])
            st.caption(item['tagline']+' | '+item['difficulty']+' | '+item['duration'])
            saved=st.session_state.get('case_saves',{}).get(item['id'])
            if saved and saved.get('state'):
                ps=saved['state'];st.caption(('اتقفلت القضية' if ps['finished'] else 'تحقيق محفوظ في الجلسة')+' · '+str(len(ps['discovered']))+' أدلة · '+str(len(ps['interviews']))+' ردود')
            saved=st.session_state.get('case_saves',{}).get(item['id'])
            if st.button(('كمّل التحقيق' if saved else 'افتح المحضر')+' · '+item['title'], key='open_case_'+item['id'], type='primary'):
                saved=st.session_state.get('case_saves',{}).get(item['id'])
                st.session_state.case = saved['case'] if saved else generate_case(item['id'])
                st.session_state.investigation = saved['state'] if saved else new_investigation()
                st.session_state.detective_notes = saved.get('notes','') if saved else ''
                st.session_state.entry_phase='game'
                for k in ['previous_mode','mode_choice','ai_suspect','focus_person','solo_snapshot','last_scene_nonce','link_feedback','reveal_solution']:
                    st.session_state.pop(k,None)
                st.rerun()
    st.caption('الأماكن الحقيقية إلهام للأجواء بس. المعسكر والمركب وكل الجرائم والشخصيات مؤلّفة. دي مش معلومات سفر أو تصريح زيارة.')
    st.stop()
if st.button('ارجع لاختيار القضية'):
    archive_solo()
    if st.session_state.get('room_token'):
        st.warning('اخرج من الأوضة على الجهاز ده الأول عشان ترجع لاختيار قضية من غير خلط.')
        st.stop()
    st.session_state.entry_phase = 'choose'
    st.rerun()
selected_case_id=st.session_state.get('case',{}).get('id','001') if st.session_state.get('case') else '001'
with st.expander("طريقة اللعب: فردي، مع صحابك، أو سباق"):
    if selected_case_id!='001':
        st.caption('القضية دي فردي دلوقتي. التعاوني والسباق شغالين في قضية الفندق بس، لحد ما قواعد السيرفر تتختبر للقضايا الجديدة.')
    mode = st.radio("تحب تلعب إزاي؟", ["🔍 العب لوحدك", "🎮 العب مع صحابك", "🏁 سباق محققين"], horizontal=True, key='mode_choice', disabled=selected_case_id!='001' or bool(st.session_state.get('room_token')))
room_mode = mode != "🔍 العب لوحدك"
race_mode = mode == "🏁 سباق محققين"
room = None
previous_mode = st.session_state.get('previous_mode')
if previous_mode is not None and previous_mode != mode:
    if previous_mode == "🔍 العب لوحدك":
        archive_solo()
        st.session_state.solo_snapshot = (st.session_state.get('case'), st.session_state.get('investigation'),st.session_state.get('detective_notes',''))
    else:
        snapshot=st.session_state.get('solo_snapshot', (None,None,''))
        old_case, old_state=snapshot[:2]
        st.session_state.detective_notes=snapshot[2] if len(snapshot)>2 else ''
        st.session_state.case = old_case
        st.session_state.investigation = old_state
st.session_state.previous_mode = mode
if st.session_state.get('room_token'):
    st.caption('إنت جوه أوضة. اخرج منها على الجهاز ده الأول لو عايز تغيّر طريقة اللعب أو القضية.')
if room_mode:
    from room_client import rpc, RoomError
    st.subheader("سباق محققين" if race_mode else "أوضة تحقيق ليك ولصاحبك")
    if race_mode:
        st.caption("كل واحد يحقق لوحده. أول حل صح بالمتهم والأدلة يكسب. اتهام نهائي واحد لكل لاعب، الغلط يخرجك، ولو الاتنين غلط محدش يكسب. السباق يبدأ لما الاتنين يدخلوا.")
        st.caption("دي نفس القضية الموجودة في الفردي والتعاوني. اللي عارف حلها من قبل عنده أفضلية، مش مسابقة عمياء أو ضد الغش.")
    else:
        st.caption("تعاون بين اتنين، مش أدوار سرية. الأدلة والاستجوابات مشتركة، والنوتة خاصة بكل لاعب. الاتهام لازم موافقة الاتنين.")
    try:
        db_url, db_key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    except Exception:
        st.info("ربط الأوض مش جاهز دلوقتي. اللعب الفردي شغّال.")
        st.stop()
    def room_call(op, payload=None, code='', token=None):
        return rpc(db_url, db_key, op, token=st.session_state.get('room_token','') if token is None else token,
                   code=code, payload=payload)
    if not st.session_state.get('room_token'):
        with st.form('room_entry'):
            player_name = st.text_input('اسمك في الأوضة', max_chars=30)
            room_code = st.text_input('كود الأوضة لو هتدخل عند صاحبك', max_chars=10)
            create = st.form_submit_button('اعمل أوضة')
            join = st.form_submit_button('ادخل الأوضة')
        with st.form('room_resume'):
            recovery = st.text_input('مفتاح رجوعك الشخصي', type='password', max_chars=64)
            resume = st.form_submit_button('ارجع لأوضتك')
        try:
            if create or join:
                room = room_call('create' if create else 'join', {'name':player_name,'mode':'race' if race_mode else 'coop'}, code=room_code)
                st.session_state.room_token = room['token']
                st.session_state.room_fresh = True
                st.rerun()
            if resume:
                room = room_call('read', token=recovery.strip())
                st.session_state.room_token = recovery.strip()
                st.rerun()
        except RoomError as e:
            st.warning(str(e))
        st.stop()
    try:
        room = room_call('read')
    except RoomError as e:
        st.warning(str(e))
        if st.button('ارجع لشاشة الدخول'):
            st.session_state.pop('room_token',None); st.rerun()
        st.stop()
    race_mode = room.get('mode','coop') == 'race'
    state = room['state']
    st.session_state.investigation = state
    st.info('كود الأوضة: ' + room['code'] + ' | الموجودين: ' + '، '.join(p['name'] for p in room['players']))
    st.caption('الكود دعوة لصاحبك. اللي معاه الكود يقدر يدخل لو فيه مكان. الاسم مش إثبات هوية.')
    with st.expander('احفظ مفتاح رجوعك قبل ما تقفل'):
        st.warning('ده مفتاحك إنت بس، ما تبعتوش لصاحبك ولا تكتبه في الشات. اللي معاه يقدر يدخل باسمك ويشوف نوتتك. ارجع بنفس المفتاح لو الجلسة قفلت. مفيش استرجاع بالاسم بس.')
        st.download_button('نزّل مفتاح الرجوع', st.session_state.room_token, file_name='balagh-recovery.txt', mime='text/plain')
    if st.button('حدّث الأوضة'):
        st.rerun()
    @st.fragment(run_every=5)
    def room_watch():
        try:
            latest = room_call('read')
            if latest['revision'] != room['revision'] or len(latest['players']) != len(room['players']):
                st.rerun()
        except RoomError:
            st.caption('المزامنة متأخرة، جرّب تحديث الأوضة.')
    room_watch()
    st.caption('التحديث كل 5 ثواني طول ما الصفحة مفتوحة. لو الخدمة المجانية وقفت، هتظهر رسالة بدل نجاح وهمي.')
    if st.button('اخرج من الأوضة على الجهاز ده'):
        for k in [k for k in st.session_state if k.startswith('room_notes_')] + ['room_token','ai_suspect']:
            st.session_state.pop(k,None)
        st.rerun()
    if race_mode:
        if len(room['players']) < 2:
            st.info('مستني صاحبك يدخل. التحقيق هيفتح للاتنين بعد دخوله.')
            st.stop()
        if room['status'] == 'finished':
            winner = next((p['name'] for p in room['players'] if p['id']==room['winner']), None)
            if room['winner'] == room['me']:
                st.success('كسبت السباق، حلك والأدلة صح وقرارك اتسجل الأول.')
            elif winner:
                st.info(winner + ' سبقك ووصل للحل الصح بالأدلة. السباق خلص.')
            else:
                st.warning('السباق خلص من غير فايز، الاتنين قدموا اتهام غلط.')
            if st.button('سيب السباق وابدأ واحد جديد'):
                st.session_state.clear(); st.rerun()
            st.stop()
        if state['finished']:
            st.warning('اتهامك النهائي ماطلعش حل صحيح مكتمل بالأدلة. خرجت من السباق، وصاحبك لسه بيكمّل. النتيجة هتظهر هنا لما يخلص.')
            st.stop()
    case = generate_case()
    st.session_state.case = case
else:
    if "case" not in st.session_state:
        st.session_state.case = None
    if st.session_state.case is None:
        st.subheader("بلاغ 001 • الغرفة المغلقة")
        st.write("بص يا حضرة الظابط، قدامك بلاغ قتل وأربع أشخاص لازم تسمع منهم. امسك الملف واحدة واحدة، وراجع كل كلمة على الأدلة. مش عايزين اسم وخلاص، عايزين تعرف مين عملها وتقول دليلك إيه.")
        if st.button("🚔 يلا نحقق", type="primary"):
            st.session_state.case = generate_case()
            st.session_state.investigation = new_investigation()
            st.rerun()
        st.stop()

def persist_room(op, payload=None):
    if room_mode:
        try:
            args = dict(payload or {}, revision=room['revision'])
            room_call(op, args)
        except RoomError as e:
            st.warning(str(e)); st.stop()


case = st.session_state.case
state = st.session_state.investigation
public = case["public"]
st.subheader(f"بلاغ {case['id']} • {public['title']}")
st.caption(f"المكان: {public['location']} | اللي اتقتل: {public['victim']}")
with st.expander("اقرا البلاغ وحكاية اللي حصل"):
    st.info(public["story"])
# Each case owns its scene and public evidence. No truth or credentials cross to the browser.
crime_scene = components.declare_component('balagh_crime', path=str(Path(__file__).parent/'crime_frontend'/'crime_frontend'))
scene_scope = '|'.join([case['id'], mode, str(room.get('me','')) if room_mode else state.setdefault('attempt_id',__import__('uuid').uuid4().hex)])
scene_event = crime_scene(cards=available_evidence(case,state), locked_cards=[{'id':e['id'],'title':e['title'],'requires':e.get('requires',[])} for e in evidence_cards(case) if e not in available_evidence(case,state)], total=len(evidence_cards(case)), discovered=state['discovered'],
    timeline=timeline_entries(case,state), finished=state['finished'], link_feedback=st.session_state.get('link_feedback',''), allow_links=not room_mode, scope=scene_scope, location=public['location'],
    scene_id=case.get('scene','hotel'), reasoning=[{'id':x['id'],'title':x['title'],'text':x['text']} for x in case.get('reasoning',[]) if x['id'] in state.get('deductions',[])], deductions=state.get('deductions',[]), case_title=public['title'], victim=public['victim'], story=public['story'], people=[{'id':c['id'],'name':c['name'],'job':c['job'],'info':c['public_info'],
        'questions':[{'id':q['id'],'question':q['question']} for q in available_questions(c,state['discovered'])],
        'locked':len(c['interviews'])-len(available_questions(c,state['discovered'])),
        'answers':[a for a in state['interviews'] if a['suspect']==c['name']]} for c in case['characters']], key='crime_scene_'+scene_scope, default=None)
if isinstance(scene_event, dict) and scene_event.get('nonce') != st.session_state.get('last_scene_nonce'):
    st.session_state.last_scene_nonce = scene_event.get('nonce')
    eid = scene_event.get('evidence')
    person = scene_event.get('person')
    if scene_event.get('scope') == scene_scope and person in {c['id'] for c in case['characters']}:
        st.session_state.focus_person = person
    selected_links=scene_event.get('link')
    if scene_event.get('scope')==scene_scope and isinstance(selected_links,list) and not state['finished'] and not room_mode:
        try:
            found=link_evidence(case,state,selected_links)
            st.session_state.link_feedback=found['text'] if found else 'الربط ده لسه ما يثبتش نتيجة لوحده. جرّب تقارن وقت أو رواية بأكتر من مصدر.'
            st.rerun()
        except ValueError as e:st.warning(str(e))
    topic = scene_event.get('topic')
    if scene_event.get('scope') == scene_scope and topic and not state['finished']:
        suspect = next((c for c in case['characters'] if c['id']==person),None)
        if suspect and topic in {q['id'] for q in available_questions(suspect,state['discovered'])}:
            persist_room('interview', {'suspect':person,'topic':topic})
            if not room_mode:
                record_answer(case,state,person,topic)
            st.rerun()
    if (scene_event.get('scope') == scene_scope and not state['finished']
            and eid in {e['id'] for e in available_evidence(case,state)} and eid not in state['discovered']):
        # Room validation and revision checks run before any local change.
        persist_room('inspect', {'evidence':eid})
        if not room_mode:
            inspect_evidence(case,state,eid)
        st.rerun()

if state["finished"]:
    result = state["result"]
    st.subheader('محضر قفل القضية')
    st.caption('مش المهم الاسم بس، المهم إزاي وصلت له.')
    st.write('راجعت '+str(len(state['discovered']))+' أدلة، وسجلت '+str(len(state['interviews']))+' ردود، وخدت '+str(state['hints_used'])+' تلميحات.')
    if result["success"]:
        st.success("تمام يا حضرة الظابط، وصلت للي عملها والأدلة ساندت كلامك. المحاولة دي خلصت.")
    elif result["killer_correct"]:
        st.warning("مسكت الفاعل، بس الأدلة اللي اخترتها لسه مش مكمّلة الحكاية. المحاولة دي خلصت؛ شوف الحل لو حابب أو جرّب من الأول.")
    else:
        st.error("لأ، مش هو ده اللي عملها. المحاولة دي خلصت، بس مش هنحرق عليك اسم الفاعل. لو عايز تعرفه، اختار تشوف الحل.")
    st.write(f"قرارك: {result['suspect']} | الأدلة: {', '.join(result['submitted_evidence'])}")
    if st.checkbox("ورّيني الحل وفهّمني الأدلة", key="reveal_solution"):
        st.subheader(f"الحل: {case['truth']['killer']}")
        st.write(case["truth"]["explanation"])
        for e in evidence_cards(case):
            if e['id'] in case['truth']['required_evidence']:
                st.markdown('**'+e['id']+' · '+e['title']+'**')
                st.write(e['text'])
    if st.button("نجرّب من الأول" if not room_mode else "سيب الأوضة وابدأ واحدة جديدة", type="primary"):
        if not room_mode:
            st.session_state.investigation=new_investigation()
            st.session_state.detective_notes=''
            st.session_state.setdefault('case_saves',{}).pop(case['id'],None)
            st.session_state.pop('reveal_solution',None)
        else:
            st.session_state.clear()
        st.rerun()

with st.expander('إزاي تمسك البلاغ؟'):
    st.write('١. افتح المكان واقرا الأدلة المتاحة. دوس «فحصت الدليل ده» عشان المحضر يسجّلها.')
    st.write('٢. بعض الملفات مستنية أدلة قبلها. المطلوب مكتوب على الملف المقفول.')
    st.write('٣. اسمع كل واحد، وارجع واجهه لما دليل جديد يفتح سؤال. حط دليلين أو أكتر على ترابيزة الربط.')
    st.write('٤. نوتتك ليك. التلميحات تساعد من غير ما تختار مكانك. قرار الاتهام النهائي واحد في المحاولة، فراجع السبب والدليل.')
a, b, c = st.columns(3)
a.metric("أدلة بصّيت عليها", f"{len(state['discovered'])}/{len(evidence_cards(case))}")
b.metric("ردود اتسجّلت", len(state["interviews"]))
c.metric("تلميحات خُدتها", state["hints_used"])

with st.expander("🕒 إيه حصل وإمتى؟"):
    for item in public["timeline"]:
        time_label, event = item.split(" • ", 1)
        with st.container(border=True):
            st.markdown(f"**{time_label}**")
            st.write(event)

st.subheader("💬 اسأل بطريقتك، تجربة AI")
st.caption("AI من Groq بيفهم سؤالك وسياق آخر كلامكم. الرد نفسه من كلام القضية المكتوب، عشان الحقيقة والأدلة ما يتغيّروش. لسه مش حوار مولّد بحرية.")
st.warning("سؤالك وآخر 4 أسئلة بيتبعتوا لـ Groq. ما تكتبش بيانات شخصية أو أسرار. لو الحد المجاني خلص، التجربة بتقف من غير دفع، والأسئلة الجاهزة تفضل شغّالة.")
try:
    groq_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    groq_key = ""
if state.get("imported_dossier"):
    st.info("ملف الحفظ بيكمّل بالأسئلة الجاهزة بس. AI متاح في محاولة جديدة، عشان ما نعيدش حدوده مع كل تحميل.")
elif not groq_key:
    st.info("ربط AI مش جاهز على السيرفر دلوقتي. تقدر تكمّل بالأسئلة الجاهزة.")
else:
    from ai_interrogation import ask_suspect, AIUnavailable
    st.caption(f"أسئلة AI في المحاولة: {len(state.get('ai_interviews', []))}/20")
    selected_suspect = st.selectbox("هتسأل مين؟", [s["id"] for s in case["characters"]],
                                    index=None, placeholder="اختار الشخصية", key="ai_suspect",
                                    format_func=lambda sid: next(s["name"] for s in case["characters"] if s["id"] == sid))
    with st.form("suspect_ai", clear_on_submit=True):
        free_question = st.text_input("سؤالك إيه؟", max_chars=350,
                                      placeholder="كنت فين وقت اللي حصل؟")
        ai_sent = st.form_submit_button("اسأل", disabled=state["finished"] or selected_suspect is None)
    if ai_sent:
        try:
            with st.spinner("السؤال بيتراجع..."):
                turn = ask_suspect(case, state, selected_suspect, free_question, groq_key)
            persist_room('ai', {'suspect':selected_suspect,'question':free_question,'topic':turn['topic']})
            st.rerun()
        except AIUnavailable as error:
            st.warning(str(error))
    for turn in state.get("ai_interviews", []):
        with st.container(border=True):
            st.text("إنت: " + turn["question"])
            st.write(turn.get("suspect", "نادين مراد") + ": " + turn["answer"])

st.subheader("📓 نوتة التحقيق")
if not room_mode:
    with st.expander('احفظ التحقيق وكمّل بعدين'):
        from dossier import export_dossier
        st.caption('حفظ الفردي داخل الجلسة بس. نزّل ملفك قبل ما تقفل. الملف فيه نوتتك وتقدّمك، ما تشاركهوش لو عايز تحافظ على أسرارك. ده مش إثبات نتيجة ولا ينفع للسباق. سجل AI الحر مش بينتقل. بعد تحميل الملف، التحقيق بيكمّل بالأسئلة الجاهزة بس، وتجربة AI مش بتتفتح من جديد بالتحميل.')
        st.download_button('نزّل ملف حفظ التحقيق',export_dossier(case,state,st.session_state.get('detective_notes','')),file_name='balagh-'+case['id']+'.json',mime='application/json')
if room_mode:
    notes_key = 'room_notes_' + str(room['me'])
    if notes_key not in st.session_state:
        st.session_state[notes_key] = room['notes']
    st.text_area('نوتتك الخاصة، صاحبك مش بيشوفها', key=notes_key, height=150, max_chars=6000)
    if st.button('احفظ نوتتي'):
        try:
            room_call('notes', {'notes':st.session_state[notes_key]})
            st.success('نوتتك اتحفظت ليك لوحدك.')
        except RoomError as e:
            st.warning(str(e))
else:
    st.text_area("اكتب اللي واخد بالك منه هنا، هيفضل معاك طول ما جلسة اللعب شغّالة بس", key="detective_notes", height=150, max_chars=6000)
if not state["finished"]:
    if st.button("💡 ادّيني طرف خيط من غير حرق"):
        state["hints_used"] += 1
        persist_room('hint')
        if room_mode: st.rerun()
    if state["hints_used"]:
        st.info(case.get('hints',['خلي بالك، وقت دخول اللي عملها مش لازم يبقى هو وقت الموت. راجع الزيارة والكوباية والسبب. البصمة لوحدها أو الخناقة لوحدها مش كفاية.'])[min(state['hints_used']-1,len(case.get('hints',[0]))-1)])
    st.subheader("⚖️ مين المتهم وإيه دليلك؟")
    st.caption("اتهام نهائي واحد، لو المتهم أو الأدلة غلط هتخرج من السباق. الفوز محتاج ربط الزيارة بالكوباية والدافع." if race_mode else "اقتراحك لازم صاحبك يوافق عليه عشان التحقيق يقفل." if room_mode else "قبل ما تثبّت الاتهام، راجع نفسك: مين عملها؟ وإيه اللي يثبت كلامك؟ اختار الأدلة اللي بتربط زيارته باللي حصل وسببه. الشك لوحده مش كفاية. ليك قرار أخير واحد في المحاولة.")
    cards = {e["id"]: e for e in evidence_cards(case)}
    with st.form("accusation"):
        selected = st.selectbox("مين اللي عملها؟", [s["name"] for s in case["characters"]], index=None, placeholder="اختار حد")
        evidence_ids = st.multiselect("إيه الأدلة اللي بصّيت عليها وبتسند كلامك؟", state["discovered"], format_func=lambda x: f"{x} • {cards[x]['title']}")
        confirmed = st.checkbox("أيوه، ده قراري الأخير وعارف إن المحاولة هتقفل بعده")
        submitted = st.form_submit_button("ثبّت الاتهام", type="primary")
    if submitted:
        if not confirmed or selected is None or not evidence_ids:
            st.warning("اختار حد ودليل واحد على الأقل، وعلّم إن ده قرارك الأخير.")
        else:
            if room_mode:
                try:
                    proposal = {'suspect':selected,'evidence':sorted(evidence_ids)}
                    room_call('accuse' if race_mode else 'propose', proposal)
                    st.rerun()
                except RoomError as e:
                    st.warning(str(e))
            else:
                finish_investigation(case, state, selected, evidence_ids)
                st.rerun()

if room_mode and not race_mode and room['proposal'] and not state['finished']:
    proposal = room['proposal']
    st.subheader('راجع اقتراح الاتهام')
    st.write('المتهم: ' + proposal['suspect'] + ' | الأدلة: ' + '، '.join(proposal['evidence']))
    if room['me'] in room['approvals']:
        st.info('موافقتك متسجلة، مستني صاحبك. أي دليل أو استجواب جديد بيلغي الاقتراح عشان تراجعوه تاني.')
    elif st.button('موافق على نفس الاتهام والأدلة، نقفل التحقيق'):
        try:
            room_call('approve', {'proposal':proposal})
            st.rerun()
        except RoomError as e:
            st.warning(str(e))

if not room_mode:
    archive_solo()

st.caption("الفردي بيتحفظ طول الجلسة بس. الأوضة بتحفظ التحقيق والنوتة الخاصة على السيرفر، والرجوع بمفتاحك الشخصي. المجاني ليه حدود وممكن يتوقف مع قلة الاستخدام.")
