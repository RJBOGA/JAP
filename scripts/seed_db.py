import os
import sys
import bcrypt
from datetime import datetime, timedelta
from faker import Faker
import random

# --- Setup Project Path ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backend.db import get_db, counters_collection
from src.backend.models.user_models import UserProfileType

fake = Faker()

def get_next_sequence(collection_name, counter_name):
    """Manually handling counters here to ensure sync during seed"""
    db = get_db()
    ret = db.counters.find_one_and_update(
        {"_id": counter_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return ret["sequence_value"]

def reset_counters(db):
    """Resets all sequence counters to 0"""
    print("  -> Resetting counters...")
    db.counters.delete_many({})
    counters = ["UserID", "jobId", "appId", "interviewId", "resumeId"]
    for c in counters:
        db.counters.insert_one({"_id": c, "sequence_value": 0})

def seed_database():
    print("="*60)
    print("🌱 SEEDING DATABASE")
    print("="*60)
    
    db = get_db()
    
    # 1. Clear Data
    print("1. Dropping existing collections...")
    collections = ["users", "jobs", "applications", "resumes", "interviews", "schedules", "counters"]
    for col in collections:
        db[col].drop()
    
    reset_counters(db)

    # 2. Create Users
    print("\n2. Creating Users (2 per role)...")
    users = []
    
    # --- RECRUITERS ---
    recruiters = [
        {"email": "recruiter1@tech.com", "first": "Alice", "last": "Recruiter"},
        {"email": "recruiter2@tech.com", "first": "Bob", "last": "Talent"},
    ]
    
    recruiter_ids = []
    for r in recruiters:
        uid = get_next_sequence(db, "UserID")
        recruiter_ids.append(uid)
        users.append({
            "UserID": uid,
            "email": r["email"],
            "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()),
            "firstName": r["first"],
            "lastName": r["last"],
            "role": UserProfileType.RECRUITER.value,
            "createdAt": datetime.utcnow().isoformat()
        })

    # --- MANAGERS ---
    managers = [
        {"email": "manager1@tech.com", "first": "Sarah", "last": "Connor", "title": "Engineering Manager"},
        {"email": "manager2@tech.com", "first": "Mike", "last": "Ross", "title": "Product Director"},
    ]
    
    manager_ids = []
    for m in managers:
        uid = get_next_sequence(db, "UserID")
        manager_ids.append(uid)
        users.append({
            "UserID": uid,
            "email": m["email"],
            "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()),
            "firstName": m["first"],
            "lastName": m["last"],
            "role": UserProfileType.MANAGER.value,
            "professionalTitle": m["title"],
            "createdAt": datetime.utcnow().isoformat()
        })

    # --- APPLICANTS ---
    applicants = [
        {"email": "app1@gmail.com", "first": "Charlie", "last": "Dev", "citizen": True, "exp": 5, "title": "Senior Python Dev"},
        {"email": "app2@gmail.com", "first": "Diana", "last": "Junior", "citizen": False, "exp": 2, "title": "Junior Web Dev"},
    ]
    
    applicant_ids = []
    for a in applicants:
        uid = get_next_sequence(db, "UserID")
        applicant_ids.append(uid)
        users.append({
            "UserID": uid,
            "email": a["email"],
            "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()),
            "firstName": a["first"],
            "lastName": a["last"],
            "role": UserProfileType.APPLICANT.value,
            "is_us_citizen": a["citizen"],
            "years_of_experience": a["exp"],
            "professionalTitle": a["title"],
            "city": "San Francisco",
            "country": "USA",
            "skills": ["Python", "React", "SQL"],
            "createdAt": datetime.utcnow().isoformat()
        })

    db.users.insert_many(users)
    print(f"  -> Inserted {len(users)} users.")

    # 3. Create Schedules for Managers
    print("\n3. Creating Schedules for Managers...")
    schedules = []
    # Sarah (Manager 1) is free Mon/Wed 9-5
    schedules.append({
        "recruiterId": manager_ids[0],
        "availability": [
            {"dayOfWeek": "Monday", "startTime": "09:00", "endTime": "17:00"},
            {"dayOfWeek": "Wednesday", "startTime": "09:00", "endTime": "17:00"}
        ]
    })
    # Mike (Manager 2) is free Tue/Thu 10-4
    schedules.append({
        "recruiterId": manager_ids[1],
        "availability": [
            {"dayOfWeek": "Tuesday", "startTime": "10:00", "endTime": "16:00"},
            {"dayOfWeek": "Thursday", "startTime": "10:00", "endTime": "16:00"}
        ]
    })
    db.schedules.insert_many(schedules)
    print(f"  -> Inserted {len(schedules)} schedules.")

    # 4. Create Jobs
    print("\n4. Creating Jobs...")
    jobs = []
    
    # Job 1: Linked to Manager Sarah, Posted by Recruiter Alice
    jid1 = get_next_sequence(db, "jobId")
    jobs.append({
        "jobId": jid1,
        "title": "Senior Python Backend",
        "company": "TechCorp",
        "location": "Remote",
        "status": "Open",
        "requires_us_citizenship": True,
        "hiringManagerId": manager_ids[0],
        "hiringManagerName": "Sarah Connor",
        "posterUserId": recruiter_ids[0],
        "posterName": "Alice Recruiter",
        "description": "Expert Python developer needed.",
        "skillsRequired": ["Python", "Django", "FastAPI"],
        "postedAt": datetime.utcnow().strftime('%Y-%m-%d')
    })

    # Job 2: Linked to Manager Mike, Posted by Recruiter Bob
    jid2 = get_next_sequence(db, "jobId")
    jobs.append({
        "jobId": jid2,
        "title": "Frontend React Engineer",
        "company": "StartUp Inc",
        "location": "New York, NY",
        "status": "Open",
        "requires_us_citizenship": False,
        "hiringManagerId": manager_ids[1],
        "hiringManagerName": "Mike Ross",
        "posterUserId": recruiter_ids[1],
        "posterName": "Bob Talent",
        "description": "React wizard needed.",
        "skillsRequired": ["React", "TypeScript", "Redux"],
        "postedAt": datetime.utcnow().strftime('%Y-%m-%d')
    })
    
    db.jobs.insert_many(jobs)
    print(f"  -> Inserted {len(jobs)} jobs.")

    # 5. Create Resumes
    print("\n5. Creating Mock Resumes...")
    resumes = []
    
    # Resume for Charlie
    res_id1 = get_next_sequence(db, "resumeId")
    resumes.append({
        "resumeId": res_id1,
        "userId": applicant_ids[0],
        "filename": "Charlie_CV_2025.pdf",
        "url": "/resumes/mock_charlie.pdf",
        "uploadedAt": datetime.utcnow().isoformat(),
        "calculatedExperience": 5,
        "skills": ["Python", "Django", "Postgres"]
    })
    
    db.resumes.insert_many(resumes)
    print(f"  -> Inserted {len(resumes)} resumes.")

    # 6. Create Applications
    print("\n6. Creating Applications...")
    apps = []
    
    # Charlie applies to Python Job
    aid1 = get_next_sequence(db, "appId")
    apps.append({
        "appId": aid1,
        "userId": applicant_ids[0],
        "jobId": jid1,
        "status": "Interviewing", # Pre-set to interviewing
        "submittedAt": datetime.utcnow().isoformat(),
        "userName": "Charlie Dev",
        "jobTitle": "Senior Python Backend",
        "companyName": "TechCorp",
        "notes": "Strong candidate."
    })
    
    # Diana applies to React Job
    aid2 = get_next_sequence(db, "appId")
    apps.append({
        "appId": aid2,
        "userId": applicant_ids[1],
        "jobId": jid2,
        "status": "Applied",
        "submittedAt": datetime.utcnow().isoformat(),
        "userName": "Diana Junior",
        "jobTitle": "Frontend React Engineer",
        "companyName": "StartUp Inc"
    })
    
    db.applications.insert_many(apps)
    print(f"  -> Inserted {len(apps)} applications.")

    # 7. Create an Interview (Booking)
    print("\n7. Creating Interviews...")
    interviews = []
    
    # Charlie has an interview with Sarah (Manager 1) for Job 1
    # Next Monday at 10 AM
    today = datetime.utcnow()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    start_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=30)
    
    interviews.append({
        "interviewId": get_next_sequence(db, "interviewId"),
        "jobId": jid1,
        "candidateId": applicant_ids[0],
        "recruiterId": manager_ids[0], # Booked against Sarah
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat()
    })
    
    db.interviews.insert_many(interviews)
    print(f"  -> Inserted {len(interviews)} interviews.")

    print("\n" + "="*60)
    print("✅ DATABASE SEEDED SUCCESSFULLY")
    print("="*60)
    print("CREDENTIALS (Password: password123):")
    print("-----------------------------------")
    print("RECRUITERS:")
    for r in recruiters: print(f" - {r['email']}")
    print("\nMANAGERS:")
    for m in managers: print(f" - {m['email']}")
    print("\nAPPLICANTS:")
    for a in applicants: print(f" - {a['email']} (Citizen: {a['citizen']})")
    print("-----------------------------------")

if __name__ == "__main__":
    seed_database()