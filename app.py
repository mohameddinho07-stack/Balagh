import streamlit as st
from game_engine import generate_case, investigate

st.set_page_config(
    page_title="🚨 بلاغ",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 بلاغ")
st.markdown("## وصل بلاغ... والحقيقة مستخبية في التفاصيل")

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

## القضية: الغرفة المغلقة

**المكان:** {case['location']}

**الضحية:** {case['victim']}

تم العثور على الضحية داخل جناح خاص بفندق النيل الملكي.

الغرفة كانت مغلقة من الداخل.

لا توجد آثار اقتحام.

لا يوجد سلاح جريمة واضح.

توجد تناقضات في توقيت الوفاة.
""")

    st.markdown("---")

    st.subheader("📂 ملف القضية")

    st.warning(
        "بعض الأدلة قد تكون مضللة. لا تفترض أن أول مشتبه به هو القاتل."
    )

    st.markdown("---")

    st.subheader("🕵️ المشتبه بهم")

    for suspect in case["suspects"]:

        st.info(
            f"""
الاسم: {suspect['name']}

العمر: {suspect['age']} سنة

الوظيفة: {suspect['job']}
"""
        )

    st.markdown("---")

    st.subheader("🔎 إجراءات التحقيق")

    col1, col2 = st.columns(2)

    with col1:

        if st.button("🔍 فحص الجثة"):
            st.session_state.evidence.append(
                investigate("فحص الجثة")
            )

        if st.button("📱 فحص الهاتف"):
            st.session_state.evidence.append(
                investigate("فحص الهاتف")
            )

    with col2:

        if st.button("📹 مراجعة الكاميرات"):
            st.session_state.evidence.append(
                investigate("مراجعة الكاميرات")
            )

        if st.button("👤 استجواب الشاهد"):
            st.session_state.evidence.append(
                investigate("استجواب الشاهد")
            )

    st.markdown("---")

    st.subheader("📋 الأدلة المكتشفة")

    if st.session_state.evidence:

        for ev in st.session_state.evidence:
            st.success(ev)

    else:

        st.info(
            "لم يتم اكتشاف أي أدلة حتى الآن."
        )

    st.markdown("---")

    st.subheader("⚖️ قرار الاتهام")

    suspect_names = [
        s["name"]
        for s in case["suspects"]
    ]

    selected = st.selectbox(
        "اختر المتهم",
        suspect_names
    )

    if st.button("⚖️ إحالة للنيابة"):

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
