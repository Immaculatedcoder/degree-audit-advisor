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

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"knowledge_bank")


def fetch_page(url):
    """
        Here: We
        1. Open a browser
        2. Go to the URL
        3. View page source
        4. Handle resonse code
    """
    # Pretend we are Chome
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print(f"Fetching: {url}")
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        print(f"ERROR: Got status code {response.status_code} from url")
        return None
    
    print(f"Success! Got {len(response.text)} characters of HTML.")
    return BeautifulSoup(response.text, "html.parser")

def parse_prerequisite_table(soup):
    """
    Parse the prerequisites table from the UD Math course offerings page.
    """
    prereqs = {}

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")

            if len(cells) == 3:
                course = cells[0].get_text(strip=True)
                prerequisite = cells[1].get_text(strip=True)
                corequisite = cells[2].get_text(strip=True)

                # Remove ALL non-ASCII characters (hidden unicode like zero-width spaces)
                import unicodedata
                course = ''.join(c for c in course if unicodedata.category(c) != 'Cf')
                course = re.sub(r'\s+', '', course).upper()

                prerequisite = ''.join(c for c in prerequisite if unicodedata.category(c) != 'Cf')
                prerequisite = prerequisite.strip()

                corequisite = ''.join(c for c in corequisite if unicodedata.category(c) != 'Cf')
                corequisite = corequisite.strip()

                if course.startswith("MATH") and len(course) >= 7:
                    prereqs[course] = {
                        "prerequisites": prerequisite if prerequisite and prerequisite.upper() != "NONE" else "None",
                        "corequisites": corequisite if corequisite else "None"
                    }

    print(f"Found prerequisite for {len(prereqs)} course(s).")
    return prereqs

def parse_semester_offerings(soup):
    """
        The page has a table with two columns:
        - Fall 
        - Spring
    """
    fall_courses = set()
    spring_courses = set()

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")

            if len(cells) == 2:
                fall_text = cells[0].get_text(strip=True)
                spring_text = cells[1].get_text(strip=True)

                fall_matches = re.findall(r'M(\d{3})', fall_text)
                spring_matches = re.findall(r'M(\d{3})', spring_text)

                for num in fall_matches:
                    fall_courses.add(f"MATH{num}")
                for num in spring_matches:
                    spring_courses.add(f"MATH{num}")
    
    all_courses = fall_courses | spring_courses

    offerings = {}

    for course in all_courses:
        semesters = []

        if course in fall_courses:
            semesters.append("Fall")
        if course in spring_courses:
            semesters.append("Spring")
        offerings[course] = semesters
    
    print(f"Found semester data for {len(offerings)} courses.")
    return offerings

