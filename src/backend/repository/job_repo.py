import re
from typing import Optional, Dict, Any, List
from pymongo import ReturnDocument
from ..db import jobs_collection, next_job_id

def to_job_output(doc: dict) -> dict:
    """Formats a job document from MongoDB for GraphQL output."""
    if not doc:
        return None
    return {
        "jobId": int(doc.get("jobId")) if doc.get("jobId") is not None else None,
        "title": doc.get("title"),
        "company": doc.get("company"),
        "location": doc.get("location"),
        "salaryRange": doc.get("salaryRange"),
        "skillsRequired": doc.get("skillsRequired"),
        "description": doc.get("description"),
        "postedAt": doc.get("postedAt"),
    }

def build_job_filter(company: Optional[str], location: Optional[str], title: Optional[str]) -> Dict[str, Any]:
    """Builds a filter query for jobs with case-insensitive regex matching."""
    q: Dict[str, Any] = {}
    if company:
        q["company"] = {"$regex": f"^{re.escape(company)}$", "$options": "i"}
    if location:
        q["location"] = {"$regex": f"^{re.escape(location)}$", "$options": "i"}
    if title:
        q["title"] = {"$regex": f".*{re.escape(title)}.*", "$options": "i"} # Partial match for title
    return q

def find_jobs(q: Dict[str, Any], skip: Optional[int], limit: Optional[int]) -> List[dict]:
    """Finds multiple jobs in the database."""
    col = jobs_collection()
    cursor = col.find(q, {"_id": 0})
    if skip is not None:
        cursor = cursor.skip(int(skip))
    if limit is not None:
        cursor = cursor.limit(int(limit))
    return list(cursor)

def find_job_by_id(job_id: int) -> Optional[dict]:
    """Finds a single job by its unique jobId."""
    return jobs_collection().find_one({"jobId": int(job_id)}, {"_id": 0})

def insert_job(doc: dict) -> None:
    """Inserts a new job document into the database."""
    jobs_collection().insert_one(doc)

def update_one_job(q: Dict[str, Any], set_fields: Dict[str, Any]) -> Optional[dict]:
    """Finds one job and updates it."""
    return jobs_collection().find_one_and_update(
        q,
        {"$set": set_fields},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )

def delete_one_job(q: Dict[str, Any]) -> int:
    """Deletes one job matching the query."""
    res = jobs_collection().delete_one(q)
    return int(res.deleted_count)