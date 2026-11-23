import streamlit as st
from game_engine import generate_case, investigate

st.set_page_config(
    page_title="بلاغ",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 بلاغ")

st.markdown(
    "## وصل بلاغ... والحقيقة مستخبية في التفاصيل."
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

    st.subheader("📄 تفاصيل البلاغ")

    st.write(
        f"تم العثور على {case['victim']} داخل {case['location']} في ظروف غامضة."
    )

    st.markdown("---")

    st.subheader("🕵️ إجراءات التحقيق")

    col1, col2 = st.columns(2)

    with col1:

        if st.button("🔍 فحص الجثة"):
            result = investigate("فحص الجثة")
            st.session_state.evidence.append(result)

        if st.button("📱 فحص الهاتف"):
            result = investigate("فحص الهاتف")
            st.session_state.evidence.append(result)

    with col2:

        if st.button("📹 مراجعة الكاميرات"):
            result = investigate("مراجعة الكاميرات")
            st.session_state.evidence.append(result)

        if st.button("👤 استجواب الشاهد"):
            result = investigate("استجواب الشاهد")
            st.session_state.evidence.append(result)

    st.markdown("---")

    st.subheader("📂 الأدلة المكتشفة")

    if st.session_state.evidence:

        for item in st.session_state.evidence:
            st.info(item)

    else:

        st.warning("لم يتم جمع أي أدلة حتى الآن.")

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

    if st.button("إحالة للنيابة"):

        if selected == case["killer"]["name"]:

            st.success(
                f"""
✅ تم حل القضية

المتهم:
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
