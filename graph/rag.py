import json
import os
from typing import List, Optional
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config import DATA_PATH

_model: Optional[SentenceTransformer] = None
_index: Optional[faiss.IndexFlatL2] = None
_students: List[dict] = []


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def _student_to_text(s: dict) -> str:
    return (
        f"Học sinh: {s['name']}, ID: {s['student_id']}, "
        f"Lớp: {s['class_name']}, Trường: {s['school']}, "
        f"Điểm quá trình: {s['process_score']}, Điểm cuối kỳ: {s['final_score']}, "
        f"Chuyên cần: {s['attendance']}"
    )


def build_index():
    global _index, _students
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        _students = json.load(f)

    model = _get_model()
    texts = [_student_to_text(s) for s in _students]
    embeddings = model.encode(texts, convert_to_numpy=True)

    dim = embeddings.shape[1]
    _index = faiss.IndexFlatL2(dim)
    _index.add(embeddings.astype(np.float32))
    return _index, _students


def retrieve_students(query: str, top_k: int = 5) -> List[dict]:
    global _index, _students
    if _index is None:
        build_index()

    model = _get_model()
    query_vec = model.encode([query], convert_to_numpy=True).astype(np.float32)
    distances, indices = _index.search(query_vec, min(top_k, len(_students)))

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(_students):
            results.append(_students[idx])
    return results


def retrieve_by_name(name: str) -> Optional[dict]:
    global _students
    if not _students:
        build_index()
    name_lower = name.lower()
    for s in _students:
        if name_lower in s["name"].lower():
            return s
    return None


def retrieve_by_id(student_id: str) -> Optional[dict]:
    global _students
    if not _students:
        build_index()
    for s in _students:
        if s["student_id"] == student_id:
            return s
    return None
