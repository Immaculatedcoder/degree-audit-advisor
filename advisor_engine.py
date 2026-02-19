"""
    advisor_engine.py - The AI brain of the Degree Audit Advisor.

    This module uses LangChain + ChromaDB + Ollama to provide Retrieval-Augmented Generation (RAG) for academic advising.

    How it works:
    1. Load degree requirements and course data from JSON files
    2. Split data into smaller chunks
    3. Store chunks in a ChromaDB vector database with embeddings
    4. When a student ask a question, search for the most relevant chunks
    5. Send only the relevant data+question to llama3.2 via Ollama
"""


from typing import Dict, List

import json
import os
import re 

# Pulled from requirements.txt
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from PyPDF2 import PdfReader

def load_knowledge_base() -> Dict[str, Dict]:
    """
    Load degree requirements and course data from our JSON file.

    Returns a dictonary with two keys:
        - "degrees": full degree requirements
        - "courses": the course catalog with prerequisites
    """

    # Get the knowledge_base folder file path ready
    ae_dir = os.path.abspath(__file__)
    base_dir = os.path.dirname(ae_dir)
    kb_dir = os.path.join(base_dir, "knowledge_bank")

    try: 
        courses_dir = os.path.join(kb_dir, "courses.json")
        with open(courses_dir, "r") as f:
            courses = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {courses_dir} was not found")
    except json.JSONDecodeError as e:
        print("Invalid JSON syntax:", e)

    try: 
        degrees_dir = os.path.join(kb_dir, "degrees.json")
        with open(degrees_dir, "r") as f:
            degrees = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {degrees_dir} was not found")
    except json.JSONDecodeError as e:
        print("Invalid JSON syntax:", e)
    print("\n========== Files read successfully =============\n")

    # Convert structured data into searchable text documents
    documents = []

    documents.append(
        f"Program: {degrees['program']} at {degrees['university']}. "
        f"Department: {degrees['department']}. "
        f"Total credits required: {degrees['total_credits_required']}. "
        f"Catalog year: {degrees['catalog_year']}."
    )

    uni_reqs = degrees["university_requirements"]
    documents.append(f"University Requirements: {uni_reqs['description']}")
    for course in uni_reqs["courses"]:
        doc = f"University Requirement: {course['id']} — {course['name']}. Credits: {course['credits']}."
        if "min_grade" in course:
            doc += f" Minimum grade: {course['min_grade']}."
        if "notes" in course:
            doc += f" Notes: {course['notes']}"
        documents.append(doc)

    breadth = uni_reqs["breadth_requirements"]
    documents.append(f"University Breadth Requirements: {breadth['description']}")
    for area in breadth["areas"]:
        doc = f"University Breadth Area: {area['area']} — {area['credits']} credits required."
        if "notes" in area:
            doc += f" {area['notes']}"
        documents.append(doc)
    

    college = degrees["college_requirements"]
    writing = college["second_writing_requirement"]
    # Handle both formats: simple strings ["ENGL312"] or objects [{"id": "ENGL312", ...}]
    approved = writing["approved_courses"]
    if approved and isinstance(approved[0], dict):
        approved_list = [c["id"] for c in approved]
    else:
        approved_list = approved
    documents.append(
        f"College of Arts and Sciences Second Writing Requirement: {writing['description']} "
        f"Approved courses: {', '.join(approved_list)}."
    )

    col_breadth = college["breadth_requirements"]
    documents.append(f"CAS Breadth Requirements: {col_breadth['description']}")
    for group in col_breadth["groups"]:
        documents.append(
            f"CAS Breadth Group {group['group']}: {group['name']} — minimum {group['min_credits']} credits."
        )

    major = degrees["major_requirements"]
    documents.append(f"Major General Notes: {major['general_notes']}")
    documents.append(
        f"First Year Experience: {major['first_year_experience']['course']} — "
        f"{major['first_year_experience']['name']} ({major['first_year_experience']['credits']} credit)."
    )
    core_names = [f"{c['id']} — {c['name']} ({c['credits']} credits)" for c in major["core_courses"]]
    documents.append(
        f"Major Core Courses (ALL required): {'; '.join(core_names)}."
    )

    math_opt = major["mathematics_option"]
    opt_names = [f"{c['id']} — {c['name']} ({c['credits']} credits)" for c in math_opt["courses"]]
    documents.append(
        f"Mathematics Option: {math_opt['description']} "
        f"Choices: {'; '.join(opt_names)}."
    )

    restricted = major["restricted_electives"]
    documents.append(
        f"Restricted Electives: {restricted['description']} "
        f"Rules: {' '.join(restricted['rules'])}"
    )

    lab = major["laboratory_science"]
    documents.append(f"Laboratory Science Requirement: {lab['description']}")
    for seq in lab["sequences"]:
        # Handle both formats: simple strings ["BISC207"] or objects [{"id": "BISC207", ...}]
        seq_courses = seq["courses"]
        if seq_courses and isinstance(seq_courses[0], dict):
            seq_list = [c["id"] for c in seq_courses]
        else:
            seq_list = seq_courses
        documents.append(
            f"Lab Science Option — {seq['name']}: {', '.join(seq_list)} "
            f"({seq['total_credits']} credits total)."
        )
    
    cs = major["computer_science"]
    cs_names = [f"{c['id']} — {c['name']} ({c['credits']} credits)" for c in cs["courses"]]
    documents.append(
        f"Required Computer Science: {cs['description']} Courses: {'; '.join(cs_names)}."
    )

    plan = degrees["four_year_plan_guidance"]
    for semester, course_list in plan.items():
        semester_label = semester.replace("_", " ").title()
        documents.append(
            f"Four Year Plan — {semester_label}: {', '.join(course_list)}."
        )
    for course in courses["courses"]:
        doc = (
            f"Course: {course['id']} — {course['name']}. "
            f"Credits: {course['credits']}. Level: {course['level']}. "
            f"Description: {course['description']} "
            f"Prerequisites: {', '.join(course['prerequisites']) if course['prerequisites'] else 'None'}. "
            f"Corequisites: {', '.join(course['corequisites']) if course['corequisites'] else 'None'}. "
            f"Offered: {', '.join(course['offered'])}."
        )
        if course.get("core_for_bs_math"):
            doc += " This is a CORE required course for BS Math."
        if course.get("math_option"):
            doc += " This is a Mathematics Option course (choose 3 of 6)."
        if course.get("honors_section"):
            doc += f" Honors section: {course['honors_section']}."
        if course.get("satisfies_second_writing"):
            doc += " This course satisfies the CAS Second Writing Requirement."
        if course.get("restricted_elective_eligible") is False:
            doc += " WARNING: This does NOT count as a restricted elective."
        documents.append(doc)

    chains = courses["common_prerequisite_chains"]
    for name, chain in chains.items():
        chain_label = name.replace("_", " ").title()
        documents.append(
            f"Common Prerequisite Chain — {chain_label}: {', '.join(chain)}."
        )
    # return {"degrees": degrees, "courses": courses}
    return documents

def build_vector_store(documents):
    """ 
        Takes our document and store them in a ChromeDB vector database

        Steps:
        1. Split documents into smaller chunks
        2. Create embeddings unsing HuggingFace (text -> numbers)
        3. Store everything in ChromeDB (so it searchable)

        Returns:
            A ChromaDB
    
    """
    # 1) Split

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )

    chunks = []
    for doc in documents:
        # Safety check: make sure every document is a string
        if isinstance(doc, list):
            doc = ", ".join([str(item) for item in doc])
        elif not isinstance(doc, str):
            doc = str(doc)
        splits = text_splitter.split_text(doc)
        chunks.extend(splits)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # 2) Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 3) Store chunks in ChromaDB
    vector_store = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        collection_name="ud_math_advisor"
    )

    return vector_store

def build_system_prompt():
    """ 
        Instruction manual for the AI
    """
    system_prompt = """ 
                        You are Aworawo, an AI academic advisor for the University of Delaware's 
                        BS in Mathematics program in the Department of Mathematical Sciences.

                        FIRST MESSAGE RULE:
                            - When this is the FIRST message in a conversation (only one user message in the history), 
                            ALWAYS start your response with: "Hi! I'm Aworawo 🎓 I can help you navigate your degree 
                            requirements, course planning, prerequisites, and even solve math problems for the BS in 
                            Mathematics at UD."
                            Then add: "\n\nNow, back to your question!\n\n"
                            Then answer their actual question normally.
                            - For ALL subsequent messages, do NOT repeat the introduction. Just answer the question directly.


                        YOUR MISSION:
                            Help students — especially first-generation and international students — in TWO ways:

                            1. ACADEMIC ADVISING: Navigate degree requirements, course planning, and prerequisites 
                            in plain, friendly English. You are a SUPPLEMENT to human advisors, not a replacement. 
                            Always encourage students to confirm important decisions with their official advisor.

                            2. MATH TUTORING: Help students understand and solve math problems related to their coursework.
                            This includes:
                            - Showing step-by-step solutions with clear explanations
                            - Explaining concepts from courses like Calculus, Linear Algebra, Differential Equations, 
                                Probability, Real Analysis, Abstract Algebra, and Discrete Math
                            - Working through practice problems
                            - Explaining WHY each step works, not just HOW
                            - Using simple language before introducing formal notation
                            - If a problem is too complex, break it into smaller parts
                            
                            When solving math problems:
                            - Show your work step by step
                            - Use clear formatting (number each step)
                            - Explain the reasoning behind each step
                            - Provide the final answer clearly marked with 📌
                            - Offer to explain any step in more detail if needed
                        
                        YOUR PERSONALITY:
                        -  Warm, encouraging, patient - like the best advisor your ever had
                        - Use plain English, avoid jargon unless the student use it first
                        - Be specific and actionable - don't just sat "take electives," say WHICH courses and WHY
                        - When a student seems stressed, acknowledge it - "I know this feels overwhelming, but let's break it down"
                        - Use the student's name if they provide it.
                        - Celebrate progress - "You've already knocked out Calc B and C - that's huge!"

                        

                        HOW TO HANDLE DIFFERENT QUESTION TYPES:
                        1. "What courses do I need?" - Walk through the equirements category by category.
                            Show what's done (if the told you) and what's left.
                        2. "What should I take next semester?" - Check prerequisites they've completed, look at what's offered that semester (Fall vs Spring), and suggest a 
                            balanced schedule (typically 4-5 courses, 15-17 credits). Consider prerequisite chains - don't let them get bottlenecked!
                        3. "Can I graduate on time? - Count their completed credits vs 124 needed.
                            Check if they have any prerequisite bottlenecks that could delay them.
                        4. "What are the prerequisites for X?" - Look up the exact prerequisites from the course data.
                            Also mention if there are corequisites. Explain the prerequisite chain if relevant.
                        5. "I'm struggling / thinking about switching majors" - Be supportive. Mention UD resources:
                            - Student Success Center in CAS
                            - Math Sciences Learning Lab
                            - Office hours with professors
                            - Tutoring services
                        6. "I failed / need to retake a course" - Explain how this affects their plan.
                            Help them build a recovery plan. Check if the course is offerered every semsester or only Fall/Spring.

                        IMPORTANT RULES:
                        - ALWAYS check prerequisites before recommending a course
                        - ALWAYS note when a course is only offered in Fall or Spring - this is a common trap!
                        - If you're unsure about something, SAY SO and recommend with their advisor
                        - Never make up course information - only reference courses in your knowledge base
                        - When listing courses, include the course number AND name (e.g., "MATH 245 — Introduction to Proof")
                        - Remind students about the C- minimum grade requirement for major courses
                        - Flag the restricted electives rules - MATH 308, 379, 382 DON'T count

                        FORMAT GUIDELINES:
                            - Use **bold** for course names and important terms
                            - Use ### headings to organize long answers into sections
                            - Use bullet points for lists of courses or requirements
                            - Use ✅ for completed items and ⬜ for remaining items when doing audits
                            - Use ⚠️ for warnings (prerequisite issues, scheduling conflicts, Spring/Fall only courses)
                            - Use 📌 for key takeaways or action items
                            - Use numbered lists (1. 2. 3.) for step-by-step plans or recommended course sequences
                            - Add a brief friendly summary at the end of long answers
                            - Keep responses well-structured but conversational — like a knowledgeable friend, not a textbook
                            - Break up walls of text with spacing and formatting
                            - When recommending a semester schedule, present it in a clear organized format with total credits

                        You will receive CONTEXT with each question — this is real data from the UD catalog.
                        Base your answers on this context. If the context doesn't contain the answer, say so honestly.

                    """
    return system_prompt

