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
    from brand import wordmark_html
    st.markdown(wordmark_html(), unsafe_allow_html=True)
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
    st.caption('الأماكن الحقيقية إلهام للأجواء بس. المخيم والمركب وكل الجرائم والشخصيات مؤلّفة. دي مش معلومات سفر أو تصريح زيارة.')
    st.stop()
if st.button('ارجع لاختيار القضية'):
    archive_solo()
    if st.session_state.get('room_token'):
        st.warning('اخرج من الأوضة على الجهاز ده الأول عشان ترجع لاختيار قضية من غير خلط.')
        st.stop()
    st.session_state.entry_phase = 'choose'
    st.rerun()
MODES = ["🔍 العب لوحدك", "🤝 تعاون", "🏁 سباق فردي", "⚔️ سباق فرق"]
MODE_KEYS = {MODES[1]: 'coop', MODES[2]: 'race', MODES[3]: 'team'}
def team_label(unit):
    return 'الفريق ' + str(unit)[1:].translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')) if str(unit).startswith('t') else ''
with st.expander("طريقة اللعب: فردي، تعاون، سباق، أو فرق"):
    st.caption('كل القضايا بتشتغل بنفس الأوضاع، حتى اللي هتتضاف بعدين. تعاون: الكل في تحقيق واحد. سباق فردي: كل واحد لوحده. سباق فرق: فريقين لـ ٤ فرق، كل فريق من ١ لـ ٥ لاعبين (٢ ضد ٢، ٤ ضد ٤، وغيره)، التقدم مشترك جوه الفريق ومنفصل بين الفرق.')
    mode = st.radio("تحب تلعب إزاي؟", MODES, horizontal=True, key='mode_choice', disabled=bool(st.session_state.get('room_token')))
