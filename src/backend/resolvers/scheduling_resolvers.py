from ariadne import QueryType, MutationType, ObjectType
from datetime import datetime, timedelta
from ..services import scheduling_service
from ..repository import job_repo, user_repo
from ..db import to_user_output

query = QueryType()
mutation = MutationType()
interview = ObjectType("Interview") 

# --- Query Resolvers ---

@query.field("mySchedule")
def resolve_my_schedule(_, info):
    # This allows BOTH Recruiters and Managers to see their own schedules
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role not in ["Recruiter", "Manager"]:
        raise PermissionError("Access denied: Only Recruiters or Managers can view schedules.")

    from ..db import schedules_collection
    schedule = schedules_collection().find_one({"recruiterId": user_id}) 
    return schedule.get("availability") if schedule else []


@query.field("findAvailableSlots")
def resolve_find_available_slots(_, info, jobId, candidateId, durationMinutes=30, numDays=14):
    # 1. Fetch Job to determine WHO to schedule against
    job = job_repo.find_job_by_id(jobId)
    if not job:
        raise ValueError(f"Job {jobId} not found.")
    
    # 2. Determine Interviewer ID
    # Priority: Hiring Manager -> Job Poster (Recruiter)
    interviewer_id = job.get("hiringManagerId") or job.get("posterUserId")
    
    if not interviewer_id:
        raise ValueError("This job has no assigned Hiring Manager or Poster to schedule with.")

    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=numDays or 14)
    
    # 3. Find slots using the INTERVIEWER'S ID, not the logged-in user's
    slots = scheduling_service.find_open_slots(
        recruiter_id=interviewer_id, 
        candidate_id=candidateId,
        start_date=start_date,
        end_date=end_date,
        duration_minutes=durationMinutes or 30
    )
    return slots

# --- Mutation Resolvers ---

@mutation.field("setMyAvailability")
def resolve_set_my_availability(_, info, availability):
    # Allows both Recruiters AND Managers to set their time
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role not in ["Recruiter", "Manager"]:
        raise PermissionError("Access denied: Only Recruiters or Managers can set availability.")
    
    # Pass to service and RETURN the result (True/False)
    return scheduling_service.set_recruiter_availability(user_id, availability)


@mutation.field("bookInterview")
def resolve_book_interview(_, info, jobId, candidateId, startTime, endTime):
    # Only Recruiters can book (acting as coordination), or potentially Managers
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role not in ["Recruiter", "Manager"]:
        raise PermissionError("Access denied: You must be a Recruiter or Manager to book interviews.")
        
    # 1. Fetch Job to determine the Recruiter and Hiring Manager
    job = job_repo.find_job_by_id(jobId)
    if not job:
        raise ValueError(f"Job {jobId} not found.")
    
    # Extract both IDs distinctly
    recruiter_id = job.get("posterUserId")  # The Recruiter who created the job (coordinator)
    hiring_manager_id = job.get("hiringManagerId")  # The Manager assigned to interview
    
    if not recruiter_id:
        raise ValueError("Job has no recruiter coordinator assigned.")
    if not hiring_manager_id:
        raise ValueError("Job has no hiring manager assigned.")

    try:
        if startTime.endswith('Z'): startTime = startTime[:-1]
        start_time_dt = datetime.fromisoformat(startTime)
        # Force 30 min duration for consistency
        end_time_dt = start_time_dt + timedelta(minutes=30)
        
    except ValueError:
        raise ValueError("Invalid time format. Use ISO 8601 format.")
    
    # 2. Book with BOTH recruiter (coordinator) and hiring manager (interviewer)
    booked_interview = scheduling_service.book_interview(
        job_id=jobId,
        candidate_id=candidateId,
        recruiter_id=recruiter_id,         # The Coordinator
        hiring_manager_id=hiring_manager_id,  # The Interviewer
        start_time=start_time_dt,
        end_time=end_time_dt
    )
    return booked_interview

@mutation.field("bookInterviewByNaturalLanguage")
def resolve_book_interview_nl(_, info, candidateName, jobTitle, startTimeISO, companyName=None):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role != "Recruiter":
        raise PermissionError("Access denied: Only a Recruiter can book interviews.")

    # 1. Resolve Candidate
    name_parts = candidateName.strip().split()
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
    
    q_user = user_repo.build_filter(first_name, last_name, None)
    candidates = user_repo.find_users(q_user, None, None)
    if not candidates: raise ValueError(f"Candidate '{candidateName}' not found.")
    candidate_id = candidates[0]['UserID']

    # 2. Resolve Job
    q_job = job_repo.build_job_filter(companyName, None, jobTitle)
    jobs = job_repo.find_jobs(q_job, None, None)
    if not jobs: raise ValueError(f"Job '{jobTitle}' not found.")
    job = jobs[0]
    job_id = job['jobId']
    
    # 3. Extract both IDs distinctly
    recruiter_id = job.get("posterUserId")  # The Recruiter who created the job (coordinator)
    hiring_manager_id = job.get("hiringManagerId")  # The Manager assigned to interview

    # 4. Parse Time
    try:
        if startTimeISO.endswith('Z'): startTimeISO = startTimeISO[:-1]
        start_dt = datetime.fromisoformat(startTimeISO)
        end_dt = start_dt + timedelta(minutes=30)
    except ValueError:
        raise ValueError(f"Invalid date format ({startTimeISO}).")

    # 5. Book with both IDs
    return scheduling_service.book_interview(
        job_id=job_id,
        candidate_id=candidate_id,
        recruiter_id=recruiter_id,         # The Coordinator
        hiring_manager_id=hiring_manager_id,  # The Interviewer
        start_time=start_dt,
        end_time=end_dt
    )

# --- Field resolvers ---
@interview.field("job")
def resolve_interview_job(interview_obj, _):
    return job_repo.to_job_output(job_repo.find_job_by_id(interview_obj.get("jobId")))

@interview.field("candidate")
def resolve_interview_candidate(interview_obj, _):
    return user_repo.to_user_output(user_repo.find_one_by_id(interview_obj.get("candidateId")))
