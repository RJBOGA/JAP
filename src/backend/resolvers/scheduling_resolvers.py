from ariadne import QueryType, MutationType, ObjectType
from datetime import datetime, timedelta
# Lazy imports are no longer needed as the app is starting now
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
    
	schedule = scheduling_service.schedules_collection().find_one({"recruiterId": user_id}) 
	return schedule.get("availability") if schedule else []

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
	# This is a Recruiter-only mutation
	user_id = info.context.get("UserID")
	user_role = info.context.get("user_role")
	if not user_id or user_role != "Recruiter":
		raise PermissionError("Access denied: Only a Recruiter can book interviews.")
        
	try:
		start_time_dt = datetime.fromisoformat(startTime)
		end_time_dt = datetime.fromisoformat(endTime)
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