room_mode = mode != MODES[0]
race_mode = mode == MODES[2]
team_mode = mode == MODES[3]
competitive = race_mode or team_mode
room = None
previous_mode = st.session_state.get('previous_mode')
if previous_mode is not None and previous_mode != mode:
    if previous_mode == MODES[0]:
        archive_solo()
        st.session_state.solo_snapshot = (st.session_state.get('case'), st.session_state.get('investigation'),st.session_state.get('detective_notes',''))
    elif mode == MODES[0]:
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
    st.subheader({'coop':'أوضة تعاون','race':'سباق محققين','team':'سباق فرق'}[MODE_KEYS[mode]])
    try:
        db_url, db_key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    except Exception:
        st.info("ربط الأوض مش جاهز دلوقتي. اللعب الفردي شغّال.")
        st.stop()
    def room_call(op, payload=None, code='', token=None):
        return rpc(db_url, db_key, op, token=st.session_state.get('room_token','') if token is None else token,
                   code=code, payload=payload)
    if not st.session_state.get('room_token'):
        if race_mode:
            st.caption("كل واحد يحقق لوحده على نفس القضية. اتهام نهائي واحد لكل لاعب، الغلط يخرجك. أول حل صح بالمتهم والأدلة يكسب. صاحب الأوضة يبدأ السباق لما الكل يدخل.")
        elif team_mode:
            st.caption("فرق متنافسة على نفس القضية. جوه الفريق الأدلة والأقوال مشتركة والنوتة خاصة، واتهام الفريق لازم كل أعضائه يوافقوا عليه. أول فريق يوصل للحل الصح بالأدلة يكسب، والفريق الغلط يخرج.")
        else:
            st.caption("الكل في تحقيق واحد، من ٢ لـ ١٠ لاعبين. الأدلة والاستجوابات مشتركة، والنوتة خاصة بكل لاعب. الاتهام لازم يوافق عليه كل اللي في الأوضة.")
        st.caption("دي نفس القضية الموجودة في الفردي. اللي عارف حلها من قبل عنده أفضلية، مش مسابقة عمياء أو ضد الغش.")
        picked_case_id = (st.session_state.get('case') or {}).get('id','001')
        with st.form('room_entry'):
            player_name = st.text_input('اسمك في الأوضة', max_chars=30)
            st.caption('لو بتعمل أوضة، القضية هتبقى القضية اللي فاتحها دلوقتي: ' + picked_case_id + '. لو بتدخل بكود، القضية هي قضية الأوضة.')
            if team_mode:
                team_count = st.number_input('عدد الفرق (للي بيعمل الأوضة)', min_value=2, max_value=4, value=2, step=1)
                team_size = st.number_input('عدد لاعبين كل فريق (للي بيعمل الأوضة)', min_value=1, max_value=5, value=2, step=1)
                my_team = st.number_input('رقم فريقك (٠ = توزيع تلقائي)', min_value=0, max_value=4, value=0, step=1)
            else:
                max_players = st.number_input('أقصى عدد لاعبين (للي بيعمل الأوضة)', min_value=2, max_value=10, value=2 if not race_mode else 4, step=1)
            room_code = st.text_input('كود الأوضة لو هتدخل عند صحابك', max_chars=10)
            create = st.form_submit_button('اعمل أوضة')
            join = st.form_submit_button('ادخل الأوضة')
        with st.form('room_resume'):
            recovery = st.text_input('مفتاح رجوعك الشخصي', type='password', max_chars=64)
            resume = st.form_submit_button('ارجع لأوضتك')
        try:
            if create or join:
                if team_mode:
                    args = {'name':player_name,'mode':'team','case':picked_case_id,'team_count':int(team_count),'team_size':int(team_size),'team':int(my_team)}
                else:
                    args = {'name':player_name,'mode':MODE_KEYS[mode],'case':picked_case_id,'max_players':int(max_players)}
                room = room_call('create' if create else 'join', args, code=room_code)
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
    team_mode = room.get('mode','coop') == 'team'
    competitive = race_mode or team_mode
    state = room['state']
    st.session_state.investigation = state
    case = generate_case(room['case_id'])
    st.session_state.case = case
    names = {p['id']:p['name'] for p in room['players']}
    st.info('كود الأوضة: ' + room['code'] + ' | القضية: ' + case['public']['title'])
    if team_mode:
        for i in range(1, room['team_count']+1):
            mine = ' (فريقك)' if room['my_unit']=='t'+str(i) else ''
            st.write('**' + team_label('t'+str(i)) + mine + ':** ' + ('، '.join(p['name'] for p in room['players'] if p['unit']=='t'+str(i)) or 'فاضي') + ' ('+str(sum(1 for p in room['players'] if p['unit']=='t'+str(i)))+'/'+str(room['team_size'])+')')
    else:
        st.write('**الموجودين (' + str(len(room['players'])) + '/' + str(room['max_players']) + '):** ' + '، '.join(p['name'] for p in room['players']))
    st.caption('الكود دعوة لصحابك. اللي معاه الكود يقدر يدخل لو فيه مكان. الاسم مش إثبات هوية.')
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
    if competitive:
        if not room['started']:
            if room['me'] == room['host']:
                st.info('إنت صاحب الأوضة. ابدأ لما كل صحابك يدخلوا. بعد البداية محدش جديد بيدخل.')
                if st.button('ابدأ السباق', type='primary'):
                    try:
                        room_call('start'); st.rerun()
                    except RoomError as e:
                        st.warning(str(e))
            else:
                st.info('مستنيين صاحب الأوضة يبدأ. التحقيق هيفتح للكل مع بعض.')
            st.stop()
        if room['status'] == 'finished':
            wu = room['winner_unit']
            if wu and wu == room['my_unit']:
                st.success(('فريقكم كسب السباق' if team_mode else 'كسبت السباق') + '، الحل والأدلة صح وقرار الفوز اتسجل الأول.')
            elif wu:
                winners = '، '.join(p['name'] for p in room['players'] if p['unit']==wu)
                st.info((team_label(wu) + ' (' + winners + ')' if team_mode else winners) + ' سبقكم ووصل للحل الصح بالأدلة. السباق خلص.')
            else:
                st.warning('السباق خلص من غير فايز، كل اتهام كان ناقص أو غلط.')
            if st.button('سيب السباق وابدأ واحد جديد'):
                st.session_state.clear(); st.rerun()
            st.stop()
        if state['finished']:
            st.warning(('اتهام فريقكم' if team_mode else 'اتهامك') + ' النهائي ماطلعش حل صحيح مكتمل بالأدلة. خرجتوا من السباق والباقيين لسه بيكمّلوا. النتيجة هتظهر هنا لما يخلصوا.' if team_mode else 'اتهامك النهائي ماطلعش حل صحيح مكتمل بالأدلة. خرجت من السباق والباقيين لسه بيكمّلوا. النتيجة هتظهر هنا لما يخلصوا.')
            done = sum(1 for v in room['unit_done'].values() if v)
            st.caption('خلصوا اتهامهم: ' + str(done) + ' من ' + str(room.get('team_count') if team_mode else len(room['players'])))
            st.stop()
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
            args = dict(payload or {}, revision=room['urev'])
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
import importlib, pilot; importlib.reload(pilot)  # picks up data edits without a manual reboot
from pilot import confront_only, intro_beats, mood as case_mood, confront_people, heard_statements, resolve_confront
_mood = case_mood(case['id'])
if _mood:
    st.markdown('<div style="border-right:4px solid '+_mood['color']+';padding:.3rem .9rem;margin:.2rem 0 .6rem;opacity:.92">'+_mood['line']+'</div>', unsafe_allow_html=True)
