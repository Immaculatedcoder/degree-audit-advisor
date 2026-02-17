"""
advisor_engine.py - The AI brain of the Degree Audit Advisor.

This module:
1. loads structured degree requirement data from JSON files,
2. Builds a detailed system prompt that makes the AI an expert on UD's BS in Mathematics degree requirements,
3. Sends student questions to Ollama (llama3.2) and returns accurate, context-aware answers in a conversational format.
"""

import json
import os
import ollama

# Load degree requirements from JSON file

def load_knowledge_base():
    """
    Load degree requirements and course data from our JSON file.

    Returns a dictonary with two keys:
        - "degrees": 
    """

