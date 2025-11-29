from datetime import datetime, timedelta, time
from ..repository import user_repo, job_repo
from ..db import schedules_collection, interviews_collection, next_interview_id
from ..repository.application_repo import update_one_application

# --- Public Service Functions ---

def set_recruiter_availability(recruiter_id: int, availability_data: list):
	"""Creates or replaces the availability schedule for a given recruiter."""
	# Basic validation (ensures fields exist)
	for slot in availability_data:
		if not all(k in slot for k in ['dayOfWeek', 'startTime', 'endTime']):
			raise ValueError("Each availability slot must contain dayOfWeek, startTime, and endTime.")
    
	schedules_collection().update_one(
		{"recruiterId": recruiter_id},
		{"$set": {"availability": availability_data, "recruiterId": recruiter_id}},
		upsert=True
	)
	return True

def find_open_slots(recruiter_id: int, candidate_id: int, start_date: datetime, end_date: datetime, duration_minutes: int = 30):
	"""
	The core conflict-resolution algorithm.
	Finds available interview slots for a recruiter and a candidate within a date range.
	"""
	# 1. Get the recruiter's general weekly availability
	schedule = schedules_collection().find_one({"recruiterId": recruiter_id})
	if not schedule or not schedule.get("availability"):
		return [] # Recruiter has not set their availability

	# 2. Get all existing interviews for BOTH the recruiter and the candidate
	# NOTE: MongoDB ISO 8601 strings are sortable and comparable
	booked_interviews = list(interviews_collection().find({
		"$or": [{"recruiterId": recruiter_id}, {"candidateId": candidate_id}],
		"startTime": {"$gte": start_date.isoformat()},
		"endTime": {"$lte": end_date.isoformat()}
	}))
    
	booked_slots = set()
	for interview in booked_interviews:
		# Convert booked slots to datetime objects for accurate comparison
		start = datetime.fromisoformat(interview["startTime"])
		end = datetime.fromisoformat(interview["endTime"])
		booked_slots.add((start, end))

	# 3. Iterate through each day in the date range and generate potential slots
	open_slots = []
	day_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
    
	current_date = start_date
	while current_date <= end_date:
		day_of_week = day_map[current_date.weekday()]
        
		# Find if the recruiter is available on this day of the week
		for avail_slot in schedule["availability"]:
			if avail_slot["dayOfWeek"].lower() == day_of_week.lower():
                
				# Combine current_date with time component from availability slot
				slot_start_time = datetime.strptime(avail_slot["startTime"], "%H:%M").time()
				slot_end_time = datetime.strptime(avail_slot["endTime"], "%H:%M").time()

				potential_start = datetime.combine(current_date.date(), slot_start_time)
				potential_end_limit = datetime.combine(current_date.date(), slot_end_time)
                
				while (potential_start + timedelta(minutes=duration_minutes)) <= potential_end_limit:
					potential_end = potential_start + timedelta(minutes=duration_minutes)
                    
					# 4. Check for conflicts
					is_conflict = False
					for booked_start, booked_end in booked_slots:
						# Check for overlap: (StartA < EndB) and (EndA > StartB)
						if (potential_start < booked_end) and (potential_end > booked_start):
							is_conflict = True
							break
                    
					if not is_conflict:
						# Return in ISO format for consistency
						open_slots.append(potential_start.isoformat())
                        
					potential_start += timedelta(minutes=duration_minutes)
        
		current_date += timedelta(days=1)
        
	return open_slots

def book_interview(job_id: int, candidate_id: int, recruiter_id: int, start_time: datetime, end_time: datetime):
	"""Books a new interview after a final conflict check."""
    
	# Final conflict check right before booking
	conflicts = list(interviews_collection().find({
		"$or": [{"recruiterId": recruiter_id}, {"candidateId": candidate_id}],
		"startTime": {"$lt": end_time.isoformat()},
		"endTime": {"$gt": start_time.isoformat()}
	}))

	if conflicts:
		raise ValueError("Conflict detected. This time slot is no longer available.")
        
	interview_doc = {
		"interviewId": next_interview_id(),
		"jobId": job_id,
		"candidateId": candidate_id,
		"recruiterId": recruiter_id,
		"startTime": start_time.isoformat(),
		"endTime": end_time.isoformat()
	}
    
	interviews_collection().insert_one(interview_doc)
    
	# Update application status to Interviewing/Scheduled
	app_query = {"userId": candidate_id, "jobId": job_id}
	update_one_application(app_query, {"status": "Interviewing"})
    
	# You would also trigger the email here, but we will leave the full logic 
	# out of the service layer for now to avoid dependency cycles.
    
	return interview_doc