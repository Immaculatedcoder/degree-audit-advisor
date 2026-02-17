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


def load_knowledge_base() -> Dict[str, object]:
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
    return {"degrees": degrees, "courses": courses}




def main():
    load_knowledge_base()


if __name__ == "__main__":
    main()


