"""
Test Fixtures: Sample Documents
Provides consistent test data across test suite
"""

from typing import List, Dict

# Sample Air Force-style documents for testing
SAMPLE_DOCUMENTS = [
    {
        "text": """Air Force Instruction 36-2903: Dress and Personal Appearance of Air Force Personnel

1. OVERVIEW
This instruction prescribes the authorization, wear, and appearance of Air Force uniforms and civilian clothing.

2. UNIFORM STANDARDS
All Airmen must maintain professional military appearance when in uniform. Uniforms will be clean, pressed, and properly fitted. Hair must be neat, clean, and professional in appearance.

3. FOOTWEAR
Conservative black or brown oxfords are the primary duty footwear. Athletic shoes may be worn with the physical training uniform only.

4. JEWELRY
Airmen may wear one ring per hand, a conservative watch, and up to three bracelets on the non-watch wrist.
""",
        "metadata": {
            "document_id": "AFI-36-2903",
            "file_name": "dafi36-2903.pdf",
            "page": 1,
            "chunk_index": 0,
            "category": "uniform_regulations",
            "file_type": "pdf"
        }
    },
    {
        "text": """Air Force Instruction 36-3003: Military Leave Program

1. PURPOSE
This instruction implements policy for military leave, passes, and permissive temporary duty.

2. LEAVE ACCRUAL
Active duty members accrue 2.5 days of leave per month, for a total of 30 days per fiscal year. Leave may be carried over to the next fiscal year up to a maximum of 60 days.

3. TYPES OF LEAVE
Regular Leave: Used for rest, relaxation, and personal affairs.
Emergency Leave: Granted for personal or family emergencies.
Convalescent Leave: Prescribed by medical authority for recovery.

4. LEAVE APPROVAL
Leave requests must be submitted through the member's chain of command. Leave may be disapproved for operational requirements.
""",
        "metadata": {
            "document_id": "AFI-36-3003",
            "file_name": "dafi36-3003.pdf",
            "page": 1,
            "chunk_index": 0,
            "category": "leave_policy",
            "file_type": "pdf"
        }
    },
    {
        "text": """Air Force Instruction 36-2905: Physical Fitness Program

1. PROGRAM OVERVIEW
The Air Force Physical Fitness Program is a year-round fitness program that emphasizes total fitness. It includes exercise, health promotion, and fitness assessment.

2. FITNESS ASSESSMENT
The fitness assessment consists of four components:
- Aerobic fitness: 1.5 mile run or alternative
- Body composition: Abdominal circumference measurement
- Push-ups: Maximum repetitions in 1 minute
- Sit-ups: Maximum repetitions in 1 minute

3. SCORING
Members are scored on a 100-point scale, with passing score of 75 points required. Score breakdowns:
- Excellent: 90-100
- Satisfactory: 75-89.9
- Unsatisfactory: <75

4. TESTING FREQUENCY
Members with scores of 90 or above may test annually. Members scoring between 75-89.9 test semi-annually.
""",
        "metadata": {
            "document_id": "AFI-36-2905",
            "file_name": "dafi36-2905.pdf",
            "page": 1,
            "chunk_index": 0,
            "category": "fitness",
            "file_type": "pdf"
        }
    },
    {
        "text": """Air Force Instruction 36-2110: Assignments

1. ASSIGNMENT POLICY
Assignments are based on Air Force requirements, matched with individual qualifications and preferences when possible.

2. ASSIGNMENT CYCLES
Officers: Assignment vulnerable dates typically 18-24 months before projected move.
Enlisted: Assignment cycles vary by Air Force Specialty Code (AFSC).

3. OVERSEAS TOURS
Accompanied tours: 36 months
Unaccompanied tours: 12-15 months depending on location

4. SPECIAL DUTY ASSIGNMENTS
Assignments to special duty positions (Recruiter, Instructor, etc.) are typically 3-4 year controlled tours.
""",
        "metadata": {
            "document_id": "AFI-36-2110",
            "file_name": "dafi36-2110.pdf",
            "page": 1,
            "chunk_index": 0,
            "category": "assignments",
            "file_type": "pdf"
        }
    },
    {
        "text": """Air Force Manual 36-2108: Enlisted Classification

1. AIR FORCE SPECIALTY CODES (AFSC)
Each enlisted member is classified into an AFSC based on their training and qualifications.

2. SKILL LEVELS
1-Level: Helper (apprentice in technical training)
3-Level: Apprentice (initial qualification)
5-Level: Journeyman (qualified to perform independently)
7-Level: Craftsman (supervisor capability)
9-Level: Superintendent (senior enlisted leader)

3. SPECIALTY TRAINING
Initial Skills Training (technical school) provides qualification to 3-level. On-the-job training and career development courses lead to advancement.

4. RETRAINING
Airmen may retrain into critically manned career fields subject to eligibility and Air Force needs.
""",
        "metadata": {
            "document_id": "AFM-36-2108",
            "file_name": "afman36-2108.pdf",
            "page": 1,
            "chunk_index": 0,
            "category": "classification",
            "file_type": "pdf"
        }
    }
]


