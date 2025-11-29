# src/backend/resolvers/application_resolvers.py
from datetime import datetime
from ariadne import QueryType, MutationType, ObjectType
from ..db import next_application_id, to_application_output
from ..validators.common_validators import clean_update_input
from ..repository import user_repo, job_repo, application_repo
from ..services import email_service
import threading
import logging # <-- NEW IMPORT

logger = logging.getLogger(__name__) # <-- NEW LOGGER INSTANCE

query = QueryType()
mutation = MutationType()
application = ObjectType("Application")
job = ObjectType("Job")

# --- CORE WORKFLOW HELPER FUNCTIONS ---

def _handle_hired_status_side_effects(job_id, hired_user_id):
    """
    This function runs in a background thread to:
    1. Close the job.
    2. Notify all other unsuccessful applicants.
    """
    print(f"Triggering side-effects for hired status on job {job_id}...")
    job_repo.update_one_job({"jobId": job_id}, {"status": "Closed"})
    
    # Find all other applications for this job (excluding the hired user)
    other_apps = application_repo.find_applications({"jobId": job_id, "userId": {"$ne": hired_user_id}})
    job = job_repo.find_job_by_id(job_id)
    if not job: 
        print(f"ERROR: Could not find job {job_id} for rejection emails.")
        return

    for app in other_apps:
        # Only notify if status is Applied or Interviewing (i.e., not already Rejected)
        if app.get("status") in ["Applied", "Interviewing"]:
            candidate = user_repo.find_one_by_id(app["userId"])
            if candidate:
                email_service.send_rejection_notification(
                    to_email=candidate["email"], candidate_name=candidate["firstName"],
                    job_title=job["title"], company=job["company"],
                    app_id=app["appId"] # Correctly passes app_id
                )
                # OPTIONAL: Mark them as Rejected so they don't get processed again
                application_repo.update_one_application({"appId": app["appId"]}, {"status": "Rejected"})
                
    print("Hired status side-effects complete. Job is Closed, mass rejections sent.")

# --- FIELD RESOLVERS ---
@job.field("applicants") 
def resolve_job_applicants(job_obj, info):
    job_id = job_obj.get("jobId")
    if not job_id: return []
    
    # 1. Find all applications for the job
    applications = application_repo.find_applications({"jobId": job_id})
    if not applications: return []
    
    # 2. Get all unique UserIDs
    user_ids = [app.get("userId") for app in applications]
    user_id_to_status = {app.get("userId"): app.get("status") for app in applications} # Map for status lookup
    if not user_ids: return []
    
    # 3. Fetch User documents
    applicant_docs = user_repo.find_users({"UserID": {"$in": user_ids}}, None, None)
    
    # 4. Attach status and format output
    output_users = []
    for doc in applicant_docs:
        user_output = user_repo.to_user_output(doc)
        # --- NEW: Inject application status into the User object for display ---
        user_output['applicationStatus'] = user_id_to_status.get(doc.get("UserID"), 'Applied') 
        output_users.append(user_output)
        
    return output_users # Now each User object has an 'applicationStatus' field
    
@job.field("applicationCount")
def resolve_job_application_count(job_obj, info):
    job_id = job_obj.get("jobId")
    if not job_id: return 0
    return application_repo.count_applications({"jobId": job_id})

@query.field("applications")
def resolve_applications(obj, info, userId=None, jobId=None, status=None):
    q = {}
    # Security: If Applicant is requesting, restrict to their ID unless an ID is explicitly passed
    if info.context.get("user_role") == "Applicant" and not userId:
        userId = info.context.get("UserID")
    
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
    return user_repo.to_user_output(user_repo.find_one_by_id(app_obj.get("userId")))

@application.field("job")
def resolve_application_job(app_obj, _):
    return job_repo.to_job_output(job_repo.find_job_by_id(app_obj.get("jobId")))

# --- MUTATIONS ---

