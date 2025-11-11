# src/backend/resolvers/job_resolvers.py
from datetime import datetime
from ariadne import QueryType, MutationType
from ..validators.common_validators import require_non_empty_str, clean_update_input
from ..repository.job_repo import (
    build_job_filter,
    find_jobs,
    find_job_by_id,
    insert_job,
    update_one_job,
    delete_one_job,
    to_job_output,
    add_skills_to_job,
)
from ..db import next_job_id

query = QueryType()
mutation = MutationType()

# --- READ Operations (Publicly Accessible) ---

@query.field("jobs")
def resolve_jobs(obj, info, limit=None, skip=None, company=None, location=None, title=None):
    # No authorization check needed here. Anyone can search for jobs.
    q = build_job_filter(company, location, title)
    docs = find_jobs(q, skip, limit)
    return [to_job_output(d) for d in docs]

@query.field("jobById")
def resolve_job_by_id(obj, info, jobId):
    # No authorization check needed here. Anyone can view a specific job.
    doc = find_job_by_id(int(jobId))
    if not doc:
        raise ValueError(f"Job with ID {jobId} not found.")
    return to_job_output(doc)

# --- MUTATION Operations (Protected for Recruiters) ---

@mutation.field("createJob")
def resolve_create_job(obj, info, input):
    # --- AUTHORIZATION CHECK ---
    user_role = info.context.get("user_role")
    if user_role != "Recruiter":
        raise ValueError("Permission denied: You must be a Recruiter to post a job.")

    title = require_non_empty_str(input.get("title"), "title")
    
    doc = {
        "jobId": next_job_id(),
        "title": title,
        "company": input.get("company"),
        "location": input.get("location"),
        "salaryRange": input.get("salaryRange"),
        "skillsRequired": input.get("skillsRequired", []),
        "description": input.get("description"),
        "postedAt": datetime.utcnow().strftime('%Y-%m-%d'),
    }
    insert_job(doc)
    return to_job_output(doc)

@mutation.field("updateJob")
def resolve_update_job(obj, info, jobId, input):
    # --- AUTHORIZATION CHECK ---
    user_role = info.context.get("user_role")
    if user_role != "Recruiter":
        raise ValueError("Permission denied: You must be a Recruiter to update a job.")

    if "title" in input and input["title"] is not None:
        require_non_empty_str(input["title"], "title")

    set_fields = clean_update_input(input)
    if not set_fields:
        raise ValueError("No fields provided to update.")

    updated = update_one_job({"jobId": int(jobId)}, set_fields)
    if not updated:
        raise ValueError(f"Job with ID {jobId} not found for update.")
    return to_job_output(updated)

@mutation.field("deleteJob")
def resolve_delete_job(obj, info, jobId):
    # --- AUTHORIZATION CHECK ---
    user_role = info.context.get("user_role")
    if user_role != "Recruiter":
        raise ValueError("Permission denied: You must be a Recruiter to delete a job.")

    count = delete_one_job({"jobId": int(jobId)})
    if count == 0:
        raise ValueError(f"Job with ID {jobId} not found for deletion.")
    return True

@mutation.field("addSkillsToJob")
def resolve_add_skills_to_job(obj, info, jobId, skills):
    # --- AUTHORIZATION CHECK ---
    user_role = info.context.get("user_role")
    if user_role != "Recruiter":
        raise ValueError("Permission denied: You must be a Recruiter to modify a job.")

    if not skills:
        raise ValueError("The 'skills' list cannot be empty.")

    # Call our new repository function
    updated_job = add_skills_to_job(jobId, skills)
    
    if not updated_job:
        raise ValueError(f"Job with ID {jobId} not found.")
        
    return to_job_output(updated_job)

@mutation.field("deleteJobByFields")
def resolve_delete_job_by_fields(obj, info, title, company=None):
    # --- AUTHORIZATION CHECK ---
    user_role = info.context.get("user_role")
    if user_role != "Recruiter":
        raise ValueError("Permission denied: You must be a Recruiter to delete a job.")

    # Build a filter to find the job(s)
    q = build_job_filter(company, None, title)
    
    # --- SAFETY CHECK ---
    # Before deleting, find how many jobs match the criteria.
    matching_jobs = find_jobs(q, None, None)
    
    if len(matching_jobs) == 0:
        raise ValueError(f"No job found with title '{title}' at company '{company or ''}'.")
    if len(matching_jobs) > 1:
        raise ValueError("Multiple jobs matched this criteria. Please be more specific or use a Job ID.")
        
    # If exactly one job matches, proceed with deletion
    count = delete_one_job(q)
    return count == 1