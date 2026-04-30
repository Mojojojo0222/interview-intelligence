import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'agent-service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'interview-service'))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from tools.text_analyzer import analyze_text_patterns


def test_text_analyzer_detects_ai_patterns():
    ai_text = (
        "Furthermore, it is important to note that Kubernetes provides a robust orchestration "
        "platform. Additionally, the system leverages multiple components. Moreover, the architecture "
        "ensures high availability. Consequently, deployments are streamlined. Therefore, teams benefit."
    )
    result = analyze_text_patterns(ai_text)
    assert result["pattern_score"] >= 20
    assert result["high_formal_transitions"] is True


def test_text_analyzer_human_patterns():
    human_text = "I actually set this up at my last job. We basically had like 3 nodes and honestly it was kind of a mess at first."
    result = analyze_text_patterns(human_text)
    assert result["first_person_count"] >= 2
    assert result["filler_words"] >= 2
    assert result["pattern_score"] < 60


def test_health_endpoint():
    with patch("main.run_interview_planning"), patch("main.run_answer_analysis"), patch("main.run_report_generation"):
        from main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_session_not_found():
    with patch("main.run_interview_planning"), patch("main.run_answer_analysis"), patch("main.run_report_generation"):
        from main import app
        client = TestClient(app)
        response = client.get("/interview/session/nonexistent-id")
        assert response.status_code == 404
