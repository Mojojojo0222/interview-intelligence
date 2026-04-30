"""
Local Benchmark Script â€” AI Interview Intelligence System
Run this to test efficiency, response times, and AI detection accuracy.

Usage:
    python benchmark.py

Requirements:
    pip install requests matplotlib
    Ollama must be running: ollama serve
    API must be running: uvicorn main:app --port 8000
"""

import requests
import time
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime

BASE_URL = "http://localhost:8001"

# â”€â”€ Test Data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

HUMAN_ANSWERS = [
    {
        "question": "How do you handle a Kubernetes pod that keeps crashing?",
        "answer": "Honestly the first thing I do is kubectl describe pod to see the events. Last time this happened at my job, it was an OOMKilled â€” we had set memory limits too low. I bumped the limit from 256Mi to 512Mi and it stabilized. Also checked logs with kubectl logs --previous to see what happened before the crash."
    },
    {
        "question": "Explain how you'd set up a CI/CD pipeline for a microservice.",
        "answer": "At my last company we used GitHub Actions. Basically on every PR it ran pytest, then built the Docker image, pushed to ECR. On merge to main it deployed to EKS using kubectl set image. Took us a while to get the rollback working properly â€” we ended up using helm rollback after a bad deploy broke prod."
    },
]

AI_ANSWERS = [
    {
        "question": "How do you handle a Kubernetes pod that keeps crashing?",
        "answer": "To handle a Kubernetes pod that keeps crashing, you should follow these systematic steps. First, use kubectl describe pod to examine the pod's events and status. Furthermore, review the container logs using kubectl logs to identify error messages. Additionally, check resource limits and requests to ensure they are appropriately configured. Moreover, verify that the container image is correct and accessible. Consequently, examine liveness and readiness probes to ensure they are properly defined. Therefore, by following these comprehensive steps, you can effectively diagnose and resolve pod crash issues."
    },
    {
        "question": "What is the difference between blue-green and canary deployments?",
        "answer": "Blue-green and canary deployments are two distinct deployment strategies used in modern software delivery. Blue-green deployment involves maintaining two identical production environments, namely blue and green. Furthermore, traffic is switched entirely from one environment to the other. Additionally, this approach enables zero-downtime deployments and straightforward rollbacks. Canary deployment, on the other hand, involves gradually routing a small percentage of traffic to the new version. Moreover, this strategy allows teams to monitor the new version's performance before full rollout. Consequently, both strategies have their respective advantages and use cases."
    },
]

# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_server():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except:
        return False

def timed_request(method, url, **kwargs):
    t0 = time.time()
    r = getattr(requests, method)(url, **kwargs)
    return r, round((time.time() - t0) * 1000)

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# â”€â”€ Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

results = {
    "planning_time_ms": None,
    "answer_times_ms": [],
    "report_time_ms": None,
    "ai_detection_scores": {"human": [], "ai": []},
    "answer_quality_scores": [],
    "errors": [],
}

def test_health():
    print_section("1. Health Check")
    r, ms = timed_request("get", f"{BASE_URL}/health")
    if r.status_code == 200:
        print(f"  âœ… API is healthy ({ms}ms)")
    else:
        print(f"  âŒ API not responding")
        results["errors"].append("health check failed")

def test_planning():
    print_section("2. Interview Planning (Planner + Question Generator agents)")
    print("  Starting interview session... (this takes 30-90s with llama3.2:3b)")
    r, ms = timed_request("post", f"{BASE_URL}/interview/start", json={
        "candidate_name": "Test Candidate",
        "role": "DevOps Engineer",
        "level": "mid"
    }, timeout=600)

    if r.status_code == 200:
        data = r.json()
        results["planning_time_ms"] = ms
        results["session_id"] = data["session_id"]
        print(f"  âœ… Planning complete in {ms}ms ({ms/1000:.1f}s)")
        print(f"  Session ID: {data['session_id'][:8]}...")
        print(f"  Questions preview: {str(data.get('questions', ''))[:200]}...")
        return True
    else:
        print(f"  âŒ Failed: {r.text[:200]}")
        results["errors"].append(f"planning failed: {r.status_code}")
        return False

