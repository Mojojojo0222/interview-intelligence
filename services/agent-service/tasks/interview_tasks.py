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
        description=f"""You are an expert at catching AI-generated answers, even ones edited to sound human.

{experience_context}

Analyze this answer:
---
{answer}
---

Check each RED FLAG:
RED FLAG 1 - NO SPECIFIC NUMBERS: Uses vague words instead of real numbers?
RED FLAG 2 - NO FAILURE STORY: Only describes success, no mistakes mentioned?
RED FLAG 3 - NO TOOL VERSIONS: No specific versions like Kubernetes 1.28?
RED FLAG 4 - PERFECT COVERAGE: Covers every sub-topic equally with no gaps?
RED FLAG 5 - NO PERSONAL OPINION: Never says "I prefer X because in my experience"?
RED FLAG 6 - HIDDEN STRUCTURE: Reads like a document not a conversation?
RED FLAG 7 - HEDGING LANGUAGE: Uses "it's worth noting", "one approach would be"?

Respond exactly:
ai_likelihood_score: X
verdict: likely_human OR possibly_ai OR likely_ai
red_flags_found: X
reason: two sentences on top signals found""",
        expected_output="ai_likelihood_score 0-100, verdict, red_flags_found, reason.",
        agent=agent,
    )


def create_domain_validation_task(agent, question: str, answer: str):
    return Task(
        description=f"""Check if this DevOps/AWS answer is technically correct.
Question: {question}
Answer: {answer}

Respond exactly:
accuracy_score: X (0-10)
correct: what they got right in one sentence
incorrect: any mistakes (or 'none')
missing: key concepts not mentioned (or 'none')""",
        expected_output="accuracy_score, correct claims, incorrect claims, missing concepts.",
        agent=agent,
    )


def create_followup_task(agent, question: str, answer: str, analysis: str):
    return Task(
        description=f"""Generate 3 follow-up questions that will EXPOSE whether this candidate truly has hands-on experience.

Question asked: {question}
Candidate answered: {answer}

Rules:
- Pick specific claims they made and drill into them
- Ask about a specific failure or edge case
- Require personal memory to answer well
- ChatGPT cannot answer these without real experience

Number them 1, 2, 3.""",
        expected_output="3 numbered follow-up questions requiring genuine personal experience.",
        agent=agent,
    )


def create_report_task(agent, session_data: dict):
    candidate = session_data.get("candidate_name", "Candidate")
    role = session_data.get("role", "Engineer")
    level = session_data.get("level", "mid")
    answers = session_data.get("answers", [])
    answers_count = len(answers)
    started_at = session_data.get("started_at", "")

    # Build answer summaries for the agent
    answer_summaries = []
    ai_scores = []
    layer2_results = []

    for i, ans in enumerate(answers, 1):
        det = ans.get("ai_detection", {})
        ana = ans.get("analysis", {})
        voice = ans.get("voice_signals", {})
        layer2 = ans.get("layer2_result")

        ai_score = det.get("final_score", det.get("ai_likelihood_score", 50))
        ai_scores.append(ai_score)

        summary = f"""
Answer {i} (at {ans.get('timestamp', '')[:19].replace('T', ' ')}):
  Question: {ans.get('question', '')[:100]}
  AI Score: {ai_score}/100 | Verdict: {det.get('verdict', 'unknown')}
  Red Flags: {det.get('red_flags_found', 0)}/7
  Technical Depth: {ana.get('technical_depth', 5)}/10
  Specificity: {ana.get('specificity', 5)}/10
  Response Time: {voice.get('response_time', 0):.1f}s
  WPM: {voice.get('wpm', 0)} | Hesitations: {voice.get('hesitations', 0)}
  Reading Signal: {voice.get('reading_signal', False)}
  Layer 2: {layer2.get('gap_type', 'not tested') if layer2 else 'not tested'}
  Layer 2 Conclusion: {layer2.get('conclusion', '') if layer2 else ''}"""
        answer_summaries.append(summary)

        if layer2:
            layer2_results.append(layer2)

    avg_ai = round(sum(ai_scores) / len(ai_scores)) if ai_scores else 0
    high_ai_count = sum(1 for s in ai_scores if s >= 60)
    ai_gaps = sum(1 for r in layer2_results if r.get("gap_type") == "AI_GAP")
    knowledge_gaps = sum(1 for r in layer2_results if r.get("gap_type") == "KNOWLEDGE_GAP")

    return Task(
        description=f"""Generate a complete, HR-friendly interview report. Write in plain English that anyone can understand.

CANDIDATE: {candidate}
ROLE: {role} ({level})
INTERVIEW DATE: {started_at[:10] if started_at else 'today'}
TOTAL ANSWERS: {answers_count}
AVERAGE AI SCORE: {avg_ai}/100
HIGH AI SUSPICION ANSWERS: {high_ai_count} out of {answers_count}
AI GAPS IN DEEP TESTING: {ai_gaps}
KNOWLEDGE GAPS IN DEEP TESTING: {knowledge_gaps}

ANSWER DATA:
{''.join(answer_summaries)}

Write the report in this EXACT format:

VERDICT: HIRE or MAYBE or NO_HIRE
CONFIDENCE: X% (how confident you are in this verdict)

EXECUTIVE_SUMMARY: Write 3 sentences. First sentence: overall impression. Second sentence: biggest concern. Third sentence: recommendation action. Use simple words, no jargon.

AI_VERDICT: CLEAN or SUSPICIOUS or CONFIRMED_AI_USE
AI_EXPLANATION: One paragraph explaining what AI patterns were found and what it means. Write as if explaining to an HR manager who has never heard of AI detection.

STRENGTHS:
- strength one in plain English
- strength two in plain English
- strength three in plain English

CONCERNS:
- concern one in plain English
- concern two in plain English
- concern three in plain English

KNOWLEDGE_MAP:
KNOWS_WELL: topics they demonstrated real knowledge of
SURFACE_ONLY: topics they answered but failed deep follow-up
GAPS: topics they clearly don't know

BEHAVIORAL_SIGNALS: One paragraph about voice patterns, response times, reading signals. Plain English for HR.

FINAL_NOTE: One sentence final recommendation for the hiring manager.""",
        expected_output="Complete HR-friendly interview report with all sections filled.",
        agent=agent,
    )
