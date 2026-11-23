import streamlit as st
from game_engine import (generate_case, new_investigation, evidence_cards,
                         available_questions, record_answer, finish_investigation)

st.set_page_config(page_title="بلاغ", page_icon="🚨", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"] {direction:rtl;text-align:right;}
[data-testid="stSidebar"] {direction:rtl;}
.stButton button, .stSelectbox, .stMultiSelect, textarea {direction:rtl;}
[data-testid="stMarkdownContainer"] p, .stButton button p {direction:rtl;unicode-bidi:plaintext;text-align:right;}
h1, h2, h3, [data-testid="stCaptionContainer"] {text-align:right;direction:rtl;}
[data-testid="stMainBlockContainer"] {max-width:1100px;}
</style>""", unsafe_allow_html=True)
st.title("بلاغ")
st.caption("حكاية جريمة من خيالنا • جرّب تلعب لوحدك • تجربة AI مع نادين، وباقي الشخصيات بأسئلة جاهزة")
mode = st.radio("تحب تلعب إزاي؟", ["🔍 العب لوحدك", "🎮 العب مع صحابك"], horizontal=True)
if mode == "🎮 العب مع صحابك":
    st.info("اللعب مع صحابك لسه مش شغّال. مفيش أوض ولا لعيبة متوصلين ببعض دلوقتي. اختار تلعب لوحدك وجرّب القضية.")
    st.stop()

if "case" not in st.session_state:
    st.session_state.case = None

if st.session_state.case is None:
    st.subheader("بلاغ 001 • الغرفة المغلقة")
    st.write("بص يا حضرة الظابط، قدامك بلاغ قتل وأربع أشخاص لازم تسمع منهم. امسك الملف واحدة واحدة، وراجع كل كلمة على الأدلة. مش عايزين اسم وخلاص، عايزين تعرف مين عملها وتقول دليلك إيه. ولما تثبّت اتهامك، المحاولة هتقفل. الحل مش هيتقالك إلا لو طلبته بعدها.")
    if st.button("🚔 يلا نحقق", type="primary"):
        st.session_state.case = generate_case()
        st.session_state.investigation = new_investigation()
        st.rerun()
    st.stop()

case = st.session_state.case
state = st.session_state.investigation
public = case["public"]
st.subheader(f"بلاغ {case['id']} • {public['title']}")
st.caption(f"المكان: {public['location']} | اللي اتقتل: {public['victim']}")
st.info(public["story"])
if state["finished"]:
    result = state["result"]
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
    if st.button("نجرّب من الأول", type="primary"):
        for key in list(st.session_state):
            del st.session_state[key]
        st.rerun()

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

st.subheader("📂 الأدلة اللي في المحضر")
st.caption("افتح الدليل واقراه، وبعدها دوس «بصّيت على الدليل ده». كده هيتسجّل عندك ويفتحلك أسئلة تواجه بيها الناس.")
for evidence in evidence_cards(case):
    inspected = evidence["id"] in state["discovered"]
    with st.expander(f"{evidence['id']} • {evidence['title']} {'✓' if inspected else ''}"):
        st.write(evidence["text"])
        if st.button("بصّيت على الدليل ده", key=f"inspect_{evidence['id']}", disabled=inspected or state["finished"]):
            state["discovered"].append(evidence["id"])
            st.rerun()

st.subheader("🕵️ نسمع أقوالهم")
for suspect in case["characters"]:
    with st.expander(suspect["name"]):
        st.caption(f"{suspect['job']} • {suspect['age']} سنة")
        st.write(suspect["public_info"])
        unlocked = available_questions(suspect, state["discovered"])
        for question in unlocked:
            if st.button(question["question"], key=f"ask_{question['id']}", disabled=state["finished"]):
                record_answer(case, state, suspect["id"], question["id"])
                st.rerun()
        locked = len(suspect["interviews"]) - len(unlocked)
        if locked:
            st.caption(f"أسئلة مواجهة لسه مقفولة: {locked}. بصّ على أدلة تانية عشان تفتحها.")
        for entry in state["interviews"]:
            if entry["suspect"] == suspect["name"]:
                st.markdown(f"**س: {entry['question']}**")
                st.write(f"ج: {entry['answer']}")

st.subheader("💬 اسأل نادين بطريقتك، تجربة AI")
st.caption("AI من Groq بيفهم سؤالك وسياق آخر كلامكم. الرد نفسه من كلام القضية المكتوب، عشان الحقيقة والأدلة ما يتغيّروش. لسه مش حوار مولّد بحرية.")
st.warning("سؤالك وآخر 4 أسئلة بيتبعتوا لـ Groq. ما تكتبش بيانات شخصية أو أسرار. لو الحد المجاني خلص، التجربة بتقف من غير دفع، والأسئلة الجاهزة تفضل شغّالة.")
try:
    groq_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    groq_key = ""
if not groq_key:
    st.info("ربط AI مش جاهز على السيرفر دلوقتي. تقدر تكمّل بالأسئلة الجاهزة.")
else:
    from ai_interrogation import ask_nadine, AIUnavailable
    st.caption(f"أسئلة AI في المحاولة: {len(state.get('ai_interviews', []))}/20")
    with st.form("nadine_ai", clear_on_submit=True):
        free_question = st.text_input("هتسأل نادين إيه؟", max_chars=350,
                                      placeholder="إنتي سيبتي الفندق إمتى؟")
        ai_sent = st.form_submit_button("اسأل نادين", disabled=state["finished"])
    if ai_sent:
        try:
            with st.spinner("نادين بتسمع سؤالك..."):
                ask_nadine(case, state, free_question, groq_key)
            st.rerun()
        except AIUnavailable as error:
            st.warning(str(error))
    for turn in state.get("ai_interviews", []):
        with st.container(border=True):
            st.text("إنت: " + turn["question"])
            st.write("نادين: " + turn["answer"])

with st.expander("🗂️ الناس قالت إيه؟", expanded=False):
    if not state["interviews"]:
        st.write("لسه ما سألتش حد.")
    for entry in state["interviews"]:
        st.write(f"{entry['suspect']} | {entry['question']}")
        st.write(entry["answer"])

st.subheader("📓 نوتة التحقيق")
st.text_area("اكتب اللي واخد بالك منه هنا، هيفضل معاك طول ما جلسة اللعب شغّالة بس", key="detective_notes", height=150)
if not state["finished"]:
    if st.button("💡 ادّيني طرف خيط من غير حرق"):
        state["hints_used"] += 1
    if state["hints_used"]:
        st.info("خلي بالك، وقت دخول اللي عملها مش لازم يبقى هو وقت الموت. شوف حكاية «أنا مشيت» دي صح ولا لأ، واربط الزيارة بالكوباية والسبب. البصمة لوحدها أو الخناقة لوحدها مش كفاية.")
    st.subheader("⚖️ مين المتهم وإيه دليلك؟")
    st.caption("قبل ما تثبّت الاتهام، راجع نفسك: مين عملها؟ وإيه اللي يثبت كلامك؟ اختار الأدلة اللي بتربط زيارته باللي حصل وسببه. الشك لوحده مش كفاية. ليك قرار أخير واحد في المحاولة.")
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
            finish_investigation(case, state, selected, evidence_ids)
            st.rerun()

st.caption("اللعبة فاكرة اللي عملته طول جلسة اللعب دي بس، مش بتحفظه في حساب. لو الاتصال اتجدد أو الجلسة قفلت ممكن يضيع. تجربة AI متاحة مع نادين بس، ولسه مفيش أوض تلعب فيها مع صحابك.")
