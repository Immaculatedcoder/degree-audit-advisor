import streamlit as st

from advisor_engine import (
    create_advisor,
    get_advisor_response,
    parse_completed_courses,
    extract_text_from_pdf,
)

# --------------------------------
#      Page configuration 
# --------------------------------

st.set_page_config(
    page_title="Professor Mark - UD Math Advisor",
    page_icon="🎓 ",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
        <style>
            .main-header {
                # background: linear-gradient(135deg, #00539F 0%, #003366 100%)

            
            }
        </style>
    """, unsafe_allow_html=True
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "completed_courses" not in st.session_state:
    st.session_state.completed_courses = []

@st.cache_resource(show_spinner=False)
def init_advisor():
    """ Load the advisor engine once and cache it"""
    return create_advisor()

with st.spinner("Professor Mark is getting ready...(this may take a minute in first load)"):
    llm, vector_store, system_prompt = init_advisor()

st.markdown("""
<div class="main-header">
    <h1>🎓 Aworawo AI</h1>
    <p>AI Academic Advisor — BS Mathematics, University of Delaware</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(" Quick Questions")
    st.caption("Click any question to get started:")

    quick_questions = [
        "What courses do I need for BS Math?",
        "What should I take next semester?",
        "What are the prerequisite for MATH 302?",
        "Can I graduate in 4 years?",
        "What are the Math Option courses?",
        "What are the restricted elective rules?"
    ]

    for q in quick_questions:
        if st.button(q, key=f"quick_{q}"):
            st.session_state.messages.append({"role": "user", "content": q})
            with st.spinner("Aworawo is thinking..."):
                response = get_advisor_response()