_beats = intro_beats(case['id'])
_ikey = 'intro:'+case['id']+':'+str(room.get('code','') if room_mode else 'solo')
if _beats and not state['discovered'] and not state['interviews'] and not state['finished'] and not st.session_state.get(_ikey+':done'):
    _step = min(st.session_state.get(_ikey, 0), len(_beats)-1)
    for _who, _line in _beats[:_step+1]:
        st.markdown('**'+_who+':** '+_line)
    _c1, _c2 = st.columns(2)
    if _c1.button('ابدأ التحقيق' if _step == len(_beats)-1 else 'كمّل', key=_ikey+':next', type='primary'):
        if _step == len(_beats)-1:
            st.session_state[_ikey+':done'] = True
        else:
            st.session_state[_ikey] = _step+1
        st.rerun()
    if _c2.button('تخطّى', key=_ikey+':skip'):
        st.session_state[_ikey+':done'] = True
        st.rerun()
    st.stop()
# Each case owns its scene and public evidence. No truth or credentials cross to the browser.
crime_scene = components.declare_component('balagh_crime', path=str(Path(__file__).parent/'crime_frontend'/'crime_frontend'))
scene_scope = '|'.join([case['id'], mode, str(room.get('me','')) if room_mode else state.setdefault('attempt_id',__import__('uuid').uuid4().hex)])
scene_event = crime_scene(cards=available_evidence(case,state), locked_cards=[{'id':e['id'],'title':e['title'],'requires':e.get('requires',[])} for e in evidence_cards(case) if e not in available_evidence(case,state)], total=len(evidence_cards(case)), discovered=state['discovered'],
    timeline=timeline_entries(case,state), finished=state['finished'], link_feedback=st.session_state.get('link_feedback',''), allow_links=not room_mode, scope=scene_scope, location=public['location'],
    scene_id=case.get('scene','hotel'), reasoning=[{'id':x['id'],'title':x['title'],'text':x['text']} for x in case.get('reasoning',[]) if x['id'] in state.get('deductions',[])], deductions=state.get('deductions',[]), case_title=public['title'], victim=public['victim'], story=public['story'], people=[{'id':c['id'],'name':c['name'],'job':c['job'],'info':c['public_info'],
        'questions':[{'id':q['id'],'question':q['question']} for q in available_questions(c,state['discovered']) if q['id'] not in confront_only(case['id'])],
        'locked':len([q for q in c['interviews'] if q['id'] not in confront_only(case['id'])])-len([q for q in available_questions(c,state['discovered']) if q['id'] not in confront_only(case['id'])]),
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

_cps = confront_people(case, state)
if _cps and not state['finished']:
    with st.expander('🎯 واجهه حد بدليل'):
        st.caption('اختار حد، وكلام قاله، ودليل فحصته. لو الدليل بيكذّب الكلام هيرد عليك.')
        if st.session_state.get('confront_msg'):
            st.info(st.session_state.pop('confront_msg'))
        _who = st.selectbox('هتواجه مين؟', [p['id'] for p in _cps], format_func=lambda i: next(p['name'] for p in _cps if p['id']==i), key='confront_person')
        _heard = heard_statements(case, state, _who)
        if not _heard:
            st.write('اسمع منه الأول. اسأله من المشهد وبعدين ارجع هنا.')
        else:
            _sid = st.selectbox('كلامه', [h['id'] for h in _heard], format_func=lambda i: next(h['answer'] for h in _heard if h['id']==i), key='confront_statement')
            _ev = [e for e in evidence_cards(case) if e['id'] in state['discovered']]
            _eid = st.selectbox('دليلك', [e['id'] for e in _ev], format_func=lambda i: next(e['id']+' · '+e['title'] for e in _ev if e['id']==i), key='confront_evidence') if _ev else None
            if _eid and st.button('واجهه', key='confront_go'):
                _kind, _out = resolve_confront(case, state, _who, _sid, _eid)
                if _kind == 'unlock':
                    try:
                        persist_room('interview', {'suspect': _who, 'topic': _out['id']})
                        if not room_mode:
                            record_answer(case, state, _who, _out['id'])
                        st.session_state['confront_msg'] = _out['answer']
                        st.rerun()
                    except ValueError as e:
                        st.warning(str(e))
                elif _kind == 'done':
                    st.info(_out['answer'])
                else:
                    st.warning(_out)
solo_unit = room_mode and room["unit_size"]==1
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
        if room_mode:
            persist_room('hint')
            st.rerun()
        else:
            state["hints_used"] += 1
            st.rerun()
    if state["hints_used"]:
        st.info(case.get('hints',['خلي بالك، وقت دخول اللي عملها مش لازم يبقى هو وقت الموت. راجع الزيارة والكوباية والسبب. البصمة لوحدها أو الخناقة لوحدها مش كفاية.'])[min(state['hints_used']-1,len(case.get('hints',[0]))-1)])
    st.subheader("⚖️ مين المتهم وإيه دليلك؟")
    if competitive:
        st.caption("اتهام نهائي واحد" + (" للفريق، لازم كل أعضائه يوافقوا." if room_mode and not solo_unit else " لكل لاعب.") + " لو المتهم أو الأدلة غلط بتخرجوا من السباق. الفوز محتاج الأدلة المطلوبة مش الاسم بس.")
    elif room_mode:
        st.caption("اقتراحك لازم كل اللي في الأوضة يوافقوا عليه عشان التحقيق يقفل.")
    else:
        st.caption("قبل ما تثبّت الاتهام، راجع نفسك: مين عملها؟ وإيه اللي يثبت كلامك؟ اختار الأدلة اللي بتربط الخيوط ببعض. الشك لوحده مش كفاية. ليك قرار أخير واحد في المحاولة.")
    cards = {e["id"]: e for e in evidence_cards(case)}
    with st.form("accusation"):
        selected = st.selectbox("مين اللي عملها؟", [s["name"] for s in case["characters"]], index=None, placeholder="اختار حد",key="final_suspect_"+scene_scope)
        evidence_ids = st.multiselect("إيه الأدلة اللي بصّيت عليها وبتسند كلامك؟", state["discovered"], format_func=lambda x: f"{x} • {cards[x]['title']}",key="final_evidence_"+scene_scope)
        confirmed = st.checkbox("أيوه، ده قراري الأخير وعارف إن المحاولة هتقفل بعده",key="final_confirm_"+scene_scope)
        submitted = st.form_submit_button("ثبّت الاتهام", type="primary")
    if submitted:
        if not confirmed or selected is None or not evidence_ids:
            st.warning("اختار حد ودليل واحد على الأقل، وعلّم إن ده قرارك الأخير.")
        else:
            if room_mode:
                try:
                    proposal = {'suspect':selected,'evidence':sorted(evidence_ids)}
                    room_call('accuse' if solo_unit else 'propose', proposal)
                    st.rerun()
                except RoomError as e:
                    st.warning(str(e))
            else:
                finish_investigation(case, state, selected, evidence_ids)
                st.rerun()

if room_mode and not solo_unit and room['proposal'] and not state['finished']:
    proposal = room['proposal']
    st.subheader('راجع اقتراح الاتهام')
    st.write('المتهم: ' + proposal['suspect'] + ' | الأدلة: ' + '، '.join(proposal['evidence']))
    st.caption('موافقات: ' + str(len(room['approvals'])) + ' من ' + str(room['unit_size']))
    if room['me'] in room['approvals']:
        st.info('موافقتك متسجلة، مستني الباقيين. أي دليل أو استجواب جديد بيلغي الاقتراح عشان تراجعوه تاني.')
    elif st.button('موافق على نفس الاتهام والأدلة، نقفل التحقيق'):
        try:
            room_call('approve', {'proposal':proposal})
            st.rerun()
        except RoomError as e:
            st.warning(str(e))

if not room_mode:
    archive_solo()

st.caption("الفردي بيتحفظ طول الجلسة بس. الأوضة بتحفظ التحقيق والنوتة الخاصة على السيرفر، والرجوع بمفتاحك الشخصي. المجاني ليه حدود وممكن يتوقف مع قلة الاستخدام.")
