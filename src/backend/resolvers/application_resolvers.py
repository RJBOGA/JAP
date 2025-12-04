# src/backend/resolvers/application_resolvers.py
from datetime import datetime
from ariadne import QueryType, MutationType, ObjectType
from ..db import next_application_id, to_application_output, interviews_collection
from ..validators.common_validators import clean_update_input
from ..repository import user_repo, job_repo, application_repo, resume_repo
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
    if not job: return

    for app in other_apps:
        # Added 'Offered' to list of statuses that get rejected when someone else is hired
        if app.get("status") in ["Applied", "Interviewing", "InterviewInviteSent", "Offered"]:
            candidate = user_repo.find_one_by_id(app["userId"])
            if candidate:
                email_service.send_rejection_notification(
                    to_email=candidate["email"], candidate_name=candidate["firstName"],
                    job_title=job["title"], company=job["company"],
                    app_id=app["appId"]
                )
                application_repo.update_one_application({"appId": app["appId"]}, {"status": "Rejected"})
                
    print("Hired status side-effects complete.")

# --- FIELD RESOLVERS ---
@job.field("applicants") 
def resolve_job_applicants(job_obj, info):
    # --- SECURITY CHECK ---
    # If the user is NOT a recruiter, return an empty list or None
    if info.context.get("user_role") != "Recruiter":
        return []
    # ----------------------

    job_id = job_obj.get("jobId")
    if not job_id: return []
    
    # 1. Find all applications for the job
    applications = application_repo.find_applications({"jobId": job_id})
    if not applications: return []
    
    # 2. Get all unique UserIDs
    user_ids = [app.get("userId") for app in applications]
    user_id_to_status = {app.get("userId"): app.get("status") for app in applications} # Map for status lookup
    user_id_to_resume = {app.get("userId"): app.get("resume_url") for app in applications}

    # --- NEW: Fetch Interview Times ---
    interviews = list(interviews_collection().find({
        "jobId": job_id,
        "candidateId": {"$in": user_ids}
    }))
    user_id_to_time = {i.get("candidateId"): i.get("startTime") for i in interviews}
    # ----------------------------------

    if not user_ids: return []
    
    # 3. Fetch User documents
    applicant_docs = user_repo.find_users({"UserID": {"$in": user_ids}}, None, None)
    
    # 4. Attach status and format output
    output_users = []
    for doc in applicant_docs:
        user_output = user_repo.to_user_output(doc)
        # --- NEW: Inject application status into the User object for display ---
        user_output['applicationStatus'] = user_id_to_status.get(doc.get("UserID"), 'Applied') 
        user_output['resume_url'] = user_id_to_resume.get(doc.get("UserID"))
        
        # Inject Interview Time
        user_output['interviewTime'] = user_id_to_time.get(doc.get("UserID")) # <--- ADD THIS
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
    
    # 1. Fetch User and Job
    user = user_repo.find_one_by_id(user_id)
    job = job_repo.find_job_by_id(job_id)

    if not user: raise ValueError(f"Validation failed: User {user_id} not found.")
    if not job: raise ValueError(f"Validation failed: Job {job_id} not found.")
    
    # --- CITIZENSHIP VALIDATION ---
    if job.get("requires_us_citizenship", False):
        user_is_citizen = user.get("is_us_citizen", False)
        if not user_is_citizen:
            raise ValueError(
                "Application Failed: This position strictly requires US Citizenship. "
                "Your profile does not verify this status."
            )
    # ------------------------------

    existing_app = application_repo.find_applications({"userId": user_id, "jobId": job_id})
    if existing_app:
         raise ValueError(f"Duplicate application: You have already applied (AppID: {existing_app[0]['appId']}).")

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

    if not candidate or not job: return to_application_output(updated_app)

    # --- STATUS HANDLING LOGIC ---

    # 1. Interview Invite (FS.2)
    if newStatus == "InterviewInviteSent":
        email_service.send_scheduling_invite_email(
            to_email=candidate["email"], candidate_name=candidate["firstName"],
            job_title=job["title"], company=job["company"],
            app_id=updated_app["appId"] 
        )
    
    # 2. Offer Extended (FS.5 Pre-requisite) - NEW
    elif newStatus == "Offered":
        email_service.send_offer_extension_notification(
            to_email=candidate["email"], candidate_name=candidate["firstName"],
            job_title=job["title"], company=job["company"],
            app_id=updated_app["appId"]
        )

    # 3. Hired (Triggers Job Close)
    elif newStatus.lower() == "hired":
        offer_subject = f"Job Offer for {job['title']} at {job['company']}"
        offer_body = f"<p>Congratulations {candidate['firstName']}, we are delighted to offer you the position!</p>"
        if email_service._send_email(candidate["email"], offer_subject, offer_body): 
            email_service._audit_email_success(updated_app["appId"], "Hired")
        thread = threading.Thread(target=_handle_hired_status_side_effects, args=(job["jobId"], candidate["UserID"]))
        thread.start()

    # 4. Rejected
    elif newStatus.lower() == "rejected":
        email_service.send_rejection_notification(
            to_email=candidate["email"], 
            candidate_name=candidate["firstName"],
            job_title=job["title"], 
            company=job["company"],
            app_id=updated_app["appId"]
        )
    
    # Legacy Interviewing status handling...
    elif newStatus.lower().startswith("interview") and newStatus != "InterviewInviteSent":
         email_service.send_interview_invitation(
            to_email=candidate["email"], candidate_name=candidate["firstName"],
            job_title=job["title"], company=job["company"],
            app_id=updated_app["appId"] 
        )

    return to_application_output(updated_app)

# --- NEW MUTATION: REJECT OFFER (FS.5) ---
@mutation.field("acceptOffer")
def resolve_accept_offer(obj, info, jobTitle, companyName=None):
    user_id = info.context.get("UserID")
    if not user_id: raise PermissionError("You must be logged in.")
    
    # 1. Find Job
    job_filter = job_repo.build_job_filter(companyName, None, jobTitle)
    jobs = job_repo.find_jobs(job_filter, None, None)
    if not jobs: raise ValueError(f"Job '{jobTitle}' not found.")
    job = jobs[0]
    
    # 2. Find Application owned by User
    app_filter = {"userId": user_id, "jobId": job["jobId"]}
    apps = application_repo.find_applications(app_filter)
    if not apps: raise ValueError("Application not found.")
    app = apps[0]
    
    # 3. Status Validation
    if app["status"] != "Offered":
        raise ValueError(f"Cannot accept offer: Current status is '{app['status']}', not 'Offered'.")
        
    # 4. Update to Hired
    updated_app = application_repo.update_one_application({"appId": app["appId"]}, {"status": "Hired"})
    
    # 5. Notify Manager
    manager_id = job.get("hiringManagerId") or job.get("posterUserId")
    if manager_id:
        manager = user_repo.find_one_by_id(manager_id)
        candidate = user_repo.find_one_by_id(user_id)
        if manager and candidate:
            manager_name = f"{manager['firstName']} {manager['lastName']}"
            candidate_name = f"{candidate['firstName']} {candidate['lastName']}"
            email_service.send_offer_acceptance_notification(
                to_email=manager["email"],
                manager_name=manager_name,
                candidate_name=candidate_name,
                job_title=job["title"],
                app_id=app["appId"]
            )

    # 6. Trigger System Side-Effects (Close Job, Reject Others)
    thread = threading.Thread(target=_handle_hired_status_side_effects, args=(job["jobId"], user_id))
    thread.start()
    
    return to_application_output(updated_app)

@mutation.field("rejectOffer")
def resolve_reject_offer(obj, info, jobTitle, companyName=None):
    user_id = info.context.get("UserID")
    if not user_id: raise PermissionError("You must be logged in.")
    
    # 1. Find Job
    job_filter = job_repo.build_job_filter(companyName, None, jobTitle)
    jobs = job_repo.find_jobs(job_filter, None, None)
    if not jobs: raise ValueError(f"Job '{jobTitle}' not found.")
    job = jobs[0]
    
    # 2. Find Application owned by User
    app_filter = {"userId": user_id, "jobId": job["jobId"]}
    apps = application_repo.find_applications(app_filter)
    if not apps: raise ValueError("Application not found.")
    app = apps[0]
    
    # 3. Status Validation
    # Allow rejecting even if 'Hired' (reverting decision)
    if app["status"] not in ["Offered", "Hired"]:
        raise ValueError(f"Cannot reject offer: Current status is '{app['status']}', not 'Offered' or 'Hired'.")
        
    # 4. Update Status
    updated_app = application_repo.update_one_application({"appId": app["appId"]}, {"status": "Offer Rejected"})
    
    # 5. Notify Manager
    # Use Hiring Manager if assigned, otherwise Poster (Recruiter)
    manager_id = job.get("hiringManagerId") or job.get("posterUserId")
    if manager_id:
        manager = user_repo.find_one_by_id(manager_id)
        candidate = user_repo.find_one_by_id(user_id)
        if manager and candidate:
            manager_name = f"{manager['firstName']} {manager['lastName']}"
            candidate_name = f"{candidate['firstName']} {candidate['lastName']}"
            email_service.send_offer_rejection_notification(
                to_email=manager["email"],
                manager_name=manager_name,
                candidate_name=candidate_name,
                job_title=job["title"],
                app_id=app["appId"]
            )
            
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

@mutation.field("applyWithResume")
def resolve_apply_with_resume(obj, info, userName, jobTitle, resumeId, companyName=None):
    from ..repository import user_repo, job_repo, application_repo
    
    name_parts = userName.strip().split()
    first_name = name_parts[0]
    
    user_filter = user_repo.build_filter(first_name, None, None, None)
    matching_users = user_repo.find_users(user_filter, None, None)
    if not matching_users: raise ValueError("User not found")
    user = matching_users[0]
    
    job_filter = job_repo.build_job_filter(companyName, None, jobTitle)
    matching_jobs = job_repo.find_jobs(job_filter, None, None)
    if not matching_jobs: raise ValueError("Job not found")
    job = matching_jobs[0]
    
    resume = resume_repo.find_resume_by_id(resumeId)
    if not resume: raise ValueError(f"Resume {resumeId} not found.")
    if resume["userId"] != user["UserID"]: raise ValueError("You do not own this resume.")
    
    app_input = {
        "userId": user["UserID"],
        "jobId": job["jobId"],
        "userName": userName,
        "jobTitle": jobTitle,
        "companyName": companyName
    }
    
    new_app = resolve_create_application(None, info, input=app_input)
    
    application_repo.update_one_application(
        {"appId": new_app["appId"]},
        {
            "resume_url": resume["url"],
            "notes": f"Applied using specific resume: {resume.get('filename')}"
        }
    )
    
    updated_app = application_repo.find_application_by_id(new_app["appId"])
    return to_application_output(updated_app)

# --- Ensure correct Query object is exposed for ariadne schema build ---
@query.field("applicationById")
def resolve_application_by_id(*_, appId):
    doc = application_repo.find_application_by_id(int(appId))
    if not doc: raise ValueError(f"Application with ID {appId} not found.")
    return to_application_output(doc)