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
from ..repository import user_repo # <--- Need this to validate Manager ID
from ..db import next_job_id

query = QueryType()
mutation = MutationType()


# --- Helper to validate Hiring Manager (Updated for Name Lookup) ---
def _resolve_manager_info(manager_id=None, manager_name=None):
    user = None
    
    # 1. Try by ID
    if manager_id:
        user = user_repo.find_one_by_id(manager_id)
    # 2. Try by Name
    elif manager_name:
        parts = manager_name.strip().split()
        if len(parts) >= 1:
            first = parts[0]
            last = " ".join(parts[1:]) if len(parts) > 1 else None
            # Use loose matching provided by repo
            q = user_repo.build_filter(first_name=first, last_name=last, dob=None)
            # Fetch first match
            users = user_repo.find_users(q, limit=1, skip=None)
            if users:
                user = users[0]

    # 3. Validation
    if not user:
        # Only raise error if they actually tried to set a manager
        if manager_id or manager_name:
            identifier = manager_id if manager_id else manager_name
            raise ValueError(f"Hiring Manager '{identifier}' not found.")
        return None, None

    if user.get("role") not in ["Recruiter", "Manager"]:
        raise ValueError(f"User {user.get('firstName')} is not a Manager/Recruiter.")
        
    return user["UserID"], f"{user['firstName']} {user['lastName']}".strip()

# --- READ Operations ---
@query.field("jobs")
def resolve_jobs(obj, info, limit=None, skip=None, company=None, location=None, title=None, posterUserId=None):
    # 1. Build the basic search filter
    q = build_job_filter(company, location, title, posterUserId)
    
    # 2. RBAC: Filter out Closed jobs for Applicants
    user_role = info.context.get("user_role")
    
    # If user is NOT a Recruiter (i.e., Applicant or unauthenticated), hide Closed jobs
    if user_role != "Recruiter" and user_role != "Manager": # Updated to allow Managers to see closed jobs too? Maybe.
        # This matches anything that is NOT "Closed" (includes "Open" and null)
        q["status"] = {"$ne": "Closed"}

    # 3. Execute Query
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
    
    # Get the logged-in recruiter's information
    user_id = info.context.get("UserID")
    user_first_name = info.context.get("firstName", "")
    user_last_name = info.context.get("lastName", "")
    poster_name = f"{user_first_name} {user_last_name}".strip()
    
    # --- Resolve Manager (Pass both ID and Name inputs) ---
    hm_id, hm_name = _resolve_manager_info(
        input.get("hiringManagerId"), 
        input.get("hiringManagerName")
    )
    
    doc = {
        "jobId": next_job_id(),
        "title": title,
        "company": input.get("company"),
        "location": input.get("location"),
        "salaryRange": input.get("salaryRange"),
        "skillsRequired": input.get("skillsRequired", []),
        "description": input.get("description"),
        "postedAt": datetime.utcnow().strftime('%Y-%m-%d'),
        "status": "Open",
        "posterUserId": user_id,
        "posterName": poster_name if poster_name else None,
        "requires_us_citizenship": input.get("requires_us_citizenship", False),
        # --- NEW FIELDS ---
        "hiringManagerId": hm_id,
        "hiringManagerName": hm_name
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
    
    # --- Resolve Manager Update ---
    if "hiringManagerId" in input or "hiringManagerName" in input:
        hm_id, hm_name = _resolve_manager_info(
            input.get("hiringManagerId"), 
            input.get("hiringManagerName")
        )
        set_fields["hiringManagerId"] = hm_id
        set_fields["hiringManagerName"] = hm_name
        
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

@mutation.field("updateJobByFields")
def resolve_update_job_by_fields(obj, info, title, input, company=None):
    # --- AUTHORIZATION CHECK ---
    user_role = info.context.get("user_role")
    if user_role != "Recruiter":
        raise ValueError("Permission denied: You must be a Recruiter to update a job.")

    # Validate the title field in input if provided
    if "title" in input and input["title"] is not None:
        require_non_empty_str(input["title"], "title")

    set_fields = clean_update_input(input)
    
    # --- Resolve Manager Update ---
    if "hiringManagerId" in input or "hiringManagerName" in input:
        hm_id, hm_name = _resolve_manager_info(
            input.get("hiringManagerId"), 
            input.get("hiringManagerName")
        )
        set_fields["hiringManagerId"] = hm_id
        set_fields["hiringManagerName"] = hm_name

    if not set_fields:
        raise ValueError("No fields provided to update.")

    # Build a filter to find the job
    q = build_job_filter(company, None, title)
    
    # --- SAFETY CHECK ---
    # Before updating, find how many jobs match the criteria.
    matching_jobs = find_jobs(q, None, None)
    
    if len(matching_jobs) == 0:
        raise ValueError(f"No job found with title '{title}' at company '{company or 'any company'}'.")
    if len(matching_jobs) > 1:
        raise ValueError("Multiple jobs matched this criteria. Please be more specific or use a Job ID.")
        
    # If exactly one job matches, proceed with update
    updated = update_one_job(q, set_fields)
    if not updated:
        raise ValueError(f"Failed to update job with title '{title}'.")
    return to_job_output(updated)

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