def create_advisor():
    """ 
        Initialize the complete advisor system

        Returns: 
            tuple: (llm, vector_store, system_prompt)
    """
    print("Loading knowledge bank...")
    documents = load_knowledge_base()

    print("Building vector database...")
    vector_store = build_vector_store(documents)

    print("Connecting to Ollama")
    llm = ChatOllama(
        model="llama3.2",
        temperature=0,
    )

    system_prompt = build_system_prompt()

    print("Aworawo, your AI Advisor is ready!")
    return llm, vector_store, system_prompt

def get_advisor_response(llm, vector_store, system_prompt, conversation_history):
    """
        The core RAG function - search for relevant data, then ask the AI

        Args:
            llm: The ChatOllama language model
            vector_store: ChromaDB vector database with degree data
            system_prompt: The AI's behavior response
            conversation_history: List of previous messages
                        e.g [{"role": "user", "content": "When do I graduate"}]
    
        Returns:
            str: The AI's response text.
    """
    try:
        latest_question = conversation_history[-1]["content"]

        # Step 2: Search the vector database for relevant context
        # Use HYBRID search: vector similarity + keyword matching
        relevant_docs = vector_store.similarity_search(latest_question, k=10)

        # Also do a keyword search — find any chunks that mention
        # specific course codes from the question (e.g., MATH302)
        import re
        mentioned_courses = re.findall(r'(MATH|CISC|ENGL|PHYS|CHEM|BISC|GEOL)\s*(\d{3})', latest_question.upper())
        course_codes = [f"{dept}{num}" for dept, num in mentioned_courses]

        # Get ALL documents from the vector store for keyword matching
        all_docs = vector_store.similarity_search("course prerequisites offered", k=50)

        # Find chunks that mention the specific courses
        keyword_docs = []
        for doc in all_docs:
            for code in course_codes:
                if code in doc.page_content.upper().replace(" ", ""):
                    keyword_docs.append(doc)
                    break

        # Combine: keyword matches first (most relevant), then vector matches
        seen_content = set()
        combined_docs = []
        for doc in keyword_docs + relevant_docs:
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                combined_docs.append(doc)

        # Limit to top 15
        combined_docs = combined_docs[:15]

        # Debug: show what context was found (remove later)
        # print("\n🔍 Retrieved context chunks:")
        # for i, doc in enumerate(combined_docs):
        #     print(f"  [{i+1}] {doc.page_content[:100]}...")

        # Combine the relevant chunks into one context string
        context = "\n\n".join([doc.page_content for doc in combined_docs])

        messages = []

        # First: system prompt
        messages.append(SystemMessage(content=system_prompt))

        for msg in conversation_history[:-1]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
            
        augmented_question = f"""CONTEXT (from the official UD 2025-2026 Catalog):
                                {context}

                                STUDENT'S QUESTION:
                                {latest_question}

                                Use the CONTEXT above to answer the student's question accurately. 
                                If the context doesn't fully answer the question, say so and recommend they check with their advisor.
                            """
        messages.append(HumanMessage(content=augmented_question))

        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"I'm having trouble right now. Make sure Ollama is running with 'ollama serve'. Error: {str(e)}"
    
def extract_text_from_pdf(uploaded_file)->str:
    """
    Here, we read an uploaded PDF file and extract all text from it.

    This handles unofficial transcripts that students download form UDSIS.
    The extracted text is then passed to the parse_completed_courses(text) to find the course codes.

    Args:
        uploaded_file: A file object from streamlit's file uploader

    Returns:
        str: All text found in the PDF, combined from every page
    """
    try:
        reader = PdfReader(uploaded_file)
        text = ""

        # Loop through every page and grab the text
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if not text.strip():
            return "Error: Could not extract any text from this PDF. Try copying the course manually"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
    
def parse_completed_courses(text)->List:
    """
    This function find all course codes regardless of format.

    Returns: List ["MATH242", "MATh243", "CISC106"]
    """
    pattern = r"(MATH|CISC|ENGL|PHYS|CHEM|BISC|GEOL|UNIV)\s*(\d{3})"
    matches = re.findall(pattern, text.upper())

    # We remove dublicates
    seen = set()
    results = []

    for dept, num in matches:
        course_id = f"{dept}{num}"
        if course_id not in seen:
            seen.add(course_id)
            results.append(course_id)
    return results