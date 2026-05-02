import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', 'interview-service'))
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from crewai import Agent, LLM

llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

def planner_agent():
    return Agent(
        role="Interview Planner",
        goal="Create a structured interview plan based on job role and experience level",
        backstory=(
            "You are a senior technical recruiter with 10 years of experience hiring "
            "DevOps, Cloud, and SRE engineers. You know exactly what skills to probe "
            "and how to structure an interview for maximum signal."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