def test_human_answers():
    print_section("3. Human Answer Analysis (4 agents running)")
    session_id = results.get("session_id")
    if not session_id:
        print("  âš  Skipped â€” no session")
        return

    for i, qa in enumerate(HUMAN_ANSWERS):
        print(f"\n  Human Answer {i+1}: '{qa['question'][:50]}...'")
        print(f"  Analyzing... (30-120s per answer)")
        r, ms = timed_request("post", f"{BASE_URL}/interview/answer", json={
            "session_id": session_id,
            "question": qa["question"],
            "answer": qa["answer"]
        }, timeout=600)

        if r.status_code == 200:
            data = r.json()
            results["answer_times_ms"].append(ms)

            det = data.get("ai_detection")
            if isinstance(det, dict):
                score = det.get("ai_likelihood_score", 0)
                results["ai_detection_scores"]["human"].append(score)
                verdict = det.get("verdict", "unknown")
                print(f"  âœ… Done in {ms/1000:.1f}s | AI Score: {score}/100 | Verdict: {verdict}")
            else:
                print(f"  âœ… Done in {ms/1000:.1f}s | Detection: {str(det)[:100]}")

            analysis = data.get("analysis")
            if isinstance(analysis, dict):
                scores = {k: analysis.get(k, 0) for k in ["technical_depth", "specificity", "clarity", "authenticity"]}
                results["answer_quality_scores"].append(scores)
                print(f"  Quality: {scores}")
        else:
            print(f"  âŒ Failed: {r.text[:100]}")
            results["errors"].append(f"human answer {i+1} failed")

def test_ai_answers():
    print_section("4. AI-Generated Answer Detection Test")
    session_id = results.get("session_id")
    if not session_id:
        print("  âš  Skipped â€” no session")
        return

    for i, qa in enumerate(AI_ANSWERS):
        print(f"\n  AI Answer {i+1}: '{qa['question'][:50]}...'")
        print(f"  Analyzing...")
        r, ms = timed_request("post", f"{BASE_URL}/interview/answer", json={
            "session_id": session_id,
            "question": qa["question"],
            "answer": qa["answer"]
        }, timeout=600)

        if r.status_code == 200:
            data = r.json()
            det = data.get("ai_detection")
            if isinstance(det, dict):
                score = det.get("ai_likelihood_score", 0)
                results["ai_detection_scores"]["ai"].append(score)
                verdict = det.get("verdict", "unknown")
                flag = "ðŸš¨" if score >= 60 else "âš "
                print(f"  {flag} Done in {ms/1000:.1f}s | AI Score: {score}/100 | Verdict: {verdict}")
            else:
                print(f"  âœ… Done in {ms/1000:.1f}s")
        else:
            print(f"  âŒ Failed: {r.text[:100]}")

def test_report():
    print_section("5. Report Generation")
    session_id = results.get("session_id")
    if not session_id:
        print("  âš  Skipped â€” no session")
        return

    print("  Generating final report...")
    r, ms = timed_request("post", f"{BASE_URL}/interview/report", json={
        "session_id": session_id
    }, timeout=600)

    if r.status_code == 200:
        data = r.json()
        results["report_time_ms"] = ms
        report = data.get("report", {})
        print(f"  âœ… Report generated in {ms/1000:.1f}s")
        if isinstance(report, dict):
            print(f"  Verdict: {report.get('recommendation', 'N/A')}")
            print(f"  Strengths: {report.get('strengths', [])}")
            print(f"  Gaps: {report.get('knowledge_gaps', [])}")
        else:
            print(f"  Report: {str(report)[:300]}")
    else:
        print(f"  âŒ Failed: {r.text[:100]}")
        results["errors"].append("report generation failed")

