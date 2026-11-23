import streamlit as st
from game_engine import generate_case, investigate, get_timeline

st.set_page_config(
    page_title="بلاغ",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 بلاغ")

st.markdown(
    "## وصل بلاغ... والحقيقة مستخبية في التفاصيل"
)

if "case" not in st.session_state:
    st.session_state.case = None

if "evidence" not in st.session_state:
    st.session_state.evidence = []

if st.button("🚔 استلام بلاغ جديد"):
    st.session_state.case = generate_case()
    st.session_state.evidence = []

if st.session_state.case:

    case = st.session_state.case

    st.markdown("---")

    st.markdown(f"""
# 🚨 بلاغ رقم 001

## القضية: {case['title']}

📍 المكان: {case['location']}

👤 الضحية: {case['victim']}
""")

    st.write(case["story"])

    st.markdown("---")

    st.subheader("📁 التسلسل الزمني")

    for item in get_timeline():
        st.write("•", item)

    st.markdown("---")

    st.subheader("📁 الأدلة")

    if st.button("🔍 فحص الجثة"):
        st.session_state.evidence.append(
            investigate("فحص الجثة")
        )

    if st.button("📱 فحص الهاتف"):
        st.session_state.evidence.append(
            investigate("فحص الهاتف")
        )

    if st.button("📹 مراجعة الكاميرات"):
        st.session_state.evidence.append(
            investigate("مراجعة الكاميرات")
        )

    if st.button("👤 استجواب الشاهد"):
        st.session_state.evidence.append(
            investigate("استجواب الشاهد")
        )

    for ev in st.session_state.evidence:
        st.success(ev)