COURSE_DEFINITIONS = {
    "MATH010": {"name": "Intermediate Algebra", "credits": 0, "level": "preparatory",
                "description": "Preparatory algebra course. Does not count toward degree credits."},
    "MATH115": {"name": "Pre-Calculus", "credits": 4, "level": "100",
                "description": "Preparation for calculus. Covers functions, trigonometry, and algebraic techniques."},
    "MATH117": {"name": "Pre-Calculus for Scientists and Engineers", "credits": 4, "level": "100",
                "description": "Accelerated pre-calculus for STEM students. Leads directly into MATH 241."},
    "MATH205": {"name": "Statistical Methods", "credits": 3, "level": "200",
                "description": "Applied statistics course covering data analysis and inference."},
    "MATH210": {"name": "Discrete Mathematics I", "credits": 3, "level": "200",
                "description": "Logic, sets, proof techniques, combinatorics, graph theory. Foundational for upper-level math.",
                "core_for_bs_math": True},
    "MATH221": {"name": "Calculus I", "credits": 4, "level": "200",
                "description": "Single-variable differential calculus. Not the typical starting point for math majors."},
    "MATH230": {"name": "Finite Mathematics with Applications", "credits": 3, "level": "200",
                "description": "Linear algebra and probability with applications to business and social sciences."},
    "MATH231": {"name": "Integrated Calculus IA", "credits": 4, "level": "200",
                "description": "First part of a two-semester sequence integrating pre-calculus and Calculus I."},
    "MATH232": {"name": "Integrated Calculus IB", "credits": 4, "level": "200",
                "description": "Second part of the integrated calculus sequence. Equivalent to MATH 241."},
    "MATH241": {"name": "Analytic Geometry and Calculus A", "credits": 4, "level": "200",
                "description": "Single-variable calculus: limits, derivatives, integrals. Standard entry point for math majors."},
    "MATH242": {"name": "Analytic Geometry and Calculus B", "credits": 4, "level": "200",
                "description": "Continuation of calculus: techniques of integration, series, parametric equations.",
                "core_for_bs_math": True, "honors_section": "Offered every Fall"},
    "MATH243": {"name": "Analytic Geometry and Calculus C", "credits": 4, "level": "200",
                "description": "Multivariable calculus: partial derivatives, multiple integrals, vector calculus.",
                "core_for_bs_math": True, "honors_section": "Offered every Spring"},
    "MATH245": {"name": "An Introduction to Proof", "credits": 3, "level": "200",
                "description": "Bridge course to upper-level math. Proof techniques, set theory, functions. Critical gateway course.",
                "core_for_bs_math": True},
    "MATH302": {"name": "Ordinary Differential Equations", "credits": 3, "level": "300",
                "description": "First and second order ODEs, systems, Laplace transforms, applications.",
                "core_for_bs_math": True},
    "MATH305": {"name": "Applied Mathematics for the Biological Sciences", "credits": 3, "level": "300",
                "description": "Mathematical modeling in biology using differential equations and computation."},
    "MATH308": {"name": "Historical Development of Mathematical Concepts and Ideas", "credits": 3, "level": "300",
                "description": "History of mathematics. Satisfies CAS second writing requirement. WARNING: Does NOT count as a restricted elective.",
                "satisfies_second_writing": True, "restricted_elective_eligible": False},
    "MATH315": {"name": "Discrete Mathematics II", "credits": 3, "level": "300",
                "description": "Advanced combinatorics, graph theory, algorithms. Builds on MATH 210.",
                "math_option": True},
    "MATH342": {"name": "Applied Mathematics for Chemical and Biomolecular Engineering", "credits": 3, "level": "300",
                "description": "Applied math techniques for engineering students."},
    "MATH349": {"name": "Elementary Linear Algebra", "credits": 3, "level": "300",
                "description": "Matrix algebra, vector spaces, eigenvalues, linear transformations. Fundamental for upper-level math.",
                "core_for_bs_math": True, "honors_section": "Offered every Fall"},
    "MATH350": {"name": "Probability Theory and Simulation Methods", "credits": 3, "level": "300",
                "description": "Probability distributions, random variables, expectation, simulation. Foundation for statistics.",
                "core_for_bs_math": True},
    "MATH351": {"name": "Engineering Mathematics I", "credits": 3, "level": "300",
                "description": "ODEs and linear algebra for engineers. Parallel to MATH 302 + MATH 349 combined."},
    "MATH352": {"name": "Engineering Mathematics II", "credits": 3, "level": "300",
                "description": "PDEs, Fourier series, boundary value problems for engineers."},
    "MATH353": {"name": "Engineering Mathematics III", "credits": 3, "level": "300",
                "description": "Numerical methods and computation for engineers."},
    "MATH401": {"name": "Introduction to Real Analysis", "credits": 3, "level": "400",
                "description": "Rigorous treatment of limits, continuity, differentiation, integration. Essential for graduate school.",
                "math_option": True},
    "MATH426": {"name": "Computational Mathematics I", "credits": 3, "level": "400",
                "description": "Numerical methods: root finding, interpolation, numerical integration, linear systems.",
                "math_option": True},
    "MATH428": {"name": "Computational Mathematics II", "credits": 3, "level": "400",
                "description": "Advanced numerical methods for ODEs and PDEs."},
    "MATH450": {"name": "Mathematical Statistics", "credits": 3, "level": "400",
                "description": "Statistical inference, estimation, hypothesis testing. Builds on MATH 350.",
                "math_option": True},
    "MATH451": {"name": "Abstract Algebra I", "credits": 3, "level": "400",
                "description": "Groups, rings, fields. Core abstract math course for graduate school preparation.",
                "math_option": True},
    "MATH460": {"name": "Introduction to Mathematical Biology", "credits": 3, "level": "400",
                "description": "Mathematical modeling in biology."},
    "MATH512": {"name": "Contemporary Applications of Mathematics", "credits": 3, "level": "500",
                "description": "Real-world applications of mathematics. Core course AND satisfies CAS second writing requirement.",
                "core_for_bs_math": True, "satisfies_second_writing": True},
    "MATH535": {"name": "Introduction to Partial Differential Equations", "credits": 3, "level": "500",
                "description": "Heat equation, wave equation, Laplace equation, Fourier methods.",
                "math_option": True},
    "CISC106": {"name": "General Computer Science for Engineers", "credits": 3, "level": "100",
                "description": "Intro to programming (MATLAB/Python). Required for BS Math."},
    "CISC210": {"name": "Introduction to Systems Programming", "credits": 3, "level": "200",
                "description": "C programming, memory management, Unix. Required for BS Math."},
    "CISC220": {"name": "Data Structures", "credits": 3, "level": "200",
                "description": "Lists, trees, graphs, sorting, searching. Required for BS Math."},
    "ENGL110": {"name": "First-Year Writing", "credits": 3, "level": "100",
                "description": "University-required writing course. Must earn C- or better."},
    "ENGL312": {"name": "Written Communications in Business", "credits": 3, "level": "300",
                "description": "Business writing. Satisfies CAS second writing requirement.",
                "satisfies_second_writing": True},
    "ENGL410": {"name": "Technical Writing", "credits": 3, "level": "400",
                "description": "Technical and scientific writing. Satisfies CAS second writing requirement.",
                "satisfies_second_writing": True},
}

