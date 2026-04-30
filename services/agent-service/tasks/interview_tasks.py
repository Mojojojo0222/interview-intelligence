from crewai import Task

def create_plan_task(agent, role: str, level: str):
    return Task(
        description=f"""
        Create a structured interview plan for a {level} {role} candidate.
        Include:
        - Key skill areas to cover (max 5)
        - Time allocation per section
        - Difficulty progression strategy
        - Red flags to watch for at this level
        Output as structured JSON.
        """,
        expected_output="JSON interview plan with skill areas, time allocation, and red flags",
        agent=agent,
    )

def create_questions_task(agent, role: str, level: str, plan: str):
    return Task(
        description=f"""
        Based on this interview plan: {plan}
        Generate 5 technical interview questions for a {level} {role}.
        Each question must:
        - Test real hands-on experience
        - Not be answerable by simply reciting documentation
        - Include what a strong answer looks like
        Output as JSON array with question and expected_strong_answer fields.
        """,
        expected_output="JSON array of 5 questions with expected strong answers",
        agent=agent,
    )

def create_analyze_answer_task(agent, question: str, answer: str):
    return Task(
        description=f"""
        Analyze this candidate answer:
        Question: {question}
        Answer: {answer}

        Score on:
        - Technical depth (0-10)
        - Specificity with real examples (0-10)
        - Clarity of explanation (0-10)
        - Overall authenticity (0-10)
        Provide brief reasoning for each score.
        Output as JSON.
        """,
        expected_output="JSON with scores for depth, specificity, clarity, authenticity and reasoning",
        agent=agent,
    )

def create_ai_detection_task(agent, answer: str):
    return Task(
        description=f"""
        Analyze this interview answer for signs of AI generation:
        Answer: {answer}

        Check for:
        - Overly formal or structured language
        - Lack of personal pronouns or first-person experience
        - Suspiciously comprehensive coverage of all sub-topics
        - Perfect grammar with no natural hesitation or filler
        - Generic examples not tied to specific companies/projects
        - Unnaturally balanced pros/cons lists

        Return:
        - ai_likelihood_score: 0-100
        - confidence: low/medium/high
        - detected_patterns: list of patterns found
        - verdict: "likely_human" | "possibly_ai" | "likely_ai"
        Output as JSON.
        """,
        expected_output="JSON with ai_likelihood_score, confidence, detected_patterns, and verdict",
        agent=agent,
    )

def create_domain_validation_task(agent, question: str, answer: str):
    return Task(
        description=f"""
        Validate the technical accuracy of this answer:
        Question: {question}
        Answer: {answer}

        Check for:
        - Factual correctness of AWS/DevOps/SRE claims
        - Correct use of terminology
        - Any dangerous misunderstandings or anti-patterns
        - Missing critical concepts

        Return:
        - accuracy_score: 0-10
        - correct_claims: list
        - incorrect_claims: list
        - missing_concepts: list
        Output as JSON.
        """,
        expected_output="JSON with accuracy_score, correct_claims, incorrect_claims, missing_concepts",
        agent=agent,
    )

def create_followup_task(agent, question: str, answer: str, analysis: str):
    return Task(
        description=f"""
        Based on this exchange:
        Original Question: {question}
        Candidate Answer: {answer}
        Analysis: {analysis}

        Generate 3 follow-up questions that:
        - Dig into specific claims the candidate made
        - Cannot be answered well by an LLM without real experience
        - Expose potential knowledge gaps identified in the analysis
        - Reference specific details from their answer to make it personal

        Output as JSON array with question and why_this_question fields.
        """,
        expected_output="JSON array of 3 follow-up questions with reasoning",
        agent=agent,
    )

def create_report_task(agent, session_data: dict):
    return Task(
        description=f"""
        Generate a comprehensive interview report from this session data:
        {session_data}

        Report must include:
        - Candidate summary
        - Technical scores per question (average)
        - AI usage assessment with overall likelihood
        - Domain accuracy summary
        - Top 3 strengths
        - Top 3 knowledge gaps
        - Final recommendation: HIRE / MAYBE / NO_HIRE
        - Recommendation justification (2-3 sentences)
        Output as structured JSON.
        """,
        expected_output="Complete JSON interview report with all scores and hire recommendation",
        agent=agent,
    )
