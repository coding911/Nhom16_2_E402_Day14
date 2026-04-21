import json
import os
from typing import Any
from config import DATA_PATH


def classify_hoc_luc(final_score: float) -> str:
    if final_score >= 9.0:
        return "Xuất sắc"
    elif final_score >= 8.0:
        return "Giỏi"
    elif final_score >= 6.5:
        return "Khá"
    elif final_score >= 5.0:
        return "Trung bình"
    else:
        return "Yếu"


def evaluate_student(student: dict) -> dict:
    """Rule-based evaluation tool for a student."""
    try:
        final_score = float(student.get("final_score", 0))
        process_score = float(student.get("process_score", 0))
        attendance = float(student.get("attendance", 0))

        hoc_luc = classify_hoc_luc(final_score)
        chuyen_can = attendance >= 0.8
        tien_bo = final_score > process_score

        return {
            "student_id": student.get("student_id"),
            "name": student.get("name"),
            "hoc_luc": hoc_luc,
            "chuyen_can": chuyen_can,
            "tien_bo": tien_bo,
            "attendance_rate": f"{attendance * 100:.1f}%",
            "process_score": process_score,
            "final_score": final_score,
        }
    except Exception as e:
        return {"error": f"evaluate_student error: {str(e)}"}


def add_student(student_data: dict) -> dict:
    """Add a new student to the JSON database."""
    required_fields = [
        "name", "age", "student_id", "class_name",
        "school", "process_score", "final_score", "attendance"
    ]
    try:
        for field in required_fields:
            if field not in student_data:
                return {"error": f"Missing required field: {field}"}

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            students = json.load(f)

        # Check duplicate student_id
        existing_ids = {s["student_id"] for s in students}
        if student_data["student_id"] in existing_ids:
            return {"error": f"student_id {student_data['student_id']} already exists"}

        students.append(student_data)

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(students, f, ensure_ascii=False, indent=2)

        return {"success": True, "added": student_data["name"], "total_students": len(students)}
    except Exception as e:
        return {"error": f"add_student error: {str(e)}"}
    
def delete_student(student_id: str) -> dict:
    """Delete a student from the JSON database by student_id."""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            students = json.load(f)

        # Find student to delete
        matched = next((s for s in students if s["student_id"] == student_id), None)
        if not matched:
            return {"error": f"student_id {student_id} not found"}

        students = [s for s in students if s["student_id"] != student_id]

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(students, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "deleted": matched["name"],
            "student_id": student_id,
            "total_students": len(students),
        }
    except Exception as e:
        return {"error": f"delete_student error: {str(e)}"}

def update_student(student_id: str, updates: dict) -> dict:
    """
    Update student information by student_id.
    
    Supported update operations via keys in `updates`:
    - "name"          : str  — đổi tên
    - "age"           : int  — đổi tuổi  
    - "student_id"    : str  — đổi mã sinh viên (new ID)
    - "class_name"    : str  — đổi tên lớp
    - "school"        : str  — đổi tên trường
    - "final_score"   : float — đổi điểm cuối kỳ
    - "attendance"    : float — đổi chuyên cần
    - "add_scores"    : list[float] — thêm điểm quá trình
    - "remove_scores" : list[float] — xoá điểm quá trình (xoá lần xuất hiện đầu tiên của mỗi giá trị)
    - "set_scores"    : list[float] — thay toàn bộ điểm quá trình
    """
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            students = json.load(f)

        idx = next((i for i, s in enumerate(students) if s["student_id"] == student_id), None)
        if idx is None:
            return {"error": f"student_id {student_id} not found"}

        student = students[idx]
        changed = {}

        # Scalar fields
        for field in ("name", "age", "class_name", "school", "final_score", "attendance"):
            if field in updates:
                changed[field] = {"from": student.get(field), "to": updates[field]}
                student[field] = updates[field]

        # New student_id
        if "student_id" in updates:
            new_id = updates["student_id"]
            existing_ids = {s["student_id"] for i, s in enumerate(students) if i != idx}
            if new_id in existing_ids:
                return {"error": f"student_id {new_id} already exists"}
            changed["student_id"] = {"from": student_id, "to": new_id}
            student["student_id"] = new_id

        # process_score operations
        scores = list(student.get("process_score", []))

        if "set_scores" in updates:
            changed["process_score"] = {"from": scores, "to": updates["set_scores"]}
            scores = [round(float(s), 1) for s in updates["set_scores"]]

        if "add_scores" in updates:
            added = [round(float(s), 1) for s in updates["add_scores"]]
            changed["add_scores"] = added
            scores = scores + added

        if "remove_scores" in updates:
            to_remove = [round(float(s), 1) for s in updates["remove_scores"]]
            removed, not_found = [], []
            for val in to_remove:
                if val in scores:
                    scores.remove(val)
                    removed.append(val)
                else:
                    not_found.append(val)
            changed["remove_scores"] = {"removed": removed, "not_found": not_found}

        student["process_score"] = scores
        students[idx] = student

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(students, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "student_id": student.get("student_id"),
            "name": student.get("name"),
            "changed": changed,
        }

    except Exception as e:
        return {"error": f"update_student error: {str(e)}"}

def get_all_students() -> list:
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return []
