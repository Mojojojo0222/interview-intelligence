from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid, time, json, os, sys, asyncio, tempfile
from datetime import datetime

base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base, '..', 'agent-service'))
sys.path.insert(0, os.path.join(base, '..', 'audio-service'))

from crew import run_interview_planning, run_answer_analysis, run_report_generation, get_system_learning_stats
from tools.experience_memory import store_feedback
from alerts import alert_manager, build_alert
from config import CORS_ORIGINS, IS_PRODUCTION

app = FastAPI(title="AI Interview Intelligence System", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

sessions: dict = {}

# Load learned config for dynamic thresholds
def get_learned_config():
    config_path = os.path.join(base, '..', 'agent-service', 'learned_config.json')
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)
    return {"ai_detection_threshold": 60, "version": 0}


# ── Models ─────────────────────────────────────────────────────────────────────

class StartRequest(BaseModel):
    candidate_name: str
    role: str
    level: str

class AnswerRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    response_time_seconds: float = 0
    hesitation_count: int = 0
    filler_count: int = 0
    words_per_minute: float = 0
    reading_signal: bool = False

class Layer2Request(BaseModel):
    session_id: str
    experience_id: str
    followup_question: str
    followup_answer: str
    response_time_seconds: float = 0

class FeedbackRequest(BaseModel):
    experience_id: str
    correct_label: str
    notes: str = ""

class ReportRequest(BaseModel):
    session_id: str


# ── WebSocket — Interviewer Private Channel ────────────────────────────────────

@app.websocket("/ws/interviewer/{session_id}")
async def interviewer_ws(websocket: WebSocket, session_id: str):
    """Private WebSocket for interviewer alerts. Candidate never connects here."""
    await alert_manager.connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        alert_manager.disconnect(session_id)


# ── Core Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    config = get_learned_config()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": config.get("version", 0),
        "ai_threshold": config.get("ai_detection_threshold", 60),
    }


@app.get("/learning")
def learning():
    stats = get_system_learning_stats()
    config = get_learned_config()
    return {**stats, "config": config}


@app.post("/interview/start")
async def start_interview(req: StartRequest):
    session_id = str(uuid.uuid4())
    t0 = time.time()
    result = await asyncio.get_event_loop().run_in_executor(
        None, run_interview_planning, req.role, req.level
    )
    elapsed = round((time.time() - t0) * 1000)
    sessions[session_id] = {
        "session_id": session_id,
        "candidate_name": req.candidate_name,
        "role": req.role,
        "level": req.level,
        "started_at": datetime.utcnow().isoformat(),
        "plan": result.get("plan"),
        "questions": result.get("questions"),
        "answers": [],
        "alerts_sent": [],
        "timing_ms": {"planning": elapsed},
    }
    return {
        "session_id": session_id,
        "questions": result.get("questions"),
        "plan": result.get("plan"),
    }


