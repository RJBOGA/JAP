# src/backend/resolvers/application_resolvers.py
from datetime import datetime
from ariadne import QueryType, MutationType, ObjectType
from ..db import next_application_id, to_application_output
from ..validators.common_validators import clean_update_input
from ..repository import user_repo, job_repo, application_repo

query = QueryType()
mutation = MutationType()
application = ObjectType("Application")

@query.field("applications")
def resolve_applications(*_, userId=None, jobId=None, status=None):
    q = {}
    if userId: q["userId"] = int(userId)
    if jobId: q["jobId"] = int(jobId)
    if status: q["status"] = status
    docs = application_repo.find_applications(q)
    return [to_application_output(d) for d in docs]

@query.field("applicationById")
def resolve_application_by_id(*_, appId):
    doc = application_repo.find_application_by_id(int(appId))
    if not doc: raise ValueError(f"Application with ID {appId} not found.")
    return to_application_output(doc)

@application.field("candidate")
def resolve_application_candidate(app_obj, _):
    user_id = app_obj.get("userId")
    if not user_id: return None
    user_doc = user_repo.find_one_by_id(user_id)
    return user_repo.to_user_output(user_doc)

@application.field("job")
def resolve_application_job(app_obj, _):
    job_id = app_obj.get("jobId")
    if not job_id: return None
    job_doc = job_repo.find_job_by_id(job_id)
    return job_repo.to_job_output(job_doc)

@mutation.field("createApplication")
def resolve_create_application(*_, input):
    user_id, job_id = input.get("userId"), input.get("jobId")
    if not user_repo.find_one_by_id(user_id): raise ValueError(f"Validation failed: User with ID {user_id} does not exist.")
    if not job_repo.find_job_by_id(job_id): raise ValueError(f"Validation failed: Job with ID {job_id} does not exist.")
    doc = {
        "appId": next_application_id(), "userId": user_id, "jobId": job_id,
        "status": "Applied", "submittedAt": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "notes": input.get("notes")
    }
    application_repo.insert_application(doc)
    return to_application_output(doc)

@mutation.field("apply")
def resolve_apply(*_, userName, jobTitle, companyName=None):
    name_parts = userName.strip().split()
    first_name, last_name = (name_parts[0], " ".join(name_parts[1:])) if len(name_parts) > 1 else (name_parts[0], None)
    if not first_name: raise ValueError("User name cannot be empty.")

    # --- CORRECTED FUNCTION CALL ---
    user_filter = user_repo.build_filter(first_name, last_name, None, None)
    matching_users = user_repo.find_users(user_filter, None, None)
    
    if len(matching_users) == 0: raise ValueError(f"Could not find a user named '{userName}'.")
    if len(matching_users) > 1: raise ValueError(f"Found multiple users named '{userName}'. Please be more specific.")
    user = matching_users[0]
    
    job_filter = job_repo.build_job_filter(companyName, None, jobTitle)
    matching_jobs = job_repo.find_jobs(job_filter, None, None)
    if len(matching_jobs) == 0: raise ValueError(f"Could not find a job with title '{jobTitle}' at company '{companyName or ''}'.")
    if len(matching_jobs) > 1: raise ValueError(f"Found multiple jobs with title '{jobTitle}'. Please specify a company.")
    job = matching_jobs[0]

    application_input = {"userId": user["UserID"], "jobId": job["jobId"]}
    return resolve_create_application(None, input=application_input)

@mutation.field("updateApplication")
def resolve_update_application(*_, appId, input):
    set_fields = clean_update_input(input)
    if not set_fields: raise ValueError("No fields provided to update.")
    updated = application_repo.update_one_application({"appId": int(appId)}, set_fields)
    if not updated: raise ValueError(f"Application with ID {appId} not found for update.")
    return to_application_output(updated)