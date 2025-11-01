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
)
from ..db import next_job_id

# Create separate QueryType and MutationType instances
# We will combine these with the user resolvers in app.py
query = QueryType()
mutation = MutationType()

@query.field("jobs")
def resolve_jobs(*_, limit=None, skip=None, company=None, location=None, title=None):
    q = build_job_filter(company, location, title)
    docs = find_jobs(q, skip, limit)
    return [to_job_output(d) for d in docs]

@query.field("jobById")
def resolve_job_by_id(*_, jobId):
    doc = find_job_by_id(int(jobId))
    if not doc:
        raise ValueError(f"Job with ID {jobId} not found.")
    return to_job_output(doc)

@mutation.field("createJob")
def resolve_create_job(*_, input):
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
def resolve_update_job(*_, jobId, input):
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
def resolve_delete_job(*_, jobId):
    count = delete_one_job({"jobId": int(jobId)})
    if count == 0:
        raise ValueError(f"Job with ID {jobId} not found for deletion.")
    return True