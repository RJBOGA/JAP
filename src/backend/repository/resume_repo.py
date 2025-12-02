# src/backend/repository/resume_repo.py
from typing import List, Optional
from ..db import resumes_collection, next_resume_id, ensure_resume_counter

def insert_resume(doc: dict):
    """
    Inserts a new resume document into the database.
    """
    resumes_collection().insert_one(doc)

def find_resumes_by_user(user_id: int) -> List[dict]:
    """
    Retrieves all resumes associated with a specific UserID.
    """
    return list(resumes_collection().find({"userId": int(user_id)}, {"_id": 0}))

def find_resume_by_id(resume_id: int) -> Optional[dict]:
    """
    Retrieves a single resume by its unique resumeId.
    """
    return resumes_collection().find_one({"resumeId": int(resume_id)}, {"_id": 0})

def delete_resume(resume_id: int) -> bool:
    """
    Deletes a resume by ID. Returns True if deleted, False if not found.
    """
    res = resumes_collection().delete_one({"resumeId": int(resume_id)})
    return res.deleted_count > 0

# Ensure the resumeId counter exists in the DB when this module is loaded
ensure_resume_counter()