from crewai import Task

def create_plan_task(agent, role: str, level: str):
    return Task(
        description=f"Create a brief interview plan for a {level} {role}. List 3 key skill areas to test and 2 red flags to watch for. Be concise.",
        expected_output="A short interview plan with skill areas and red flags.",
        agent=agent,
    )

def create_questions_task(agent, role: str, level: str, plan: str):
    return Task(
        description=f"Generate 3 technical interview questions for a {level} {role}. Each question should test real hands-on experience, not theory. Number them 1, 2, 3.",
        expected_output="3 numbered technical interview questions.",
        agent=agent,
    )

def create_analyze_answer_task(agent, question: str, answer: str):
    return Task(
        description=f"""Score this interview answer from 0-10 on each dimension.
Question: {question}
Answer: {answer}

Give scores like this exactly:
technical_depth: X
specificity: X  
clarity: X
authenticity: X
reasoning: one sentence why""",
        expected_output="Scores for technical_depth, specificity, clarity, authenticity each 0-10.",
        agent=agent,
    )

def create_ai_detection_task(agent, answer: str):
    return Task(
        description=f"""Analyze if this answer was written by a human or AI.
Answer: {answer}

Look for: formal language, no personal stories, perfect structure, no hesitation words.
Respond exactly like this:
ai_likelihood_score: X (0-100, higher means more likely AI)
verdict: likely_human OR possibly_ai OR likely_ai
reason: one sentence""",
        expected_output="ai_likelihood_score 0-100, verdict, and reason.",
        agent=agent,
    )

def create_domain_validation_task(agent, question: str, answer: str):
    return Task(
        description=f"""Check if this DevOps/AWS answer is technically correct.
Question: {question}
Answer: {answer}

Respond exactly like this:
accuracy_score: X (0-10)
correct: what they got right in one sentence
incorrect: any mistakes in one sentence (or 'none')""",
        expected_output="accuracy_score 0-10, correct claims, incorrect claims.",
        agent=agent,
    )

def create_followup_task(agent, question: str, answer: str, analysis: str):
    return Task(
        description=f"""Based on this interview answer, generate 2 follow-up questions.
Question asked: {question}
Candidate said: {answer}

The follow-ups must:
- Reference something specific the candidate said
- Be impossible to answer without real experience
- Not be answerable by ChatGPT

Number them 1 and 2.""",
        expected_output="2 numbered follow-up questions based on the candidate's specific answer.",
        agent=agent,
    )

def create_report_task(agent, session_data: dict):
    candidate = session_data.get("candidate_name", "Candidate")
    role = session_data.get("role", "Engineer")
    answers_count = len(session_data.get("answers", []))
    return Task(
        description=f"""Write a hiring report for {candidate} applying for {role}.
They answered {answers_count} questions.
Session data summary: {str(session_data)[:500]}

Write the report like this exactly:
recommendation: HIRE or MAYBE or NO_HIRE
summary: two sentences about the candidate
strengths: list 2 strengths
gaps: list 2 knowledge gaps
ai_usage: low or medium or high suspicion of AI use""",
        expected_output="Hiring recommendation with summary, strengths, gaps, and AI usage assessment.",
        agent=agent,
    )
