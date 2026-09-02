"""
QA set loader for evaluation.

Loads held-out QA sets from JSON files in data/qa_sets/.
Format: [{ "question": "...", "ground_truth_answer": "...", "ground_truth_chunk_ids": [...] }]
"""

import json

from app.config import get_settings
from app.models import QAItem


def load_qa_set(name: str = "default") -> list[QAItem]:
    """
    Load a QA evaluation set from a JSON file.

    Args:
        name: Name of the QA set (maps to data/qa_sets/{name}_qa_set.json).

    Returns:
        List of QAItem objects.
    """
    settings = get_settings()
    qa_path = settings.qa_sets_abs_path / f"{name}_qa_set.json"

    if not qa_path.exists():
        raise FileNotFoundError(
            f"QA set not found: {qa_path}. "
            f"Create a JSON file at data/qa_sets/{name}_qa_set.json"
        )

    with open(qa_path, encoding="utf-8") as f:
        data = json.load(f)

    items = []
    for entry in data:
        items.append(
            QAItem(
                question=entry["question"],
                ground_truth_answer=entry["ground_truth_answer"],
                ground_truth_chunk_ids=entry.get("ground_truth_chunk_ids", []),
            )
        )

    print(f"[QALoader] Loaded {len(items)} QA pairs from: {qa_path.name}")
    return items


def list_qa_sets() -> list[str]:
    """List available QA set names."""
    settings = get_settings()
    qa_dir = settings.qa_sets_abs_path

    if not qa_dir.exists():
        return []

    names = []
    for f in qa_dir.glob("*_qa_set.json"):
        name = f.stem.replace("_qa_set", "")
        names.append(name)

    return sorted(names)
