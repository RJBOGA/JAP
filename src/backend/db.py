# src/backend/db.py
import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

load_dotenv(os.path.join(os.path.dirname(__file__), '../../config/.env'))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "jobtracker")
_client = MongoClient(MONGO_URI)
_db = _client[DB_NAME]
def get_db():
    return _db

# --- Collection Helpers ---
def users_collection():
    return _db["users"]

def jobs_collection():
    return _db["jobs"]

def applications_collection():
    return _db["applications"]

def counters_collection():
    return _db["counters"]

def schedules_collection():
    return _db["schedules"]

def interviews_collection():
    return _db["interviews"]

# --- NEW: Resumes Collection ---
def resumes_collection():
    return _db["resumes"]

# --- Counters ---
def _ensure_counter(counter_id: str):
    counters_collection().update_one(
        {"_id": counter_id},
        {"$setOnInsert": {"sequence_value": 0}},
        upsert=True,
    )

def _next_id(counter_id: str):
    result = counters_collection().find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"sequence_value": 1}},
        return_document=ReturnDocument.AFTER,
        upsert=True,
    )
    return int(result["sequence_value"])

def ensure_user_counter():
    _ensure_counter("UserID")

def next_user_id():
    return _next_id("UserID")

def ensure_job_counter():
    _ensure_counter("jobId")

def next_job_id():
    return _next_id("jobId")

def ensure_application_counter():
    _ensure_counter("appId")

def next_application_id():
    return _next_id("appId")

def ensure_interview_counter():
    _ensure_counter("interviewId")

def next_interview_id():
    return _next_id("interviewId")

# --- NEW: Resume Counter ---
def ensure_resume_counter():
    _ensure_counter("resumeId")

def next_resume_id():
    return _next_id("resumeId")


# --- Output Formatting ---
def to_user_output(doc: dict):
    if not doc:
        return None
    return {
        "UserID": int(doc.get("UserID")) if doc.get("UserID") is not None else None,
        "FirstName": doc.get("FirstName"),
        "LastName": doc.get("LastName"),
        "DateOfBirth": doc.get("DateOfBirth"),
        "ProfessionalTitle": doc.get("ProfessionalTitle"),
        "Summary": doc.get("Summary"),
    }

def to_job_output(doc: dict):
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

def to_application_output(doc: dict):
    if not doc:
        return None
    return {
        "appId": int(doc.get("appId")) if doc.get("appId") is not None else None,
        "userId": int(doc.get("userId")) if doc.get("userId") is not None else None,
        "jobId": int(doc.get("jobId")) if doc.get("jobId") is not None else None,
        "status": doc.get("status"),
        "submittedAt": doc.get("submittedAt"),
        "notes": doc.get("notes"),
        "userName": doc.get("userName"),
        "jobTitle": doc.get("jobTitle"),
        "companyName": doc.get("companyName"),
        "emailSent": doc.get("emailSent"),
    }