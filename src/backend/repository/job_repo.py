# src/backend/repository/job_repo.py
import re
from typing import Optional, Dict, Any, List
from pymongo import ReturnDocument
from ..db import jobs_collection

def to_job_output(doc: dict) -> dict:
    if not doc: return None
    return {
        "jobId": int(doc.get("jobId")) if doc.get("jobId") is not None else None,
        "title": doc.get("title"), "company": doc.get("company"), "location": doc.get("location"),
        "salaryRange": doc.get("salaryRange"), "skillsRequired": doc.get("skillsRequired"),
        "description": doc.get("description"), "postedAt": doc.get("postedAt"),
        "requires_us_citizenship": doc.get("requires_us_citizenship"),
        "minimum_degree_year": doc.get("minimum_degree_year"),
        "status": doc.get("status"),
        "posterUserId": doc.get("posterUserId"),
        "posterName": doc.get("posterName"),
    }

def build_job_filter(company: Optional[str], location: Optional[str], title: Optional[str], poster_user_id: Optional[int] = None) -> Dict[str, Any]:
    q: Dict[str, Any] = {}
    if company: q["company"] = {"$regex": f"^{re.escape(company)}$", "$options": "i"}
    if location: q["location"] = {"$regex": f"^{re.escape(location)}$", "$options": "i"}
    if title: q["title"] = {"$regex": f".*{re.escape(title)}.*", "$options": "i"}
    if poster_user_id is not None: q["posterUserId"] = int(poster_user_id)
    return q

def find_jobs(q: Dict[str, Any], skip: Optional[int], limit: Optional[int]) -> List[dict]:
    cursor = jobs_collection().find(q, {"_id": 0})
    if skip is not None: cursor = cursor.skip(int(skip))
    if limit is not None: cursor = cursor.limit(int(limit))
    return list(cursor)

def find_job_by_id(job_id: int) -> Optional[dict]:
    return jobs_collection().find_one({"jobId": int(job_id)}, {"_id": 0})

def insert_job(doc: dict) -> None:
    jobs_collection().insert_one(doc)

def update_one_job(q: Dict[str, Any], set_fields: Dict[str, Any]) -> Optional[dict]:
    return jobs_collection().find_one_and_update(
        q, {"$set": set_fields}, projection={"_id": 0}, return_document=ReturnDocument.AFTER
    )

def delete_one_job(q: Dict[str, Any]) -> int:
    res = jobs_collection().delete_one(q)
    return int(res.deleted_count)

def add_skills_to_job(job_id: int, skills: List[str]) -> Optional[dict]:
    return jobs_collection().find_one_and_update(
        {"jobId": int(job_id)},
        {"$addToSet": {"skillsRequired": {"$each": skills}}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )