from crewai import Crew, Process
from agents.planner import planner_agent
from agents.question_generator import question_generator_agent
from agents.answer_analyzer import answer_analyzer_agent
from agents.ai_detector import ai_detector_agent
from agents.domain_expert import domain_expert_agent
from agents.adaptive_questioner import adaptive_questioner_agent
from agents.report_generator import report_generator_agent
from tasks.interview_tasks import (
    create_plan_task,
    create_questions_task,
    create_analyze_answer_task,
    create_ai_detection_task,
    create_domain_validation_task,
    create_followup_task,
    create_report_task,
)

def run_interview_planning(role: str, level: str) -> dict:
    planner = planner_agent()
    generator = question_generator_agent()

    plan_task = create_plan_task(planner, role, level)
    questions_task = create_questions_task(generator, role, level, "{{plan_task.output}}")

    crew = Crew(
        agents=[planner, generator],
        tasks=[plan_task, questions_task],
        process=Process.sequential,
        verbose=True,
    )
    result = crew.kickoff()
    return {"plan": plan_task.output, "questions": questions_task.output, "raw": str(result)}


def run_answer_analysis(question: str, answer: str) -> dict:
    analyzer = answer_analyzer_agent()
    detector = ai_detector_agent()
    expert = domain_expert_agent()
    questioner = adaptive_questioner_agent()

    analyze_task = create_analyze_answer_task(analyzer, question, answer)
    detect_task = create_ai_detection_task(detector, answer)
    validate_task = create_domain_validation_task(expert, question, answer)
    followup_task = create_followup_task(questioner, question, answer, "{{analyze_task.output}}")

    crew = Crew(
        agents=[analyzer, detector, expert, questioner],
        tasks=[analyze_task, detect_task, validate_task, followup_task],
        process=Process.sequential,
        verbose=True,
    )
    result = crew.kickoff()
    return {
        "analysis": analyze_task.output,
        "ai_detection": detect_task.output,
        "domain_validation": validate_task.output,
        "followup_questions": followup_task.output,
        "raw": str(result),
    }


def run_report_generation(session_data: dict) -> dict:
    reporter = report_generator_agent()
    report_task = create_report_task(reporter, session_data)

    crew = Crew(
        agents=[reporter],
        tasks=[report_task],
        process=Process.sequential,
        verbose=True,
    )
    result = crew.kickoff()
    return {"report": report_task.output, "raw": str(result)}
