import streamlit as st
from game_engine import (generate_case, new_investigation, evidence_cards,
                         available_questions, record_answer, finish_investigation)

st.set_page_config(page_title="بلاغ", page_icon="🚨", layout="wide")
st.markdown("""<style>
[data-testid="stAppViewContainer"] {direction:rtl;text-align:right;}
[data-testid="stSidebar"] {direction:rtl;}
.stButton button, .stSelectbox, .stMultiSelect, textarea {direction:rtl;}
h1, h2, h3, [data-testid="stCaptionContainer"] {text-align:right;direction:rtl;}
[data-testid="stMainBlockContainer"] {max-width:1100px;}
</style>""", unsafe_allow_html=True)
st.title("بلاغ")
st.caption("قضية خيالية مصرية • نسخة فردية تجريبية • استجواب مكتوب، بدون AI أو اتصال بخدمات خارجية")
mode = st.radio("اختر نمط اللعبة", ["🔍 التحقيق الفردي", "🎮 اللعب الجماعي"], horizontal=True)
if mode == "🎮 اللعب الجماعي":
    st.info("اللعب الجماعي غير متاح في هذه النسخة. لا توجد غرف حقيقية أو لاعبين متصلين بعد. ارجع للتحقيق الفردي لتجربة القضية.")
    st.stop()

if "case" not in st.session_state:
    st.session_state.case = None

if st.session_state.case is None:
    st.subheader("بلاغ 001 • الغرفة المغلقة")
    st.write("افحص الأدلة، استجوب أربع شخصيات، ثم اربط اتهامك بالأدلة. القرار النهائي يُنهي المحاولة؛ الحل لا يظهر إلا بطلبك بعدها.")
    if st.button("🚔 بدء التحقيق", type="primary"):
        st.session_state.case = generate_case()
        st.session_state.investigation = new_investigation()
        st.rerun()
    st.stop()

case = st.session_state.case
state = st.session_state.investigation
public = case["public"]
st.subheader(f"بلاغ {case['id']} • {public['title']}")
st.caption(f"المكان: {public['location']} | الضحية: {public['victim']}")
st.info(public["story"])
if state["finished"]:
    result = state["result"]
    if result["success"]:
        st.success("اتهام مدعوم بالسلسلة المطلوبة من الأدلة. انتهت المحاولة.")
    elif result["killer_correct"]:
        st.warning("اخترت الفاعل، لكن سلسلة الأدلة المقدمة غير مكتملة. انتهت المحاولة، ويمكنك مراجعة الحل أو البدء من جديد.")
    else:
        st.error("الاتهام لا يطابق حل القضية. انتهت المحاولة. لم نكشف اسم الفاعل؛ راجع الحل فقط لو أردت.")
    st.write(f"قرارك: {result['suspect']} | الأدلة: {', '.join(result['submitted_evidence'])}")
    if st.checkbox("أريد كشف الحل وشرح الأدلة", key="reveal_solution"):
        st.subheader(f"الحل: {case['truth']['killer']}")
        st.write(case["truth"]["explanation"])
    if st.button("بدء محاولة جديدة", type="primary"):
        for key in list(st.session_state):
            del st.session_state[key]
        st.rerun()

a, b, c = st.columns(3)
a.metric("أدلة فُحصت", f"{len(state['discovered'])}/{len(evidence_cards(case))}")
b.metric("إجابات مسجلة", len(state["interviews"]))
c.metric("تلميحات مستخدمة", state["hints_used"])

with st.expander("🕒 التسلسل الزمني"):
    for item in public["timeline"]:
        st.write(item)

st.subheader("ملف الأدلة")
st.caption("افتح التقرير للقراءة، ثم اضغط فحص الدليل لتسجيله وإتاحة أسئلة المواجهة المرتبطة به.")
for evidence in evidence_cards(case):
    inspected = evidence["id"] in state["discovered"]
    with st.expander(f"{evidence['id']} • {evidence['title']} {'✓' if inspected else ''}"):
        st.write(evidence["text"])
        if st.button("تم فحص الدليل", key=f"inspect_{evidence['id']}", disabled=inspected or state["finished"]):
            state["discovered"].append(evidence["id"])
            st.rerun()

st.subheader("🕵️ الاستجواب")
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
            st.caption(f"أسئلة مواجهة إضافية مقفلة: {locked}. افحص أدلة أخرى لفتحها.")
        for entry in state["interviews"]:
            if entry["suspect"] == suspect["name"]:
                st.markdown(f"**س: {entry['question']}**")
                st.write(f"ج: {entry['answer']}")

with st.expander("🗂️ سجل الاستجوابات", expanded=False):
    if not state["interviews"]:
        st.write("لم تسجل إجابات بعد.")
    for entry in state["interviews"]:
        st.write(f"{entry['suspect']} | {entry['question']}")
        st.write(entry["answer"])

st.subheader("📓 دفتر المحقق")
st.text_area("ملاحظاتك واستنتاجاتك، محفوظة خلال الجلسة فقط", key="detective_notes", height=150)
if not state["finished"]:
    if st.button("💡 تلميح بدون كشف الفاعل"):
        state["hints_used"] += 1
    if state["hints_used"]:
        st.info("افصل بين وقت دخول الجاني ووقت الوفاة. اختبر ادعاء المغادرة، ثم اربط الزيارة بالكوب والدافع؛ البصمة أو الخصومة وحدهما لا يكفيان.")
    st.subheader("⚖️ قرار الاتهام")
    st.caption("قرار واحد لكل محاولة. اختر المتهم والأدلة التي تربط الزيارة بالفعل والدافع، وليس كل ما يثير الشك.")
    cards = {e["id"]: e for e in evidence_cards(case)}
    with st.form("accusation"):
        selected = st.selectbox("المتهم الرئيسي", [s["name"] for s in case["characters"]], index=None, placeholder="اختر المتهم")
        evidence_ids = st.multiselect("الأدلة الداعمة التي فحصتها", state["discovered"], format_func=lambda x: f"{x} • {cards[x]['title']}")
        confirmed = st.checkbox("أعتمد القرار النهائي وأفهم أنه يُنهي هذه المحاولة")
        submitted = st.form_submit_button("اعتماد الاتهام", type="primary")
    if submitted:
        if not confirmed or selected is None or not evidence_ids:
            st.warning("اختر متهمًا ودليلًا واحدًا على الأقل وأكد اعتماد القرار.")
        else:
            finish_investigation(case, state, selected, evidence_ids)
            st.rerun()

st.caption("التقدم محفوظ في جلسة المتصفح الحالية فقط، وليس في حساب أو قاعدة بيانات. تحديث الاتصال أو انتهاء الجلسة قد يفقده. لا توجد خدمة AI أو غرف مشتركة في هذه النسخة.")