# Sample queries for testing with expected document matches
SAMPLE_QUERIES = [
    {
        "query": "What are the uniform regulations?",
        "expected_type": "simple",
        "expected_doc_id": "AFI-36-2903",
        "difficulty": "easy"
    },
    {
        "query": "How many days of leave do I get per year?",
        "expected_type": "simple",
        "expected_doc_id": "AFI-36-3003",
        "difficulty": "easy"
    },
    {
        "query": "What is the passing score for the fitness test?",
        "expected_type": "simple",
        "expected_doc_id": "AFI-36-2905",
        "difficulty": "easy"
    },
    {
        "query": "What are the different types of leave available?",
        "expected_type": "moderate",
        "expected_doc_id": "AFI-36-3003",
        "difficulty": "medium"
    },
    {
        "query": "Compare the fitness standards to the uniform requirements",
        "expected_type": "complex",
        "expected_doc_id": None,  # Multiple docs
        "difficulty": "hard"
    },
    {
        "query": "How long are overseas assignments?",
        "expected_type": "simple",
        "expected_doc_id": "AFI-36-2110",
        "difficulty": "easy"
    },
    {
        "query": "What are the skill levels in the Air Force?",
        "expected_type": "simple",
        "expected_doc_id": "AFM-36-2108",
        "difficulty": "easy"
    },
    {
        "query": "What happens if I fail the fitness assessment?",
        "expected_type": "moderate",
        "expected_doc_id": "AFI-36-2905",
        "difficulty": "medium"
    },
    {
        "query": "Can I wear jewelry with my uniform?",
        "expected_type": "simple",
        "expected_doc_id": "AFI-36-2903",
        "difficulty": "easy"
    },
    {
        "query": "What is the process for retraining into a new career field?",
        "expected_type": "moderate",
        "expected_doc_id": "AFM-36-2108",
        "difficulty": "medium"
    }
]


# Out-of-scope queries (should be rejected)
OUT_OF_SCOPE_QUERIES = [
    "What is the weather forecast for tomorrow?",
    "How do I cook a perfect steak?",
    "What are the latest stock market trends?",
    "Who won the Super Bowl last year?",
    "What is quantum computing?",
    "How do I fix my car engine?",
    "What are the best vacation destinations?",
    "What is the recipe for chocolate cake?",
    "What are the rules of chess?",
    "How do I train a dog?"
]


def get_sample_documents() -> List[Dict]:
    """Get sample documents for testing"""
    return SAMPLE_DOCUMENTS.copy()


def get_sample_queries() -> List[Dict]:
    """Get sample queries for testing"""
    return SAMPLE_QUERIES.copy()


def get_out_of_scope_queries() -> List[str]:
    """Get out-of-scope queries for testing"""
    return OUT_OF_SCOPE_QUERIES.copy()


def get_query_by_difficulty(difficulty: str) -> List[Dict]:
    """Get queries filtered by difficulty"""
    return [q for q in SAMPLE_QUERIES if q["difficulty"] == difficulty]


def get_query_by_type(query_type: str) -> List[Dict]:
    """Get queries filtered by expected classification type"""
    return [q for q in SAMPLE_QUERIES if q["expected_type"] == query_type]
