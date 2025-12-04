from ariadne import QueryType, MutationType, ObjectType
from datetime import datetime, timedelta
from ..services import scheduling_service
from ..repository import job_repo, user_repo, application_repo
from ..db import to_user_output

query = QueryType()
mutation = MutationType()
interview = ObjectType("Interview") 

@query.field("mySchedule")
def resolve_my_schedule(_, info):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role not in ["Recruiter", "Manager"]:
        raise PermissionError("Access denied: Only Recruiters or Managers can view schedules.")

    from ..db import schedules_collection
    schedule = schedules_collection().find_one({"recruiterId": user_id}) 
    return schedule.get("availability") if schedule else []

@query.field("findAvailableSlots")
def resolve_find_available_slots(_, info, jobId, candidateId, durationMinutes=30, numDays=14):
    job = job_repo.find_job_by_id(jobId)
    if not job: raise ValueError(f"Job {jobId} not found.")
    
    interviewer_id = job.get("hiringManagerId") or job.get("posterUserId")
    if not interviewer_id: raise ValueError("This job has no assigned Hiring Manager or Poster to schedule with.")

    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=numDays or 14)
    
    slots = scheduling_service.find_open_slots(
        interviewer_id=interviewer_id, 
        candidate_id=candidateId,
        start_date=start_date,
        end_date=end_date,
        duration_minutes=durationMinutes or 30
    )
    return slots

# --- NEW QUERY (FS.4) ---
@query.field("myBookedInterviews")
def resolve_my_booked_interviews(_, info):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    
    if not user_id or user_role not in ["Recruiter", "Manager"]:
        raise PermissionError("Access denied: Only Recruiters or Managers can view booked interviews.")
    
    from ..db import interviews_collection
    # Find interviews where this user is either the Recruiter (Coordinator) or Hiring Manager
    interviews = list(interviews_collection().find({
        "$or": [
            {"recruiterId": user_id},
            {"hiringManagerId": user_id}
        ]
    }))
    
    return interviews

@mutation.field("setMyAvailability")
def resolve_set_my_availability(_, info, availability):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role not in ["Recruiter", "Manager"]:
        raise PermissionError("Access denied: Only Recruiters or Managers can set availability.")
    return scheduling_service.set_recruiter_availability(user_id, availability)

@mutation.field("bookInterview")
def resolve_book_interview(_, info, jobId, candidateId, startTime, endTime):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role not in ["Recruiter", "Manager"]:
        raise PermissionError("Access denied: You must be a Recruiter or Manager to book interviews.")
        
    job = job_repo.find_job_by_id(jobId)
    if not job: raise ValueError(f"Job {jobId} not found.")
    
    recruiter_id = job.get("posterUserId")
    hiring_manager_id = job.get("hiringManagerId")
    if not recruiter_id: raise ValueError("Job has no recruiter coordinator assigned.")
    
    try:
        if startTime.endswith('Z'): startTime = startTime[:-1]
        start_time_dt = datetime.fromisoformat(startTime)
        end_time_dt = start_time_dt + timedelta(minutes=30)
    except ValueError:
        raise ValueError("Invalid time format. Use ISO 8601 format.")
    
    return scheduling_service.book_interview(
        job_id=jobId,
        candidate_id=candidateId,
        recruiter_id=recruiter_id,
        hiring_manager_id=hiring_manager_id,
        start_time=start_time_dt,
        end_time=end_time_dt
    )

@mutation.field("bookInterviewByNaturalLanguage")
def resolve_book_interview_nl(_, info, candidateName, jobTitle, startTimeISO, companyName=None):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role != "Recruiter":
        raise PermissionError("Access denied.")

    name_parts = candidateName.strip().split()
    first = name_parts[0]
    last = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
    q_user = user_repo.build_filter(first, last, None)
    candidates = user_repo.find_users(q_user, None, None)
    if not candidates: raise ValueError(f"Candidate '{candidateName}' not found.")
    candidate_id = candidates[0]['UserID']

    q_job = job_repo.build_job_filter(companyName, None, jobTitle)
    jobs = job_repo.find_jobs(q_job, None, None)
    if not jobs: raise ValueError(f"Job '{jobTitle}' not found.")
    job = jobs[0]
    
    recruiter_id = job.get("posterUserId")
    hiring_manager_id = job.get("hiringManagerId")

    try:
        if startTimeISO.endswith('Z'): startTimeISO = startTimeISO[:-1]
        start_dt = datetime.fromisoformat(startTimeISO)
        end_dt = start_dt + timedelta(minutes=30)
    except ValueError:
        raise ValueError(f"Invalid date format.")

    return scheduling_service.book_interview(
        job_id=job['jobId'],
        candidate_id=candidate_id,
        recruiter_id=recruiter_id,
        hiring_manager_id=hiring_manager_id,
        start_time=start_dt,
        end_time=end_dt
    )

# --- NEW MUTATION (FS.2) ---
@mutation.field("selectInterviewSlot")
def resolve_select_interview_slot(_, info, appId, startTime):
    """
    Applicant-driven booking. Logic is slightly different:
    1. Check if user is Applicant and owns the application.
    2. Check status is InterviewInviteSent.
    3. Determine Job/Manager.
    4. Book.
    """
    user_id = info.context.get("UserID")
    if not user_id: raise PermissionError("You must be logged in.")
    
    # 1. Fetch Application
    app = application_repo.find_application_by_id(appId)
    if not app: raise ValueError("Application not found.")
    
    # Security: Ensure owning user
    if app["userId"] != user_id:
        raise PermissionError("You do not have permission to modify this application.")
    
    # Logic: Status must be InterviewInviteSent
    if app["status"] != "InterviewInviteSent":
        raise ValueError(f"Booking failed: Current status is '{app['status']}', not 'InterviewInviteSent'.")
        
    # 2. Fetch Job Details
    job = job_repo.find_job_by_id(app["jobId"])
    if not job: raise ValueError("Job not found.")
    
    recruiter_id = job.get("posterUserId")
    hiring_manager_id = job.get("hiringManagerId")
    if not recruiter_id: recruiter_id = job.get("posterUserId") or 1 # Fallback to 1 (Recruiter) if missing data issues
    
    # 3. Parse Time
    try:
        if startTime.endswith('Z'): startTime = startTime[:-1]
        start_time_dt = datetime.fromisoformat(startTime)
        end_time_dt = start_time_dt + timedelta(minutes=30)
    except ValueError:
        raise ValueError("Invalid time format.")
        
    # 4. Book
    booking = scheduling_service.book_interview(
        job_id=job["jobId"],
        candidate_id=user_id, # The applicant is the candidate
        recruiter_id=recruiter_id,
        hiring_manager_id=hiring_manager_id,
        start_time=start_time_dt,
        end_time=end_time_dt
    )
    
    return booking

@interview.field("job")
def resolve_interview_job(interview_obj, _):
    return job_repo.to_job_output(job_repo.find_job_by_id(interview_obj.get("jobId")))

@interview.field("candidate")
def resolve_interview_candidate(interview_obj, _):
    return user_repo.to_user_output(user_repo.find_one_by_id(interview_obj.get("candidateId")))
