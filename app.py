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
    page_title="Aworawo - UD Math Advisor",
    page_icon="🎓 ",
    layout="wide",
    initial_sidebar_state="auto"
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

with st.spinner("Aworawo is getting ready...(this may take a minute in first load)"):
    llm, vector_store, system_prompt = init_advisor()

st.markdown("""
<div class="main-header">
    <h1> Aworawo 🐦‍🔥 </h1>
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
                response = get_advisor_response(llm, vector_store, system_prompt, st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    # Transcript Upload
    st.markdown("---")
    st.markdown("Upload Transcript")
    st.caption("Upload your unofficial transcript (PDF) to get a more personalized advise from Aworawo AI. ")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="transcript")

    if uploaded_file is not None:
        with st.spinner("Reading your Transcript..."):
            transcript_text = extract_text_from_pdf(uploaded_file)

            if transcript_text.startswith("ERROR"):
                st.error(transcript_text)
            else:
                courses = parse_completed_courses(transcript_text)

                if courses:
                    st.session_state.completed_courses = courses
                    st.success(f"Found {len(courses)} courses in your transcript!")

                    courses_msg = f"I've completed these courses: {', '.join(courses)}. What should I take next?"
                    if not any(m["content"] == courses_msg for m in st.session_state.messages):
                        st.session_state.messages.append({"role": "user", "content": courses_msg})
                        with st.spinner("Aworawo is analyzing your transcripts"):
                            response = get_advisor_response(llm, vector_store, system_prompt, st.session_state.messages)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        st.rerun()
                    else:
                        st.warning(" Couldn't find any course codes in the PDF. Try Typing instead")

    st.markdown("---")
    st.markdown("Your Courses")

    if st.session_state.completed_courses:
        chips_html = ""
        for course in st.session_state.completed_courses:
            chips_html += f"""
                        <span style="
                            display:inline-block;
                            padding:6px 12px;
                            margin:4px;
                            background:#e0e7ff;
                            color:#1e3a8a;
                            border-radius:16px;
                            font-size:14px;
                            font-weight:500;
                        ">
                            {course}
                        </span>
                        """
        if st.button("Clear Courses"):
            st.session_state.completed_courses = []
            st.rerun()
    else:
        st.caption("No courses tracked yet. Upload a transcript!")
    
    st.markdown("---")
    if st.button("New Conversation"):
        st.session_state.messages = []
        st.session_state.completed_courses = []
        st.rerun()

# Main Chat Interface
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar=" 🧑‍🎓 "):
            st.markdown(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant", avatar="🎓"):
            st.markdown(message["content"])

# Show a welcome message
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🎓"):
        st.markdown(
            " Hi! I'm **Aworawo 🐦‍🔥**, I can help you navigate your degree requirements, course planning, prerequisites,"
            " and even solve math problems for the BS in Mathematics at UD. \n\n"
            "Try asking me something, or click a quick question in the sidebar!"
        )

if prompt := st.chat_input("Ask Aworawo anything..."):
    with st.chat_message("user", avatar=" 🧑‍🎓 "):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    mentioned_courses = parse_completed_courses(prompt)
    if mentioned_courses:
        for course in mentioned_courses:
            if course not in st.session_state.completed_courses:
                st.session_state.completed.append(course)

    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("Aworawo is thinking..."):
            response(llm, vector_store,system_prompt,st.session_state.messages)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

if st.session_state.messages:
    msg_count = len(st.session_state.messages)
    course_count = len(st.session_state.completed_courses)
    st.markdown(
        f'<div class="stats-bar">💬 {msg_count} messages | ✅ {course_count} courses tracked</div>',
        unsafe_allow_html=True,
    )