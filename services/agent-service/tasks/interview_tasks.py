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

def create_ai_detection_task(agent, answer: str, experience_context: str = ""):
    return Task(
        description=f"""You are an expert at catching AI-generated answers, even ones that have been edited to sound human.

{experience_context}

Now analyze this NEW answer:
---
{answer}
---

Check for these RED FLAGS one by one:

RED FLAG 1 - NO SPECIFIC NUMBERS: Does the answer use vague words like "large", "many", "significant" instead of real numbers like "47 nodes", "3TB", "p99 latency of 800ms"? Real engineers remember specific numbers.

RED FLAG 2 - NO FAILURE STORY: Does the answer only describe the happy path? Real engineers always mention something that went wrong or a lesson learned. AI answers are always successful.

RED FLAG 3 - NO TOOL VERSIONS: Does the answer mention specific versions like "Glue 3.0", "Kubernetes 1.28", "OpenSearch 2.11"? Real engineers remember versions they worked with.

RED FLAG 4 - PERFECT TOPIC COVERAGE: Does the answer cover every single sub-topic equally well with no gaps? Real humans focus on what they know and skip what they don't.

RED FLAG 5 - NO PERSONAL OPINION: Does the answer avoid saying "I prefer X over Y because in my experience..."? AI stays neutral, humans have opinions.

RED FLAG 6 - NARRATIVE STRUCTURE: Does it flow like a story someone told, or like a structured document with clear sections? AI answers have hidden structure even when humanized.

RED FLAG 7 - HEDGING LANGUAGE: Does it use phrases like "it's worth noting", "it's important to", "one approach would be"? These are AI patterns even in humanized text.

Count how many red flags you find. Be strict and suspicious.

Respond exactly like this:
ai_likelihood_score: X (0-100. 0-30=human, 31-60=suspicious, 61-100=AI)
verdict: likely_human OR possibly_ai OR likely_ai
red_flags_found: X out of 7
reason: two sentences explaining the top signals you found""",
        expected_output="ai_likelihood_score 0-100, verdict, red_flags_found, and reason.",
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
        description=f"""You must generate 2 follow-up questions that will EXPOSE whether this candidate truly has hands-on experience or is faking it with AI help.

Question asked: {question}
Candidate answered: {answer}

Rules for your follow-up questions:
- Pick ONE specific claim or number they mentioned and drill into it
- Ask about a specific failure, edge case, or unexpected problem
- Ask something that requires them to recall a specific moment, not explain a concept
- Make it impossible to answer well without having actually done this work
- ChatGPT cannot answer these well because they require personal memory

Example of a BAD follow-up: "Can you explain more about AWS Glue?"
Example of a GOOD follow-up: "You mentioned multipart uploads - what was the chunk size you used and why, and did you ever have a failed part that needed retry logic?"

Number them 1 and 2.""",
        expected_output="2 follow-up questions that require genuine personal experience to answer.",
        agent=agent,
    )

def create_report_task(agent, session_data: dict):
    candidate = session_data.get("candidate_name", "Candidate")
    role = session_data.get("role", "Engineer")
    answers_count = len(session_data.get("answers", []))

    # Extract AI scores from session for report context
    ai_scores = []
    for a in session_data.get("answers", []):
        det = a.get("ai_detection", {})
        if isinstance(det, dict) and det.get("ai_likelihood_score"):
            ai_scores.append(det["ai_likelihood_score"])
    avg_ai = round(sum(ai_scores) / len(ai_scores)) if ai_scores else 0
    high_ai = any(s >= 60 for s in ai_scores)

    return Task(
        description=f"""Write a hiring report for {candidate} applying for {role}.
They answered {answers_count} questions.
Average AI likelihood score across answers: {avg_ai}/100
High AI suspicion detected: {high_ai}

Important: If average AI score is above 50, the recommendation should reflect serious concern about answer authenticity.
If high AI suspicion is True, explicitly call it out in the report.

Write the report like this exactly:
recommendation: HIRE or MAYBE or NO_HIRE
summary: two sentences about the candidate performance and authenticity
strengths: list 2 genuine strengths observed
gaps: list 2 knowledge gaps or concerns
ai_usage: low or medium or high
ai_note: one sentence about whether answers appeared authentic or AI-assisted""",
        expected_output="Hiring recommendation with summary, strengths, gaps, AI usage assessment and note.",
        agent=agent,
    )
