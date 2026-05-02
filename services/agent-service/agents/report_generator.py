import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', 'interview-service'))
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from crewai import Agent, LLM

llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

def report_generator_agent():
    return Agent(
        role="Interview Report Generator",
        goal="Generate a comprehensive interview report with scores, AI detection flags, and hiring recommendation",
        backstory=(
            "You are a senior HR analyst who compiles all interview signals into a clear, "
            "structured report. You summarize technical scores, AI usage likelihood, "
            "knowledge gaps, strengths, and provide a final hire/no-hire recommendation "
            "with detailed justification."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
