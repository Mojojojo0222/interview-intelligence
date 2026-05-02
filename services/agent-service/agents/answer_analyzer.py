import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', 'interview-service'))
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from crewai import Agent, LLM

llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

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
