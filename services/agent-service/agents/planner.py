import os
from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.2:3b", base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

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
