import os
from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.2:3b", base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

def answer_analyzer_agent():
    return Agent(
        role="Answer Analyzer",
        goal="Analyze candidate answers for depth, specificity, and real-world experience signals",
        backstory=(
            "You are an expert at evaluating technical answers. You look for concrete examples, "
            "specific numbers, personal experience markers, and signs of genuine understanding "
            "vs surface-level knowledge. You score answers on depth, accuracy, and authenticity."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
