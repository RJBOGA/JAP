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
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role != "Recruiter":
        raise PermissionError("Access denied: Only a Recruiter can view their schedule.")

    from ..db import schedules_collection
    schedule = schedules_collection().find_one({"recruiterId": user_id}) 
    return schedule.get("availability") if schedule else []


@query.field("findAvailableSlots")
def resolve_find_available_slots(_, info, candidateId, durationMinutes=30, numDays=14):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role != "Recruiter":
        raise PermissionError("Access denied: Only a Recruiter can find available slots.")
        
    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=numDays or 14)
    
    slots = scheduling_service.find_open_slots(
        recruiter_id=user_id,
        candidate_id=candidateId,
        start_date=start_date,
        end_date=end_date,
        duration_minutes=durationMinutes or 30
    )
    return slots

# --- Mutation Resolvers ---
@mutation.field("setMyAvailability")
def resolve_set_my_availability(_, info, availability):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role != "Recruiter":
        raise PermissionError("Access denied: Only a Recruiter can set their availability.")
        
    return scheduling_service.set_recruiter_availability(user_id, availability)


@mutation.field("bookInterview")
def resolve_book_interview(_, info, jobId, candidateId, startTime, endTime):
    user_id = info.context.get("UserID")
    user_role = info.context.get("user_role")
    if not user_id or user_role != "Recruiter":
        raise PermissionError("Access denied: Only a Recruiter can book interviews.")
        
    # --- FIX: Handle ISO strings with Z and validate duration ---
    try:
        # Handle 'Z' manually for older Python versions
        if startTime.endswith('Z'): startTime = startTime[:-1]
        start_time_dt = datetime.fromisoformat(startTime)
        
        # We calculate end time strictly as +30 mins to prevent malicious blocking
        # ignoring the client-provided endTime for logic, but we could validate it matches.
        end_time_dt = start_time_dt + timedelta(minutes=30)
        
    except ValueError:
        raise ValueError("Invalid time format. Use ISO 8601 format.")
    
    booked_interview = scheduling_service.book_interview(
        job_id=jobId,
        candidate_id=candidateId,
        recruiter_id=user_id,
        start_time=start_time_dt,
        end_time=end_time_dt
    )
    return booked_interview

# --- Field resolvers for the Interview type ---
@interview.field("job")
def resolve_interview_job(interview_obj, _):
    return job_repo.to_job_output(job_repo.find_job_by_id(interview_obj.get("jobId")))

@interview.field("candidate")
def resolve_interview_candidate(interview_obj, _):
    return user_repo.to_user_output(user_repo.find_one_by_id(interview_obj.get("candidateId")))