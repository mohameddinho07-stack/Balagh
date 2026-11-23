import streamlit as st
from game_engine import generate_case

st.set_page_config(
    page_title="بلاغ",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 بلاغ")
st.markdown("### وصل بلاغ... والحقيقة مستخبية.")

if "case" not in st.session_state:
    st.session_state.case = None

if st.button("استلام بلاغ جديد 🚔"):
    st.session_state.case = generate_case()

if st.session_state.case:

    case = st.session_state.case

    st.markdown("---")

    st.subheader("📄 تفاصيل البلاغ")

    st.write(
        f"تم العثور على **{case['victim']}** داخل **{case['location']}** في ظروف غامضة."
    )

    st.markdown("---")

    st.subheader("🕵️ المشتبه بهم")

    cols = st.columns(2)

    for idx, suspect in enumerate(case["suspects"]):

        with cols[idx % 2]:

            st.info(
                f"""
الاسم: {suspect['name']}

العمر: {suspect['age']} سنة

الوظيفة: {suspect['job']}
"""
            )

    st.markdown("---")

    st.subheader("⚖️ قرار الاتهام")

    suspect_names = [s["name"] for s in case["suspects"]]

    selected = st.selectbox(
        "اختر المتهم الرئيسي",
        suspect_names
    )

    if st.button("إحالة للنيابة"):

        if selected == case["killer"]["name"]:

            st.success(
                f"""
✅ تم حل القضية

المتهم الحقيقي:
{case['killer']['name']}

الوظيفة:
{case['killer']['job']}

السر:
{case['killer']['secret']}
"""
            )

        else:

            st.error(
                f"""
❌ اتهام خاطئ

المتهم الحقيقي كان:
{case['killer']['name']}
"""
            )
