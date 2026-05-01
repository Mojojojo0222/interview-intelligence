"""
Real-time alert system — pushes instant alerts to interviewer
via WebSocket while candidate is answering.
Candidate has zero visibility into this.
"""
from fastapi import WebSocket
from typing import Dict
import json
import asyncio


class AlertManager:
    def __init__(self):
        # session_id -> interviewer WebSocket
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)

    async def send_alert(self, session_id: str, alert: dict):
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_text(json.dumps(alert))
            except Exception:
                self.disconnect(session_id)

    async def broadcast_to_all(self, alert: dict):
        for session_id in list(self._connections.keys()):
            await self.send_alert(session_id, alert)


# Singleton
alert_manager = AlertManager()


def build_alert(alert_type: str, data: dict) -> dict:
    """
    Alert types:
    - SCRIPTED_ANSWER   : AI detection triggered
    - KNOWLEDGE_GAP     : Domain expert found gaps
    - DEEP_QUESTION     : Suggest follow-up question
    - VOICE_SIGNAL      : Reading from screen detected
    - LAYER2_FAIL       : Failed deep follow-up = confirmed gap
    - REPORT_READY      : Final report generated
    """
    icons = {
        "SCRIPTED_ANSWER": "warning",
        "KNOWLEDGE_GAP":   "gap",
        "DEEP_QUESTION":   "question",
        "VOICE_SIGNAL":    "voice",
        "LAYER2_FAIL":     "critical",
        "REPORT_READY":    "report",
    }
    severity = {
        "SCRIPTED_ANSWER": "high",
        "KNOWLEDGE_GAP":   "medium",
        "DEEP_QUESTION":   "info",
        "VOICE_SIGNAL":    "high",
        "LAYER2_FAIL":     "critical",
        "REPORT_READY":    "info",
    }
    return {
        "type": alert_type,
        "icon": icons.get(alert_type, "info"),
        "severity": severity.get(alert_type, "info"),
        **data
    }
