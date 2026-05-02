import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', 'interview-service'))
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from crewai import Agent, LLM

llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)

def domain_expert_agent():
    return Agent(
        role="DevOps/AWS/SRE Domain Expert",
        goal="Validate technical accuracy of answers related to DevOps, AWS, Kubernetes, and SRE practices",
        backstory=(
            "You are a Staff SRE with deep expertise in AWS (EKS, RDS, CloudWatch, IAM, VPC), "
            "Kubernetes, Terraform, CI/CD pipelines, incident management, and observability. "
            "You fact-check technical claims and identify when a candidate is bluffing or "
            "misunderstanding core concepts."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
