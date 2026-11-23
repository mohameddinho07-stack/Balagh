import streamlit as st
from game_engine import generate_case

st.set_page_config(
    page_title="بلاغ",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 بلاغ")
mode = st.radio(
    "اختر نمط اللعبة",
    [
        "🔍 Investigation Mode",
        "🎮 Multiplayer"
    ]
)

if mode == "🎮 Multiplayer":

    st.subheader("🎮 Multiplayer Lobby")

    player_name = st.text_input(
        "اسم اللاعب"
    )

    room_code = st.text_input(
        "كود الغرفة"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎮 إنشاء غرفة"):
            st.success(
                "سيتم ربط إنشاء الغرفة بقاعدة البيانات في الخطوة القادمة"
            )

    with col2:
        if st.button("🚪 دخول غرفة"):
            st.success(
                f"{player_name} انضم إلى الغرفة {room_code}"
            )

    st.stop()
if "case" not in st.session_state:
    st.session_state.case = None

if st.button("🚔 بدء التحقيق"):
    st.session_state.case = generate_case()

if st.session_state.case:

    case = st.session_state.case

    st.markdown(
        f"""
# 🚨 بلاغ رقم 001

## القضية: {case["title"]}

📍 الموقع: {case["location"]}

👤 الضحية: {case["victim"]}
"""
    )

    st.error(case["story"])

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:

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

    with col2:

        st.subheader("🕵️ المشتبه بهم")

        for suspect in case["suspects"]:

            with st.expander(f"🕵️ {suspect['name']}"):

                st.write(f"**المهنة:** {suspect['job']}")
                st.write(f"**العمر:** {suspect['age']}")

                if st.button(
                    f"🎤 استجواب {suspect['name']}",
                    key=f"ask_{suspect['name']}"
                ):

                    st.info(
                        f"""
👤 الاسم: {suspect['name']}

💼 المهنة: {suspect['job']}

📝 الإفادة الأولية:

أنا {suspect['name']}.

جاوبت على كل أسئلة الشرطة،
ومش شايف إن ليا علاقة مباشرة بالجريمة.

لكن واضح إن في ناس كتير مخبية حاجات.
"""
                    )

    st.markdown("---")

    st.subheader("📓 دفتر المحقق")

    notes = st.text_area(
        "اكتب ملاحظاتك واستنتاجاتك",
        height=200
    )

    st.markdown("---")

    st.subheader("⚖️ قرار الاتهام")

    suspect_names = [
        suspect["name"]
        for suspect in case["suspects"]
    ]

    selected = st.selectbox(
        "اختر المتهم الرئيسي",
        suspect_names
    )

    if st.button("⚖️ توجيه الاتهام"):

        if selected == case["truth"]["killer"]:

            st.success(
                """
✅ اتهام صحيح

أحسنت أيها المحقق.

لقد تمكنت من كشف الحقيقة.
"""
            )

        else:

            st.error(
                f"""
❌ اتهام خاطئ

المتهم الحقيقي:

{case['truth']['killer']}
"""
            )
