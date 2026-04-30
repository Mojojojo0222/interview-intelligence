from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import time
from datetime import datetime
import sys, os
# Works regardless of which directory uvicorn is launched from
base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base, '..', 'agent-service'))
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


@app.get("/metrics")
def metrics():
    total = len(sessions)
    completed = sum(1 for s in sessions.values() if s.get("report"))
    total_answers = sum(len(s.get("answers", [])) for s in sessions.values())
    avg_ai_score = 0
    ai_scores = []
    for s in sessions.values():
        for a in s.get("answers", []):
            det = a.get("ai_detection")
            if isinstance(det, dict) and det.get("ai_likelihood_score") is not None:
                ai_scores.append(det["ai_likelihood_score"])
    if ai_scores:
        avg_ai_score = round(sum(ai_scores) / len(ai_scores), 1)
    return {
        "total_sessions": total,
        "completed_interviews": completed,
        "total_answers_analyzed": total_answers,
        "average_ai_likelihood_score": avg_ai_score,
        "sessions": [
            {
                "id": s["session_id"][:8],
                "candidate": s["candidate_name"],
                "role": s["role"],
                "answers_count": len(s.get("answers", [])),
                "timing_ms": s.get("timing_ms", {}),
                "completed": bool(s.get("report")),
            }
            for s in sessions.values()
        ]
    }


@app.post("/interview/start")
async def start_interview(req: StartInterviewRequest):
    import asyncio
    loop = asyncio.get_event_loop()
    session_id = str(uuid.uuid4())
    t0 = time.time()
    result = await loop.run_in_executor(None, run_interview_planning, req.role, req.level)
    elapsed = round((time.time() - t0) * 1000)

    sessions[session_id] = {
        "timing_ms": {"planning": elapsed},
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
async def submit_answer(req: SubmitAnswerRequest):
    import asyncio
    loop = asyncio.get_event_loop()
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    t0 = time.time()
    result = await loop.run_in_executor(None, run_answer_analysis, req.question, req.answer)
    elapsed = round((time.time() - t0) * 1000)
    session.setdefault("timing_ms", {})[f"answer_{len(session['answers'])+1}"] = elapsed

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
async def generate_report(req: GenerateReportRequest):
    import asyncio
    loop = asyncio.get_event_loop()
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session["answers"]:
        raise HTTPException(status_code=400, detail="No answers submitted yet")

    t0 = time.time()
    result = await loop.run_in_executor(None, run_report_generation, session)
    elapsed = round((time.time() - t0) * 1000)
    session.setdefault("timing_ms", {})["report"] = elapsed
    session["report"] = result.get("report")
    session["completed_at"] = datetime.utcnow().isoformat()

    return {"session_id": req.session_id, "report": result.get("report")}


@app.get("/interview/session/{session_id}")
def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
