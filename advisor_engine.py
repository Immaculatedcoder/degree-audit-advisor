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

# Pulled from requirements.txt

import json
import os
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from PyPDF2 import PdfReader

