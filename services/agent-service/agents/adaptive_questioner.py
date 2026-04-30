import os
from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.2:3b", base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

def adaptive_questioner_agent():
    return Agent(
        role="Adaptive Follow-up Questioner",
        goal="Generate unpredictable follow-up questions that expose gaps and cannot be answered by LLMs",
        backstory=(
            "You specialize in crafting follow-up questions that go beyond textbook answers. "
            "You ask about specific failure scenarios, edge cases, personal decisions made under pressure, "
            "and highly contextual situations tied to the candidate's own stated experience. "
            "Your questions are impossible to answer well without genuine hands-on experience."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
