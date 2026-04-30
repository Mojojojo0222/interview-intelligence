from crewai import Crew, Process
from agents.planner import planner_agent
from agents.question_generator import question_generator_agent
from agents.answer_analyzer import answer_analyzer_agent
from agents.ai_detector import ai_detector_agent
from agents.domain_expert import domain_expert_agent
from agents.adaptive_questioner import adaptive_questioner_agent
from agents.report_generator import report_generator_agent
from tasks.interview_tasks import (
    create_plan_task, create_questions_task,
    create_analyze_answer_task, create_ai_detection_task,
    create_domain_validation_task, create_followup_task, create_report_task,
)
import re

def _parse_scores(text: str) -> dict:
    """Extract key: value pairs from plain text LLM output."""
    result = {}
    if not text:
        return result
    text = str(text)
    patterns = {
        "technical_depth":    r"technical_depth[:\s]+(\d+)",
        "specificity":        r"specificity[:\s]+(\d+)",
        "clarity":            r"clarity[:\s]+(\d+)",
        "authenticity":       r"authenticity[:\s]+(\d+)",
        "reasoning":          r"reasoning[:\s]+(.+)",
        "ai_likelihood_score":r"ai_likelihood_score[:\s]+(\d+)",
        "verdict":            r"verdict[:\s]+(likely_human|possibly_ai|likely_ai)",
        "reason":             r"reason[:\s]+(.+)",
        "accuracy_score":     r"accuracy_score[:\s]+(\d+)",
        "correct":            r"correct[:\s]+(.+)",
        "incorrect":          r"incorrect[:\s]+(.+)",
        "recommendation":     r"recommendation[:\s]+(HIRE|MAYBE|NO_HIRE)",
        "summary":            r"summary[:\s]+(.+)",
        "ai_usage":           r"ai_usage[:\s]+(low|medium|high)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            result[key] = int(val) if val.isdigit() else val
    return result


def run_interview_planning(role: str, level: str) -> dict:
    planner = planner_agent()
    generator = question_generator_agent()

    plan_task = create_plan_task(planner, role, level)
    questions_task = create_questions_task(generator, role, level, "the plan above")

    crew = Crew(
        agents=[planner, generator],
        tasks=[plan_task, questions_task],
        process=Process.sequential,
        verbose=False,
    )
    crew.kickoff()
    return {
        "plan": str(plan_task.output),
        "questions": str(questions_task.output),
    }


def run_answer_analysis(question: str, answer: str) -> dict:
    analyzer = answer_analyzer_agent()
    detector = ai_detector_agent()
    expert = domain_expert_agent()
    questioner = adaptive_questioner_agent()

    analyze_task = create_analyze_answer_task(analyzer, question, answer)
    detect_task = create_ai_detection_task(detector, answer)
    validate_task = create_domain_validation_task(expert, question, answer)
    followup_task = create_followup_task(questioner, question, answer, "see analysis above")

    crew = Crew(
        agents=[analyzer, detector, expert, questioner],
        tasks=[analyze_task, detect_task, validate_task, followup_task],
        process=Process.sequential,
        verbose=False,
    )
    crew.kickoff()

    analysis_text = str(analyze_task.output)
    detection_text = str(detect_task.output)
    validation_text = str(validate_task.output)

    analysis = _parse_scores(analysis_text)
    detection = _parse_scores(detection_text)
    validation = _parse_scores(validation_text)

    # Fallback defaults so UI never shows 0
    if not analysis.get("technical_depth"):
        analysis = {"technical_depth": 5, "specificity": 5, "clarity": 5, "authenticity": 5, "reasoning": analysis_text[:200]}
    if not detection.get("ai_likelihood_score"):
        detection = {"ai_likelihood_score": 50, "verdict": "possibly_ai", "reason": detection_text[:200]}
    if not validation.get("accuracy_score"):
        validation = {"accuracy_score": 5, "correct": validation_text[:100], "incorrect": "none"}

    return {
        "analysis": analysis,
        "ai_detection": detection,
        "domain_validation": validation,
        "followup_questions": str(followup_task.output),
    }


def run_report_generation(session_data: dict) -> dict:
    reporter = report_generator_agent()
    report_task = create_report_task(reporter, session_data)

    crew = Crew(
        agents=[reporter],
        tasks=[report_task],
        process=Process.sequential,
        verbose=False,
    )
    crew.kickoff()

    report_text = str(report_task.output)
    report = _parse_scores(report_text)
    report["raw"] = report_text

    if not report.get("recommendation"):
        report["recommendation"] = "MAYBE"
    return {"report": report}