@app.post("/interview/answer")
async def submit_answer(req: AnswerRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    config = get_learned_config()
    threshold = config.get("ai_detection_threshold", 60)

    t0 = time.time()
    result = await asyncio.get_event_loop().run_in_executor(
        None, run_answer_analysis, req.question, req.answer
    )
    elapsed = round((time.time() - t0) * 1000)

    detection = result.get("ai_detection", {})
    analysis = result.get("analysis", {})
    ai_score = detection.get("ai_likelihood_score", 50)
    verdict = detection.get("verdict", "possibly_ai")

    # Voice signals boost AI score
    voice_boost = 0
    if req.reading_signal:
        voice_boost += 20
    if req.words_per_minute > 160 and req.hesitation_count == 0:
        voice_boost += 15
    if req.response_time_seconds < 5 and req.words_per_minute > 0:
        voice_boost += 10

    final_ai_score = min(ai_score + voice_boost, 100)

    # Two-layer scoring
    surface_score = round((
        analysis.get("technical_depth", 5) +
        analysis.get("specificity", 5) +
        analysis.get("clarity", 5)
    ) / 3, 1)

    # Determine alert type
    alerts_to_send = []

    if final_ai_score >= threshold:
        alerts_to_send.append(build_alert("SCRIPTED_ANSWER", {
            "message": f"AI-assisted answer detected (score: {final_ai_score}/100)",
            "ai_score": final_ai_score,
            "verdict": verdict,
            "suggestion": "Ask a very specific follow-up about their personal experience",
        }))

    if req.reading_signal or (req.words_per_minute > 160 and req.hesitation_count == 0):
        alerts_to_send.append(build_alert("VOICE_SIGNAL", {
            "message": "Candidate appears to be reading from another screen",
            "wpm": req.words_per_minute,
            "hesitations": req.hesitation_count,
        }))

    domain = result.get("domain_validation", {})
    if domain.get("accuracy_score", 10) < 5:
        alerts_to_send.append(build_alert("KNOWLEDGE_GAP", {
            "message": "Technical accuracy issues detected",
            "incorrect": domain.get("incorrect", ""),
        }))

    # Always send deep question suggestion
    followups = result.get("followup_questions", "")
    alerts_to_send.append(build_alert("DEEP_QUESTION", {
        "message": "Suggested follow-up to test genuine knowledge",
        "followup_questions": followups,
        "why": "These questions require real experience to answer well",
    }))

    # Push all alerts to interviewer via WebSocket
    for alert in alerts_to_send:
        await alert_manager.send_alert(req.session_id, alert)
        session["alerts_sent"].append(alert)

    answer_record = {
        "question": req.question,
        "answer": req.answer,
        "experience_id": result.get("experience_id"),
        "analysis": analysis,
        "ai_detection": {**detection, "final_score": final_ai_score, "voice_boost": voice_boost},
        "domain_validation": domain,
        "followup_questions": followups,
        "voice_signals": {
            "response_time": req.response_time_seconds,
            "hesitations": req.hesitation_count,
            "fillers": req.filler_count,
            "wpm": req.words_per_minute,
            "reading_signal": req.reading_signal,
        },
        "surface_score": surface_score,
        "layer2_result": None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    session["answers"].append(answer_record)
    session["timing_ms"][f"answer_{len(session['answers'])}"] = elapsed

    return {
        "experience_id": result.get("experience_id"),
        "ai_score": final_ai_score,
        "verdict": verdict,
        "voice_boost": voice_boost,
        "analysis": analysis,
        "domain_validation": domain,
        "followup_questions": followups,
        "surface_score": surface_score,
        "past_similar_cases": result.get("past_similar_cases", 0),
        "alerts_sent": len(alerts_to_send),
    }


@app.post("/interview/layer2")
async def submit_layer2(req: Layer2Request):
    """
    Layer 2 — candidate answered the deep follow-up.
    Did they pass or fail? This reveals knowledge gap vs AI gap.
    """
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    t0 = time.time()
    result = await asyncio.get_event_loop().run_in_executor(
        None, run_answer_analysis, req.followup_question, req.followup_answer
    )
    elapsed = round((time.time() - t0) * 1000)

    analysis = result.get("analysis", {})
    ai_score = result.get("ai_detection", {}).get("ai_likelihood_score", 50)
    depth = analysis.get("technical_depth", 5)

    # Layer 2 decision
    if depth < 4 and ai_score < 50:
        gap_type = "KNOWLEDGE_GAP"
        conclusion = "Candidate failed deep follow-up with a genuine answer — real knowledge gap"
    elif ai_score >= 60:
        gap_type = "AI_GAP"
        conclusion = "Candidate used AI again on follow-up — confirmed AI dependency"
    elif depth >= 7:
        gap_type = "PASSED"
        conclusion = "Candidate passed deep follow-up — surface answer was genuine"
    else:
        gap_type = "PARTIAL"
        conclusion = "Partial knowledge — knows basics but lacks depth"

    # Alert interviewer
    if gap_type in ["KNOWLEDGE_GAP", "AI_GAP"]:
        await alert_manager.send_alert(req.session_id, build_alert("LAYER2_FAIL", {
            "message": conclusion,
            "gap_type": gap_type,
            "depth_score": depth,
            "ai_score": ai_score,
        }))

    # Update the answer record
    for ans in session["answers"]:
        if ans.get("experience_id") == req.experience_id:
            ans["layer2_result"] = {
                "gap_type": gap_type,
                "conclusion": conclusion,
                "depth_score": depth,
                "ai_score": ai_score,
            }
            break

    return {
        "gap_type": gap_type,
        "conclusion": conclusion,
        "depth_score": depth,
        "ai_score": ai_score,
    }


@app.post("/interview/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio file using Whisper."""
    try:
        from transcriber import transcribe_file, analyze_voice
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(await audio.read())
            tmp_path = f.name
        transcript = transcribe_file(tmp_path)
        os.unlink(tmp_path)
        return {"transcript": transcript, "success": True}
    except Exception as e:
        return {"transcript": "", "success": False, "error": str(e)}


@app.post("/interview/report")
async def generate_report(req: ReportRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session["answers"]:
        raise HTTPException(status_code=400, detail="No answers submitted yet")

    t0 = time.time()
    result = await asyncio.get_event_loop().run_in_executor(
        None, run_report_generation, session
    )
    elapsed = round((time.time() - t0) * 1000)

    report = result.get("report", {})

    # Enrich report with layer2 results
    layer2_summary = []
    for ans in session["answers"]:
        if ans.get("layer2_result"):
            layer2_summary.append(ans["layer2_result"])

    if layer2_summary:
        ai_gaps = sum(1 for r in layer2_summary if r["gap_type"] == "AI_GAP")
        knowledge_gaps = sum(1 for r in layer2_summary if r["gap_type"] == "KNOWLEDGE_GAP")
        report["layer2_summary"] = {
            "ai_gaps": ai_gaps,
            "knowledge_gaps": knowledge_gaps,
            "total_followups": len(layer2_summary),
        }
        if ai_gaps >= 2:
            report["recommendation"] = "NO_HIRE"
            report["ai_note"] = f"Failed {ai_gaps} deep follow-ups with AI-assisted answers"

    session["report"] = report
    session["completed_at"] = datetime.utcnow().isoformat()
    session["timing_ms"]["report"] = elapsed

    await alert_manager.send_alert(req.session_id, build_alert("REPORT_READY", {
        "message": "Interview complete. Report generated.",
        "recommendation": report.get("recommendation", "MAYBE"),
    }))

    return {"session_id": req.session_id, "report": report}


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    success = store_feedback(req.experience_id, req.correct_label, req.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Experience not found")
    return {
        "message": f"Feedback recorded. System learned this was '{req.correct_label}'.",
        "experience_id": req.experience_id,
    }


@app.get("/interview/session/{session_id}")
def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/metrics")
def metrics():
    config = get_learned_config()
    return {
        "total_sessions": len(sessions),
        "completed": sum(1 for s in sessions.values() if s.get("report")),
        "total_answers": sum(len(s.get("answers", [])) for s in sessions.values()),
        "model_version": config.get("version", 0),
        "accuracy_history": config.get("accuracy_history", []),
    }