def build_courses_json(prereqs, offerings):
    """
    We combined scraped prerequisite + semester data with base course definitions to produce a complete course.json

    """

    courses = []

    for course_id, definition in COURSE_DEFINITIONS.items():
        course = {
            "id": course_id,
            "name": definition["name"],
            "credits": definition["credits"],
            "level": definition["level"],
            "description" : definition["description"]
        }

        # Merge scraped prerequisites (live from UD website)
        if course_id in prereqs:
            scraped = prereqs[course_id]
            prereq_text = scraped["prerequisites"]
            coreq_text = scraped["corequisites"]

            # Clean non-breaking spaces and split on common separators (& , and)
            if prereq_text and prereq_text != "None":
                prereq_text = prereq_text.replace('\xa0', ' ')
                # Split on & or "and" to get individual courses
                parts = re.split(r'\s*&\s*|\s+and\s+', prereq_text)
                course["prerequisites"] = [p.strip() for p in parts if p.strip()]
            else:
                course["prerequisites"] = []

            if coreq_text and coreq_text != "None":
                coreq_text = coreq_text.replace('\xa0', ' ')
                parts = re.split(r'\s*&\s*|\s+and\s+', coreq_text)
                course["corequisites"] = [p.strip() for p in parts if p.strip()]
            else:
                course["corequisites"] = []
        else:
            course["prerequisites"] = []
            course["corequisites"] = []

        if course_id in offerings:
            course["offered"] = offerings[course_id]
        else:
            course["offered"] = ["Fall", "Spring"]

        for flag in ["core_for_bs_math", "math_option", "honors_section", "satisfies_second_writing", "restricted_elective_eligible"]:
            if flag in definition:
                course[flag] = definition[flag]
        courses.append(course)

        result = {
        "courses": courses,
        "semester_availability_notes": {
            "MATH222": "Not offered every Spring",
            "MATH260": "Requires instructor permission",
            "honors_sections": [
                "MATH242 Honors: every Fall",
                "MATH243 Honors: every Spring",
                "MATH349 Honors: every Fall"
            ]
        },
        "common_prerequisite_chains": {
            "calculus_sequence": ["MATH117 -> MATH241 -> MATH242 -> MATH243"],
            "proof_track": ["MATH210 + MATH242 -> MATH245 -> MATH401 or MATH451"],
            "applied_track": ["MATH242 + MATH349 -> MATH302 -> MATH535"],
            "statistics_track": ["MATH243 (coreq) -> MATH350 -> MATH450"],
            "cs_sequence": ["CISC106 -> CISC210 -> CISC220"]
        }
    }
        
    return result

def main():
    """ 
        The main function
    """

    print("=" * 60)
    print(" UD Catalog Scraper - Updating knowledge Bank")
    print("="*60)

    # 1) Fetch Course offerings
    print("\n Fetching course offering page...")
    courses_soup = fetch_page(COURSES_URL)

    if courses_soup:
        print("\n Parsing prerequisite...")
        prereqs = parse_prerequisite_table(courses_soup)

        print("\n Parsing semester offerings...")
        offerings = parse_semester_offerings(courses_soup)

        print("\n Building courses.json...")
        courses_data = build_courses_json(prereqs,offerings)

        courses_path = os.path.join(OUTPUT_DIR, "courses.json")

        with open(courses_path, "w") as f:
            json.dump(courses_data, f, indent=2)
        print(f"Saved courses.json with {len(courses_data['courses'])} courses!")

    else:
        print("Failed to fetch course offerings page. Skikked courses.json update...")
    
    print("\n Knowledge base updated successfully!")
    print(f"Files saved to: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()