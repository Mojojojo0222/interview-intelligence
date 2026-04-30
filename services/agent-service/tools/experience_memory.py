"""
Experience Memory — stores every interview answer + outcome as embeddings.
Agents query this before making decisions to learn from past experience.
"""
import os
import uuid
import json
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "experience_db")

# Use sentence-transformers for local embeddings — no API needed
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

_client = None
_collections = {}

def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=DB_PATH)
    return _client

def _get_collection(name: str):
    if name not in _collections:
        _collections[name] = _get_client().get_or_create_collection(
            name=name,
            embedding_function=_ef,
            metadata={"hnsw:space": "cosine"}
        )
    return _collections[name]


# ── Store Experience ───────────────────────────────────────────────────────────

def store_answer_experience(
    question: str,
    answer: str,
    ai_score: int,
    verdict: str,
    red_flags: int,
    quality_scores: dict,
    confirmed_label: str = "unconfirmed"  # "human", "ai", "unconfirmed"
):
    """Store an analyzed answer as experience for future reference."""
    col = _get_collection("answer_experiences")
    doc_id = str(uuid.uuid4())
    col.add(
        ids=[doc_id],
        documents=[f"Q: {question}\nA: {answer}"],
        metadatas=[{
            "question": question[:500],
            "ai_score": ai_score,
            "verdict": verdict,
            "red_flags": red_flags,
            "quality_avg": sum(quality_scores.values()) / max(len(quality_scores), 1),
            "confirmed_label": confirmed_label,
            "timestamp": datetime.utcnow().isoformat(),
        }]
    )
    return doc_id


def store_feedback(doc_id: str, correct_label: str, notes: str = ""):
    """You provide feedback — was the detection correct? Updates the experience."""
    col = _get_collection("answer_experiences")
    try:
        result = col.get(ids=[doc_id])
        if result["ids"]:
            meta = result["metadatas"][0]
            meta["confirmed_label"] = correct_label
            meta["feedback_notes"] = notes
            meta["feedback_at"] = datetime.utcnow().isoformat()
            col.update(ids=[doc_id], metadatas=[meta])
            return True
    except Exception:
        pass
    return False


# ── Query Experience ───────────────────────────────────────────────────────────

def get_similar_experiences(answer: str, n: int = 3) -> list:
    """
    Find the most similar past answers and what we learned from them.
    Agents use this as few-shot context before making decisions.
    """
    col = _get_collection("answer_experiences")
    count = col.count()
    if count == 0:
        return []

    results = col.query(
        query_texts=[answer],
        n_results=min(n, count),
        include=["documents", "metadatas", "distances"]
    )

    experiences = []
    for i, doc_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        similarity = round((1 - distance) * 100, 1)
        experiences.append({
            "similarity": similarity,
            "ai_score": meta.get("ai_score", 0),
            "verdict": meta.get("verdict", "unknown"),
            "red_flags": meta.get("red_flags", 0),
            "confirmed_label": meta.get("confirmed_label", "unconfirmed"),
            "feedback_notes": meta.get("feedback_notes", ""),
            "quality_avg": round(meta.get("quality_avg", 5), 1),
        })
    return experiences


def get_learning_stats() -> dict:
    """How much has the system learned so far."""
    col = _get_collection("answer_experiences")
    count = col.count()
    if count == 0:
        return {"total_experiences": 0, "confirmed": 0, "accuracy": "no data yet"}

    all_data = col.get(include=["metadatas"])
    confirmed = [m for m in all_data["metadatas"] if m.get("confirmed_label") != "unconfirmed"]
    ai_confirmed = [m for m in confirmed if m.get("confirmed_label") == "ai"]
    human_confirmed = [m for m in confirmed if m.get("confirmed_label") == "human"]

    # Calculate detection accuracy on confirmed samples
    correct = 0
    for m in confirmed:
        label = m.get("confirmed_label")
        score = m.get("ai_score", 50)
        predicted = "ai" if score >= 60 else "human"
        if predicted == label:
            correct += 1

    accuracy = round(correct / len(confirmed) * 100, 1) if confirmed else 0

    return {
        "total_experiences": count,
        "confirmed": len(confirmed),
        "ai_samples": len(ai_confirmed),
        "human_samples": len(human_confirmed),
        "detection_accuracy": f"{accuracy}%",
        "unconfirmed": count - len(confirmed),
    }