# â”€â”€ Graphs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def show_graphs():
    print_section("6. Efficiency Graphs")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("AI Interview Intelligence System â€” Local Benchmark", fontsize=14, fontweight="bold")

    # Graph 1: Response Times
    ax1 = axes[0, 0]
    labels, times = [], []
    if results["planning_time_ms"]:
        labels.append("Planning\n(2 agents)")
        times.append(results["planning_time_ms"] / 1000)
    for i, t in enumerate(results["answer_times_ms"]):
        labels.append(f"Answer {i+1}\n(4 agents)")
        times.append(t / 1000)
    if results["report_time_ms"]:
        labels.append("Report\n(1 agent)")
        times.append(results["report_time_ms"] / 1000)

    colors = ["#3b82f6"] + ["#8b5cf6"] * len(results["answer_times_ms"]) + ["#22c55e"]
    if labels:
        bars = ax1.bar(labels, times, color=colors[:len(labels)], edgecolor="white", linewidth=0.5)
        for bar, t in zip(bars, times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"{t:.1f}s", ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax1.set_title("Response Time per Stage", fontweight="bold")
        ax1.set_ylabel("Seconds")
        ax1.set_facecolor("#f8fafc")
        ax1.axhline(y=60, color="orange", linestyle="--", alpha=0.7, label="60s threshold")
        ax1.legend(fontsize=8)

    # Graph 2: AI Detection â€” Human vs AI answers
    ax2 = axes[0, 1]
    human_scores = results["ai_detection_scores"]["human"]
    ai_scores = results["ai_detection_scores"]["ai"]
    all_scores = human_scores + ai_scores
    all_labels = [f"Human {i+1}" for i in range(len(human_scores))] + \
                 [f"AI Gen {i+1}" for i in range(len(ai_scores))]
    bar_colors = ["#22c55e"] * len(human_scores) + ["#ef4444"] * len(ai_scores)

    if all_scores:
        bars = ax2.bar(all_labels, all_scores, color=bar_colors, edgecolor="white")
        for bar, score in zip(bars, all_scores):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    str(score), ha="center", va="bottom", fontsize=10, fontweight="bold")
        ax2.axhline(y=60, color="orange", linestyle="--", alpha=0.8, label="Detection threshold (60)")
        ax2.set_title("AI Detection Scores\n(Higher = More likely AI-generated)", fontweight="bold")
        ax2.set_ylabel("AI Likelihood Score (0-100)")
        ax2.set_ylim(0, 110)
        ax2.set_facecolor("#f8fafc")
        green_patch = mpatches.Patch(color="#22c55e", label="Human answers")
        red_patch = mpatches.Patch(color="#ef4444", label="AI-generated answers")
        ax2.legend(handles=[green_patch, red_patch], fontsize=8)

    # Graph 3: Answer Quality Scores
    ax3 = axes[1, 0]
    if results["answer_quality_scores"]:
        categories = ["technical_depth", "specificity", "clarity", "authenticity"]
        display = ["Depth", "Specificity", "Clarity", "Authenticity"]
        x = range(len(categories))
        width = 0.35
        for i, scores in enumerate(results["answer_quality_scores"]):
            vals = [scores.get(c, 0) for c in categories]
            offset = (i - len(results["answer_quality_scores"])/2 + 0.5) * width
            ax3.bar([xi + offset for xi in x], vals, width, label=f"Answer {i+1}", alpha=0.85)
        ax3.set_title("Answer Quality Scores", fontweight="bold")
        ax3.set_ylabel("Score (0-10)")
        ax3.set_xticks(list(x))
        ax3.set_xticklabels(display)
        ax3.set_ylim(0, 11)
        ax3.set_facecolor("#f8fafc")
        ax3.legend(fontsize=8)
        ax3.axhline(y=7, color="green", linestyle="--", alpha=0.5, label="Good threshold")

    # Graph 4: Summary Stats
    ax4 = axes[1, 1]
    ax4.axis("off")
    total_time = sum(filter(None, [
        results["planning_time_ms"],
        *results["answer_times_ms"],
        results["report_time_ms"]
    ])) / 1000

    human_avg = round(sum(human_scores)/len(human_scores), 1) if human_scores else "N/A"
    ai_avg = round(sum(ai_scores)/len(ai_scores), 1) if ai_scores else "N/A"
    detection_working = "âœ… YES" if (ai_scores and human_scores and
                                     sum(ai_scores)/len(ai_scores) > sum(human_scores)/len(human_scores)) else "âš  CHECK"

    summary = [
        ("Total benchmark time", f"{total_time:.1f}s"),
        ("Answers analyzed", str(len(results["answer_times_ms"]))),
        ("Avg time per answer", f"{sum(results['answer_times_ms'])/len(results['answer_times_ms'])/1000:.1f}s" if results["answer_times_ms"] else "N/A"),
        ("Human avg AI score", str(human_avg)),
        ("AI-gen avg AI score", str(ai_avg)),
        ("Detection working?", detection_working),
        ("Errors", str(len(results["errors"])) if results["errors"] else "None âœ…"),
    ]

    ax4.set_title("Benchmark Summary", fontweight="bold", pad=20)
    y = 0.9
    for label, value in summary:
        color = "#ef4444" if "âŒ" in value or (label == "Errors" and value != "None âœ…") else "#1e293b"
        ax4.text(0.05, y, label, transform=ax4.transAxes, fontsize=11, color="#64748b")
        ax4.text(0.65, y, value, transform=ax4.transAxes, fontsize=11, fontweight="bold", color=color)
        y -= 0.12

    plt.tight_layout()
    filename = f"benchmark_{datetime.now().strftime('%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"  âœ… Graph saved as: {filename}")
    plt.show()

# â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == "__main__":
    print("\nðŸ¤– AI Interview Intelligence System â€” Benchmark")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Target: {BASE_URL}")

    if not check_server():
        print("\nâŒ API server not running!")
        print("\nStart it first:")
        print("  cd services/interview-service")
        print("  uvicorn main:app --reload --port 8000")
        exit(1)

    test_health()
    ok = test_planning()
    if ok:
        test_human_answers()
        test_ai_answers()
        test_report()

    print_section("Results Summary")
    if results["errors"]:
        print(f"  âš  Errors: {results['errors']}")
    else:
        print("  âœ… All tests passed")

    show_graphs()


