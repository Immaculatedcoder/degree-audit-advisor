"""
advisor_engine.py - The AI brain of the Degree Audit Advisor.

This module:
1. loads structured degree requirement data from JSON files,
2. Builds a detailed system prompt that makes the AI an expert on UD's BS in Mathematics degree requirements,
3. Sends student questions to Ollama (llama3.2) and returns accurate, context-aware answers in a conversational format.
"""

from typing import List, Dict

import json
import os
import ollama


# Load degree requirements from JSON file


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
    kb_dir = os.path.join(base_dir, "knowledge_base")

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
    return {"degrees": degrees, "courses": courses}

def build_system_prompt(knowledge_base: Dict[str, Dict]) -> str:
    """
    Here, we want to build the system instruction manual that will be used by our llm in this process.

    Nothing much, just an AI Math Advisor
    
    """
    degrees = json.dumps(knowledge_base["degrees"], indent=2)
    courses = json.dumps(knowledge_base["courses"], indent=2)

    system_prompt = f"""
                        You are Mark, a friendly and knowledgeable University of Delaware academic advisor specializing in the BS in Mathematics program.

                        Your role:
                        - Help students understand the degree requirements, prerequisite, and course options.


                        YOUR MISSION:
                        Help students - especially first-generation and international students - navigate their degree requirements, course planning, and prerequisites in 
                                        plain, friendly English. You are a SUPPLEMENT to human advisors, not a replacement. Always encourage students to comfirm important decisions
                                        with their offical advisor.
                        
                        YOUR PERSONALITY:
                        -  Warm, encouraging, patient - like the best advisor your ever had
                        - Use plain English, avoid jargon unless the student use it first
                        - Be specific and actionable - don't just sat "take electives," say WHICH courses and WHY
                        - When a student seems stressed, acknowledge it - "I know this feels overwhelming, but let's break it down"
                        - Use the student's name if they provide it.
                        - Celebrate progress - "You've already knocked out Calc B and C - that's huge!"

                        DEGREE REQUIREMENTS DATA (from the official 2025-2026 UD Catalog): {degrees}

                        COURSE CATALOG WITH PREREQUISITES including description of each course: {courses}

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
                        - Use clear headings when giving long answers
                        - Use checkmarks for completed items and squares for remaining items when doing audits
                        - Use warning signs for warnings (prerequisite issues, scheduling conflicts)
                        - Keep responses focused - students are busy and stressed
                    """
    return system_prompt

def create_advisor()->str:
    """
        Initialize the advisor by loading data and building the system prompt.
    """
    knowledge_base = load_knowledge_base()
    system_prompt = build_system_prompt(knowledge_base)

    return system_prompt






def main():
    load_knowledge_base()


if __name__ == "__main__":
    main()


