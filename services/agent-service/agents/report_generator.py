from crewai import Agent
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.2:3b", base_url="http://ollama:11434")

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
