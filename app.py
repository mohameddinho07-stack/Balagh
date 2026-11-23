import streamlit as st
from game_engine import generate_case

st.set_page_config(
    page_title="بلاغ",
    page_icon="🚨"
)

st.title("🚨 بلاغ")
st.write("وصل بلاغ... والحقيقة مستخبية.")

if "case" not in st.session_state:
    st.session_state.case = None

if st.button("استلام بلاغ جديد"):
    st.session_state.case = generate_case()

if st.session_state.case:

    case = st.session_state.case

    st.subheader("📋 بيانات البلاغ")

    st.write(f"نوع البلاغ: {case['crime']}")
    st.write(f"المكان: {case['location']}")

    st.subheader("👥 المشتبه بهم")

    for suspect in case["suspects"]:
        st.write(f"- {suspect}")

    st.subheader("🔍 الأدلة")

    for clue in case["clues"]:
        st.info(clue)

    selected = st.selectbox(
        "من المتهم الرئيسي؟",
        case["suspects"]
    )

    if st.button("إحالة للنيابة"):

        if selected == case["killer"]:

            st.success(
                f"✅ تم حل القضية\n\nالمتهم الحقيقي: {case['killer']}"
            )

        else:

            st.error(
                f"❌ اتهام خاطئ\n\nالمتهم الحقيقي: {case['killer']}"
            )