"""
Training data — 5 test cases to seed the experience memory.
Run: python train.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'services', 'agent-service'))
from tools.experience_memory import store_answer_experience

CASES = [
    {
        "question": "How do you handle a Kubernetes pod that keeps crashing?",
        "answer": "I use kubectl describe pod to check events, then kubectl logs --previous to see what happened before the crash. At my last job we had an OOMKilled issue — limits were set to 256Mi, bumped to 512Mi and it stabilized. Took about 20 mins to figure out.",
        "label": "human",
        "ai_score": 8,
        "red_flags": 1,
    },
    {
        "question": "How do you handle a Kubernetes pod that keeps crashing?",
        "answer": "To handle a Kubernetes pod that keeps crashing, you should follow these systematic steps. First, use kubectl describe pod to examine events. Furthermore, review container logs using kubectl logs. Additionally, check resource limits and requests. Moreover, verify liveness and readiness probes. Consequently, by following these comprehensive steps you can resolve pod crashes effectively.",
        "label": "ai",
        "ai_score": 95,
        "red_flags": 6,
    },
    {
        "question": "Explain your experience with Terraform.",
        "answer": "I've been using Terraform since version 0.12. At my previous company we managed about 200 AWS resources across 3 environments. Biggest pain point was state locking — we had two engineers apply at the same time once and it corrupted the state file. After that we enforced S3 backend with DynamoDB locking.",
        "label": "human",
        "ai_score": 5,
        "red_flags": 0,
    },
    {
        "question": "Explain your experience with Terraform.",
        "answer": "Terraform is an infrastructure as code tool that enables teams to define and provision infrastructure using a declarative configuration language. It supports multiple cloud providers and offers features such as state management, module reusability, and plan/apply workflows. Furthermore, it integrates seamlessly with CI/CD pipelines. Additionally, remote state backends ensure collaboration across teams.",
        "label": "ai",
        "ai_score": 92,
        "red_flags": 5,
    },
    {
        "question": "How do you approach incident response?",
        "answer": "First thing I do is check our Grafana dashboards — we had alerts set up for p99 latency above 500ms. One time at 2am we had a database connection pool exhaustion. I jumped on a call with the on-call DBA, we increased max_connections from 100 to 300 as a hotfix, then did a proper fix next morning by adding connection pooling via PgBouncer.",
        "label": "human",
        "ai_score": 6,
        "red_flags": 0,
    },
]

if __name__ == "__main__":
    print("Seeding experience memory with 5 training cases...")
    for i, case in enumerate(CASES, 1):
        exp_id = store_answer_experience(
            question=case["question"],
            answer=case["answer"],
            ai_score=case["ai_score"],
            verdict="likely_ai" if case["ai_score"] > 60 else "likely_human",
            red_flags=case["red_flags"],
            quality_scores={"technical_depth": 7, "specificity": 7, "clarity": 7, "authenticity": 7},
            confirmed_label=case["label"],
        )
        print(f"  [{i}/5] Stored: {case['label'].upper()} | score={case['ai_score']} | id={exp_id[:8]}...")
    print("\nDone! Experience memory seeded.")
    print("Run: python -c \"import sys; sys.path.insert(0, 'services/agent-service'); from tools.experience_memory import get_learning_stats; print(get_learning_stats())\"")
