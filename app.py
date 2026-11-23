import streamlit as st
from game_engine import generate_case

st.set_page_config(
    page_title="بلاغ",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 بلاغ")

if "case" not in st.session_state:
    st.session_state.case = None

if st.button("🚔 بدء التحقيق"):
    st.session_state.case = generate_case()

if st.session_state.case:

    case = st.session_state.case

    st.markdown(f"""
# 🚨 بلاغ رقم 001

## القضية: {case["title"]}

📍 الموقع: {case["location"]}

👤 الضحية: {case["victim"]}
""")

    st.error(case["story"])

    st.markdown("---")

    with st.expander("📁 تقرير الطب الشرعي"):
        st.text(case["forensic_report"])

    with st.expander("📁 كاميرات المراقبة"):
        st.text(case["camera_report"])

    with st.expander("📁 سجل المكالمات"):
        st.text(case["call_log"])

    with st.expander("📁 أقوال الشهود"):
        st.text(case["witness_statement"])

    with st.expander("📁 التسلسل الزمني"):
        for item in case["timeline"]:
            st.write(item)

    st.markdown("---")

    st.subheader("🕵️ المشتبه بهم")

    for suspect in case["suspects"]:
        st.info(
            f"""
الاسم: {suspect['name']}

العمر: {suspect['age']}

الوظيفة: {suspect['job']}
"""
        )

    st.markdown("---")

    st.subheader("⚖️ قرار الاتهام")

    suspect_names = [
        s["name"]
        for s in case["suspects"]
    ]

    selected = st.selectbox(
        "اختر المتهم الرئيسي",
        suspect_names
    )

    if st.button("⚖️ توجيه الاتهام"):

        if selected == case["killer"]:

            st.success(
                f"""
✅ تم حل القضية

المتهم الحقيقي:
{case['killer']}
"""
            )

        else:

            st.error(
                f"""
❌ اتهام خاطئ

المتهم الحقيقي:
{case['killer']}
"""
            )
