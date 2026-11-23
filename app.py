import streamlit as st
from game_engine import generate_case, investigate, get_timeline

st.set_page_config(
    page_title="بلاغ",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 بلاغ")

if "case" not in st.session_state:
    st.session_state.case = None

if "evidence" not in st.session_state:
    st.session_state.evidence = []

if st.button("🚔 بدء التحقيق"):

    st.session_state.case = generate_case()
    st.session_state.evidence = []

if st.session_state.case:

    case = st.session_state.case

    st.markdown(
        f"""
# 🚨 بلاغ رقم 001

## القضية: {case['title']}

📍 الموقع: {case['location']}

👤 الضحية: {case['victim']}
"""
    )

    st.error(case["story"])

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:

        with st.expander("📁 تقرير الطب الشرعي"):

            if st.button("تحليل الجثة"):
                st.session_state.evidence.append(
                    investigate("فحص الجثة")
                )

            st.write(
                "الضحية توفي في ظروف غامضة ولا توجد إصابات ظاهرة."
            )

        with st.expander("📁 كاميرات المراقبة"):

            if st.button("مراجعة الكاميرات"):
                st.session_state.evidence.append(
                    investigate("مراجعة الكاميرات")
                )

            st.write(
                "يوجد فقد في جزء من التسجيلات."
            )

        with st.expander("📁 سجل المكالمات"):

            if st.button("فحص الهاتف"):
                st.session_state.evidence.append(
                    investigate("فحص الهاتف")
                )

   
