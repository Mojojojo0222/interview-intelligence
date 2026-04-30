from crewai import Agent
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.2:3b", base_url="http://ollama:11434")

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
