from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Helper to handle ISO strings safely
def parse_iso(date_str):
    if not date_str: return None
    if date_str.endswith('Z'): date_str = date_str[:-1]
    return datetime.fromisoformat(date_str)

def set_recruiter_availability(recruiter_id: int, availability_data: list):
    from ..db import schedules_collection
    schedules_collection().update_one(
        {"recruiterId": recruiter_id},
        {"$set": {"availability": availability_data, "recruiterId": recruiter_id}},
        upsert=True
    )
    return True

def find_open_slots(recruiter_id: int, candidate_id: int, start_date: datetime, end_date: datetime, duration_minutes: int = 30):
    from ..db import schedules_collection, interviews_collection
    
    # 1. Get Schedule
    schedule = schedules_collection().find_one({"recruiterId": recruiter_id})
    if not schedule or not schedule.get("availability"):
        return [] # No availability set

    # 2. Get Bookings
    booked = list(interviews_collection().find({
        "$or": [{"recruiterId": recruiter_id}, {"candidateId": candidate_id}],
        "startTime": {"$gte": start_date.isoformat()},
        "endTime": {"$lte": end_date.isoformat()}
    }))
    
    booked_slots = []
    for b in booked:
        try:
            booked_slots.append((parse_iso(b.get("startTime")), parse_iso(b.get("endTime"))))
        except: continue

    # 3. Generate Slots
    open_slots = []
    day_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
    current = start_date
    now = datetime.utcnow()

    while current <= end_date:
        day_name = day_map[current.weekday()]
        
        for rule in schedule["availability"]:
            if rule.get("dayOfWeek", "").lower() != day_name.lower(): continue
            
            try:
                s_time = datetime.strptime(rule["startTime"], "%H:%M").time()
                e_time = datetime.strptime(rule["endTime"], "%H:%M").time()
                
                slot_start = datetime.combine(current.date(), s_time)
                limit = datetime.combine(current.date(), e_time)
                
                while slot_start + timedelta(minutes=duration_minutes) <= limit:
                    slot_end = slot_start + timedelta(minutes=duration_minutes)
                    
                    # Skip past slots and conflicts
                    if slot_start > now:
                        conflict = any(bs < slot_end and be > slot_start for bs, be in booked_slots)
                        if not conflict:
                            open_slots.append(slot_start.isoformat())
                    
                    slot_start += timedelta(minutes=duration_minutes)
            except Exception as e:
                logger.error(f"Error processing slot: {e}")
                continue
                
        current += timedelta(days=1)
        
    return open_slots

def book_interview(job_id, candidate_id, recruiter_id, start_time, end_time):
    from ..db import interviews_collection, next_interview_id
    from ..repository.application_repo import update_one_application
    from ..repository import user_repo, job_repo
    from ..services.email_service import send_interview_invitation
    
    # Conflict Check
    conflict = interviews_collection().find_one({
        "$or": [{"recruiterId": recruiter_id}, {"candidateId": candidate_id}],
        "startTime": {"$lt": end_time.isoformat()},
        "endTime": {"$gt": start_time.isoformat()}
    })
    
    if conflict: raise ValueError("Conflict detected. Slot unavailable.")

    doc = {
        "interviewId": next_interview_id(),
        "jobId": job_id, "candidateId": candidate_id, "recruiterId": recruiter_id,
        "startTime": start_time.isoformat(), "endTime": end_time.isoformat()
    }
    interviews_collection().insert_one(doc)
    
    # Update Status & Email
    app = update_one_application({"userId": candidate_id, "jobId": job_id}, {"status": "Interviewing"})
    cand = user_repo.find_one_by_id(candidate_id)
    job = job_repo.find_job_by_id(job_id)
    
    if cand and job:
        send_interview_invitation(cand["email"], cand["firstName"], job["title"], job["company"], app["appId"] if app else 0)
        
    return doc