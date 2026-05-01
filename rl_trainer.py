"""
Nightly RL Trainer — runs automatically, learns from all confirmed feedback.
Schedule this to run every night:
  Windows Task Scheduler: python rl_trainer.py
  Or add to docker-compose as a cron job.

What it does:
1. Pulls all confirmed experiences from ChromaDB
2. Finds patterns where detection was WRONG
3. Updates the detection thresholds based on real data
4. Saves improved config for agents to use next day
"""
import sys
import os
import json
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'services', 'agent-service'))
from tools.experience_memory import _get_collection, get_learning_stats

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'services', 'agent-service', 'learned_config.json')


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "ai_detection_threshold": 60,
        "red_flag_weight": 10,
        "voice_reading_boost": 20,
        "high_wpm_boost": 15,
        "version": 0,
        "last_trained": None,
        "total_samples_trained_on": 0,
        "accuracy_history": [],
    }


def save_config(config: dict):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def run_training():
    print(f"\n{'='*50}")
    print(f"  RL Trainer starting — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")

    config = load_config()
    col = _get_collection("answer_experiences")
    total = col.count()

    if total == 0:
        print("  No experiences yet. Run some interviews first.")
        return

    # Pull all confirmed samples
    all_data = col.get(include=["metadatas"])
    confirmed = [m for m in all_data["metadatas"] if m.get("confirmed_label") in ["ai", "human"]]

    if len(confirmed) < 5:
        print(f"  Only {len(confirmed)} confirmed samples. Need at least 5 to train.")
        print("  Use POST /feedback to confirm more detections.")
        return

    print(f"  Total experiences: {total}")
    print(f"  Confirmed samples: {len(confirmed)}")

    # Analyze where current threshold gets it wrong
    threshold = config["ai_detection_threshold"]
    correct = 0
    false_positives = []  # Said AI, was Human
    false_negatives = []  # Said Human, was AI

    for m in confirmed:
        label = m["confirmed_label"]
        score = m.get("ai_score", 50)
        predicted = "ai" if score >= threshold else "human"

        if predicted == label:
            correct += 1
        elif predicted == "ai" and label == "human":
            false_positives.append(score)
        elif predicted == "human" and label == "ai":
            false_negatives.append(score)

    accuracy = round(correct / len(confirmed) * 100, 1)
    print(f"\n  Current accuracy: {accuracy}%")
    print(f"  False positives (said AI, was Human): {len(false_positives)}")
    print(f"  False negatives (said Human, was AI): {len(false_negatives)}")

    # Adjust threshold based on errors
    new_threshold = threshold
    if len(false_positives) > len(false_negatives) * 1.5:
        # Too many false positives — raise threshold
        new_threshold = min(threshold + 5, 80)
        print(f"  Too many false positives — raising threshold: {threshold} -> {new_threshold}")
    elif len(false_negatives) > len(false_positives) * 1.5:
        # Missing too many AI answers — lower threshold
        new_threshold = max(threshold - 5, 40)
        print(f"  Missing AI answers — lowering threshold: {threshold} -> {new_threshold}")
    else:
        print(f"  Threshold balanced at {threshold}")

    # Analyze red flag patterns
    ai_samples = [m for m in confirmed if m["confirmed_label"] == "ai"]
    human_samples = [m for m in confirmed if m["confirmed_label"] == "human"]

    avg_ai_flags = sum(m.get("red_flags", 0) for m in ai_samples) / max(len(ai_samples), 1)
    avg_human_flags = sum(m.get("red_flags", 0) for m in human_samples) / max(len(human_samples), 1)

    print(f"\n  Avg red flags in AI answers: {avg_ai_flags:.1f}")
    print(f"  Avg red flags in Human answers: {avg_human_flags:.1f}")

    # Update red flag weight based on how discriminative they are
    discrimination = avg_ai_flags - avg_human_flags
    if discrimination > 3:
        new_red_flag_weight = min(config["red_flag_weight"] + 2, 20)
    elif discrimination < 1:
        new_red_flag_weight = max(config["red_flag_weight"] - 2, 5)
    else:
        new_red_flag_weight = config["red_flag_weight"]

    # Calculate new accuracy with updated threshold
    new_correct = sum(
        1 for m in confirmed
        if (m.get("ai_score", 50) >= new_threshold) == (m["confirmed_label"] == "ai")
    )
    new_accuracy = round(new_correct / len(confirmed) * 100, 1)

    # Save updated config
    config["ai_detection_threshold"] = new_threshold
    config["red_flag_weight"] = new_red_flag_weight
    config["version"] += 1
    config["last_trained"] = datetime.now().isoformat()
    config["total_samples_trained_on"] = len(confirmed)
    config["accuracy_history"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "accuracy": new_accuracy,
        "samples": len(confirmed),
        "threshold": new_threshold,
    })
    # Keep last 30 days of history
    config["accuracy_history"] = config["accuracy_history"][-30:]

    save_config(config)

    print(f"\n  New accuracy with updated config: {new_accuracy}%")
    print(f"  Config version: {config['version']}")
    print(f"  Saved to: {CONFIG_PATH}")
    print(f"\n  System will use new config on next interview.")
    print(f"{'='*50}\n")

    return {
        "accuracy_before": accuracy,
        "accuracy_after": new_accuracy,
        "threshold": new_threshold,
        "samples": len(confirmed),
        "version": config["version"],
    }


if __name__ == "__main__":
    result = run_training()
    if result:
        print(f"Training complete. Accuracy: {result['accuracy_before']}% -> {result['accuracy_after']}%")
