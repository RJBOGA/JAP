# src/backend/repository/user_repo.py
import re
from typing import Optional, Dict, Any, List
from pymongo import ReturnDocument
from ..db import users_collection

def find_user_by_email(email: str) -> Optional[dict]:
    return users_collection().find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})

def to_user_output(doc: dict) -> Optional[dict]:
    if not doc: return None
    return {
        "UserID": doc.get("UserID"), "email": doc.get("email"), "firstName": doc.get("firstName"),
        "lastName": doc.get("lastName"), "role": doc.get("role"), "phone_number": doc.get("phone_number"),
        "city": doc.get("city"), "state_province": doc.get("state_province"), "country": doc.get("country"),
        "linkedin_profile": doc.get("linkedin_profile"), "portfolio_url": doc.get("portfolio_url"),
        "highest_qualification": doc.get("highest_qualification"), "years_of_experience": doc.get("years_of_experience"),
        "createdAt": doc.get("createdAt"), "dob": doc.get("dob"), "skills": doc.get("skills"),
        "professionalTitle": doc.get("professionalTitle"), "is_us_citizen": doc.get("is_us_citizen"),
        "highest_degree_year": doc.get("highest_degree_year")
    }

def build_filter(first_name: Optional[str], last_name: Optional[str], dob: Optional[str], skills: Optional[List[str]] = None) -> Dict[str, Any]:
    q = {}
    if first_name: q["firstName"] = {"$regex": f"^{re.escape(first_name)}$", "$options": "i"}
    if last_name: q["lastName"] = {"$regex": f"^{re.escape(last_name)}$", "$options": "i"}
    if dob: q["dob"] = dob
    if skills: q["skills"] = {"$all": skills}
    return q

def find_users(q: Dict[str, Any], skip: Optional[int], limit: Optional[int]) -> List[dict]:
    cursor = users_collection().find(q, {"_id": 0, "password": 0})
    if skip is not None: cursor = cursor.skip(int(skip))
    if limit is not None: cursor = cursor.limit(int(limit))
    return list(cursor)

def find_one_by_id(user_id: int) -> Optional[dict]:
    return users_collection().find_one({"UserID": int(user_id)}, {"_id": 0, "password": 0})

def insert_user(doc: dict) -> None:
    users_collection().insert_one(doc)

def update_one(q: Dict[str, Any], set_fields: Dict[str, Any]) -> Optional[dict]:
    return users_collection().find_one_and_update(
        q, {"$set": set_fields}, projection={"_id": 0, "password": 0}, return_document=ReturnDocument.AFTER
    )

def delete_one(q: Dict[str, Any]) -> int:
    res = users_collection().delete_one(q)
    return int(res.deleted_count)

def add_skills_to_user(user_id: int, skills: List[str]) -> Optional[dict]:
    return users_collection().find_one_and_update(
        {"UserID": int(user_id)},
        {"$addToSet": {"skills": {"$each": skills}}},
        projection={"_id": 0, "password": 0},
        return_document=ReturnDocument.AFTER,
    )