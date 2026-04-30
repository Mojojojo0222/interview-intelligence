from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import json
from datetime import datetime
from crew import run_interview_planning, run_answer_analysis, run_report_generation

app = FastAPI(title="AI Interview Intelligence System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (replace with Redis/RDS in production)
sessions: dict = {}


class StartInterviewRequest(BaseModel):
    candidate_name: str
    role: str  # e.g. "DevOps Engineer", "SRE", "Cloud Engineer"
    level: str  # e.g. "junior", "mid", "senior"

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question: str
    answer: str

class GenerateReportRequest(BaseModel):
    session_id: str


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/interview/start")
def start_interview(req: StartInterviewRequest):
    session_id = str(uuid.uuid4())
    result = run_interview_planning(req.role, req.level)

    sessions[session_id] = {
        "session_id": session_id,
        "candidate_name": req.candidate_name,
        "role": req.role,
        "level": req.level,
        "started_at": datetime.utcnow().isoformat(),
        "plan": result.get("plan"),
        "questions": result.get("questions"),
        "answers": [],
    }
    return {
        "session_id": session_id,
        "plan": result.get("plan"),
        "questions": result.get("questions"),
    }


@app.post("/interview/answer")
def submit_answer(req: SubmitAnswerRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = run_answer_analysis(req.question, req.answer)

    session["answers"].append({
        "question": req.question,
        "answer": req.answer,
        "analysis": result.get("analysis"),
        "ai_detection": result.get("ai_detection"),
        "domain_validation": result.get("domain_validation"),
        "followup_questions": result.get("followup_questions"),
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {
        "analysis": result.get("analysis"),
        "ai_detection": result.get("ai_detection"),
        "domain_validation": result.get("domain_validation"),
        "followup_questions": result.get("followup_questions"),
    }


@app.post("/interview/report")
def generate_report(req: GenerateReportRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session["answers"]:
        raise HTTPException(status_code=400, detail="No answers submitted yet")

    result = run_report_generation(session)
    session["report"] = result.get("report")
    session["completed_at"] = datetime.utcnow().isoformat()

    return {"session_id": req.session_id, "report": result.get("report")}


@app.get("/interview/session/{session_id}")
def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
