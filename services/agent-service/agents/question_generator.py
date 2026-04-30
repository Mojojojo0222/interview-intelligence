import os
from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.2:3b", base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

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
