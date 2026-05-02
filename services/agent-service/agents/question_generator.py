import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', 'interview-service'))
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from crewai import Agent, LLM

llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

def question_generator_agent():
    return Agent(
        role="Question Generator",
        goal="Generate targeted technical interview questions for DevOps, Cloud, and SRE roles",
        backstory=(
            "You are a principal engineer who has conducted 500+ technical interviews. "
            "You craft questions that reveal true understanding, not memorized answers. "
            "You focus on real-world scenarios, trade-offs, and hands-on experience."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
