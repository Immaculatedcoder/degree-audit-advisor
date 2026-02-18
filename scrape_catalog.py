"""

    srcape_catalog.py - Scrapes the UD catalog to generate knowledge base files.

    We have to run the script anytime the catalog updates:
        python scrape_catalog.py
    
    It will:
        1. Fetch the BS Math program page form catalog.udel.edu
        2. Fetch the course offering page (prerequisite table)
        3. Parse both page using BeautifulSoup
        4. Generate fresh degree.json and course.json in the knowledege_base folder
"""

import json
import os
import re
import requests
from bs4 import BeautifulSoup

PROGRAM_URL = "https://catalog.udel.edu/preview_program.php?catoid=94&poid=92629&print="
COURSES_URL = "https://www.udel.edu/academics/colleges/cas/units/departments/mathematical-sciences/undergraduate-programs/course-offerings/"

OUTPUT_URL = os.path.join(os.path.dirname(os.path.abspath(__file__)),"knowledge_bank")