@mutation.field("createApplication")
def resolve_create_application(*_, input):
    user_id, job_id = input.get("userId"), input.get("jobId")
    if not user_repo.find_one_by_id(user_id): raise ValueError(f"Validation failed: User with ID {user_id} does not exist.")
    if not job_repo.find_job_by_id(job_id): raise ValueError(f"Validation failed: Job with ID {job_id} does not exist.")
    
    # Check for duplicate application
    existing_app = application_repo.find_applications({"userId": user_id, "jobId": job_id})
    if existing_app:
         raise ValueError(f"Duplicate application: This user has already applied to this job (AppID: {existing_app[0]['appId']}).")

    doc = {
        "appId": next_application_id(), "userId": user_id, "jobId": job_id,
        "status": "Applied", "submittedAt": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "notes": input.get("notes"),
        # Denormalized fields are passed from resolve_apply and correctly inserted
        "userName": input.get("userName"),
        "jobTitle": input.get("jobTitle"),
        "companyName": input.get("companyName"),
    }
    application_repo.insert_application(doc)
    return to_application_output(doc)

@mutation.field("apply")
def resolve_apply(obj, info, userName, jobTitle, companyName=None):
    name_parts = userName.strip().split()
    first_name, last_name = (name_parts[0], " ".join(name_parts[1:])) if len(name_parts) > 1 else (name_parts[0], None)
    if not first_name: raise ValueError("User name cannot be empty.")

    # 1. FIND USER
    user_filter = user_repo.build_filter(first_name, last_name, None, None)
    matching_users = user_repo.find_users(user_filter, None, None)
    if len(matching_users) == 0: raise ValueError(f"Could not find a user named '{userName}'.")
    if len(matching_users) > 1: raise ValueError(f"Found multiple users named '{userName}'. Please be more specific.")
    user = matching_users[0]
    
    # 2. FIND JOB
    job_filter = job_repo.build_job_filter(companyName, None, jobTitle)
    matching_jobs = job_repo.find_jobs(job_filter, None, None)
    if len(matching_jobs) == 0: raise ValueError(f"Could not find a job with title '{jobTitle}' at company '{companyName or ''}'.")
    if len(matching_jobs) > 1: raise ValueError(f"Found multiple jobs with title '{jobTitle}'. Please specify a company.")
    job = matching_jobs[0]

    # 3. BUILD AND PASS DENORMALIZED INPUT
    application_input = {
        "userId": user["UserID"], 
        "jobId": job["jobId"],
        "userName": f"{user['firstName']} {user['lastName']}".strip(), 
        "jobTitle": job["title"],                                     
        "companyName": job["company"]                                 
    }
    return resolve_create_application(None, info, input=application_input)

@mutation.field("updateApplication")
def resolve_update_application(obj, info, appId, input):
    set_fields = clean_update_input(input)
    if not set_fields: raise ValueError("No fields provided to update.")
    updated = application_repo.update_one_application({"appId": int(appId)}, set_fields)
    if not updated: raise ValueError(f"Application with ID {appId} not found for update.")
    return to_application_output(updated)

@mutation.field("updateApplicationStatusByNames")
def resolve_update_application_status_by_names(obj, info, userName, jobTitle, newStatus, companyName=None):
    # --- AUTHORIZATION ---
    user_role = info.context.get("user_role")
    if user_role != "Recruiter": 
        logger.warning(f"Permission denied: Non-Recruiter attempted status update for {userName}")
        raise ValueError("Permission denied: You must be a Recruiter to update an application.")
    
    # --- FIND THE SINGLE TARGET APPLICATION ---
    application_filter = {"userName": userName, "jobTitle": jobTitle}
    if companyName: application_filter["companyName"] = companyName
    
    apps = application_repo.find_applications(application_filter)
    if not apps: 
        logger.warning(f"Application not found for {userName} at {jobTitle} ({companyName or 'any'}).")
        raise ValueError(f"No application found for '{userName}' at job '{jobTitle}' at company '{companyName or ''}'.")
    if len(apps) > 1: 
        logger.warning(f"Ambiguous application update for {userName} at {jobTitle}. Matches: {len(apps)}")
        raise ValueError("Found multiple matching applications. Please be more specific.")
    
    target_app_id = apps[0]["appId"]
    logger.debug(f"DEBUG_A: Found application {target_app_id}. Status being set to '{newStatus}'")

    # --- UPDATE STATUS ---
    updated_app = application_repo.update_one_application({"appId": target_app_id}, {"status": newStatus})
    if not updated_app: 
        logger.error(f"Failed to update application {target_app_id} status to {newStatus}.")
        raise ValueError("Failed to update application status.")

    logger.debug("DEBUG_B: Status successfully updated in DB.")

    # --- TRIGGER SIDE-EFFECTS (Email, Job Closure) ---
    candidate = user_repo.find_one_by_id(updated_app["userId"])
    job = job_repo.find_job_by_id(updated_app["jobId"])

    # --- FIX: Use .lower().startswith('interview') for safety ---
    if newStatus.lower().startswith("interview") and candidate and job:
        logger.debug("DEBUG_C: Initiating send_interview_invitation.")
        email_service.send_interview_invitation(
            to_email=candidate["email"], candidate_name=candidate["firstName"],
            job_title=job["title"], company=job["company"],
            app_id=updated_app["appId"] 
        )
    
    if newStatus.lower() == "hired" and candidate and job: # <-- FIX: Checking for 'hired' (long form)
        # Send confirmation/offer email to the hired candidate and audit success
        offer_subject = f"Job Offer for {job['title']} at {job['company']}"
        offer_body = f"<p>Congratulations {candidate['firstName']}, we are delighted to offer you the position!</p><p>Details will follow shortly.</p>"
        
        # We call the internal helper directly to send the email and audit
        if email_service._send_email(candidate["email"], offer_subject, offer_body): 
            email_service._audit_email_success(updated_app["appId"], "Hired")

        logger.debug("DEBUG_D: Starting background thread for mass rejection.")
        thread = threading.Thread(target=_handle_hired_status_side_effects, args=(job["jobId"], candidate["UserID"]))
        thread.start()
    logger.debug(f"DEBUG_D: Final resolver output for App {target_app_id}.")
    return to_application_output(updated_app)

@mutation.field("addNoteToApplicationByJob")
def resolve_add_note_to_application_by_job(obj, info, jobTitle, note, companyName=None):
    # --- AUTHORIZATION (Implicit Applicant) ---
    user_id = info.context.get("UserID")
    if not user_id: raise ValueError("Permission denied: You must be logged in to add a note.")
    
    # 1. FIND JOB
    job_filter = job_repo.build_job_filter(companyName, None, jobTitle)
    jobs = job_repo.find_jobs(job_filter, None, None)
    if not jobs: raise ValueError(f"Could not find job with title '{jobTitle}'.")
    if len(jobs) > 1: raise ValueError(f"Found multiple jobs with title '{jobTitle}'. Please specify a company.")

    # 2. FIND APPLICANT'S APPLICATION
    application_filter = {"userId": user_id, "jobId": jobs[0]["jobId"]}
    apps = application_repo.find_applications(application_filter)
    if not apps: raise ValueError(f"You have not applied for the '{jobTitle}' job.")
    
    target_app_id = apps[0]["appId"]
    
    # 3. APPEND NOTE
    existing_notes = apps[0].get("notes", "") or ""
    # Applicant notes are simply appended, without a timestamp prefix
    updated_notes = f"{existing_notes}\n{note}".strip() 

    updated_app = application_repo.update_one_application({"appId": target_app_id}, {"notes": updated_notes})
    if not updated_app: raise ValueError("Failed to add note.")
    return to_application_output(updated_app)

@mutation.field("addManagerNoteToApplication")
def resolve_add_manager_note_to_application(obj, info, userName, jobTitle, note, companyName=None):
    # --- AUTHORIZATION ---
    user_role = info.context.get("user_role")
    if user_role != "Recruiter": raise ValueError("Permission denied: You must be a Recruiter to add a note.")
    
    # --- FIND THE SINGLE TARGET APPLICATION ---
    application_filter = {"userName": userName, "jobTitle": jobTitle}
    if companyName: application_filter["companyName"] = companyName

    apps = application_repo.find_applications(application_filter)
    if not apps: raise ValueError(f"No application found for user '{userName}' at job '{jobTitle}'.")
    if len(apps) > 1: raise ValueError("Found multiple matching applications. Please be more specific.")
    
    target_app_id = apps[0]["appId"]
    # --- END FIND LOGIC ---
    
    # --- APPEND NOTE ---
    existing_notes = apps[0].get("notes", "") or ""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d')
    new_note = f"\n--- Recruiter Note ({timestamp}): {note}"
    updated_notes = existing_notes.strip() + new_note

    updated_app = application_repo.update_one_application({"appId": target_app_id}, {"notes": updated_notes})
    if not updated_app: raise ValueError("Failed to add note.")
    return to_application_output(updated_app)

# --- Ensure correct Query object is exposed for ariadne schema build ---
@query.field("applicationById")
def resolve_application_by_id(*_, appId):
    doc = application_repo.find_application_by_id(int(appId))
    if not doc: raise ValueError(f"Application with ID {appId} not found.")
    return to_application_output(doc)