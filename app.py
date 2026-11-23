import streamlit as st
from game_engine import generate_case, investigate, get_timeline

st.set_page_config(
    page_title="🚨 بلاغ",
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

## القضية:
