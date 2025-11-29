import os
import sys
from datetime import datetime, timedelta
import traceback
from pprint import pprint

# Ensure project root is on sys.path (same approach as other scripts)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backend.services import scheduling_service
from src.backend.db import applications_collection, schedules_collection, users_collection, jobs_collection, next_application_id


def main():
    try:
        app = applications_collection().find_one()
        if not app:
            print("No application found in DB. Creating a test application...")
            # Find a job and an applicant user to create a minimal application
            job = jobs_collection().find_one()
            applicant = users_collection().find_one({"role": "Applicant"})
            if not job or not applicant:
                print("Could not find a job or an applicant user to create a test application. Aborting.")
                return
            job_id = job.get("jobId")
            candidate_id = applicant.get("UserID")
            app_doc = {
                "appId": next_application_id(),
                "userId": candidate_id,
                "jobId": job_id,
                "status": "Applied",
                "submittedAt": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "notes": "",
                "userName": f"{applicant.get('firstName')} {applicant.get('lastName')}",
                "jobTitle": job.get('title'),
                "companyName": job.get('company')
            }
            applications_collection().insert_one(app_doc)
            app = app_doc
        else:
            job_id = app.get("jobId")
            candidate_id = app.get("userId")

        sched = schedules_collection().find_one()
        if not sched:
            print("No recruiter schedules found. Creating a simple schedule for an available recruiter...")
            recruiter = users_collection().find_one({"role": "Recruiter"})
            if not recruiter:
                print("No recruiter user found to create a schedule. Aborting.")
                return
            recruiter_id = recruiter.get("UserID")
            schedules_collection().insert_one({
                "recruiterId": recruiter_id,
                "availability": [
                    {"dayOfWeek": "Monday", "startTime": "09:00", "endTime": "17:00"},
                    {"dayOfWeek": "Tuesday", "startTime": "09:00", "endTime": "17:00"}
                ]
            })
            sched = schedules_collection().find_one({"recruiterId": recruiter_id})
        recruiter_id = sched.get("recruiterId")

        print(f"Found application: appId={app.get('appId')}, jobId={job_id}, candidateId={candidate_id}")
        print(f"Found recruiter schedule for recruiterId={recruiter_id}")

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=7)

        print("Searching for open slots (next 7 days)...")
        open_slots = scheduling_service.find_open_slots(recruiter_id, candidate_id, start_date, end_date, duration_minutes=30)
        print(f"Open slots found: {len(open_slots)}")
        if not open_slots:
            print("No open slots available to book.")
            return

        # Pick the first available slot and book
        slot_iso = open_slots[0]
        start_time = datetime.fromisoformat(slot_iso)
        end_time = start_time + timedelta(minutes=30)

        print(f"Attempting to book interview at {start_time.isoformat()} - {end_time.isoformat()}")
        interview = scheduling_service.book_interview(job_id, candidate_id, recruiter_id, start_time, end_time)
        print("Interview booked:")
        pprint(interview)

    except Exception as e:
        print("Exception during smoke test:")
        traceback.print_exc()

if __name__ == '__main__':
    main()
