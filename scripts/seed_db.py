# scripts/seed_db.py
import os
import sys
import bcrypt
from datetime import datetime
from faker import Faker

# --- Setup Project Path ---
# This allows the script to import modules from the 'src' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import our backend modules
from src.backend.db import get_db, next_user_id, next_job_id
from src.backend.models.user_models import UserProfileType

# Initialize Faker to generate realistic data
fake = Faker()

def seed_database():
    """
    Clears and populates the database with sample users and jobs.
    """
    print("Connecting to the database...")
    db = get_db()
    
    # --- 1. Clear Existing Data ---
    print("Clearing existing collections (users, jobs, applications)...")
    db["users"].delete_many({})
    db["jobs"].delete_many({})
    db["applications"].delete_many({})
    
    # --- 2. Create Sample Users ---
    print("Creating sample users...")
    users_to_create = [
        # --- RECRUITERS ---
        {
            "UserID": next_user_id(), "email": "recruiter@google.com", "password": "password123",
            "firstName": "Alice", "lastName": "Jones", "role": UserProfileType.RECRUITER.value,
            "professionalTitle": "Senior Technical Recruiter", "createdAt": datetime.utcnow().isoformat(),
            # All other fields are null by default
        },
        {
            "UserID": next_user_id(), "email": "hiring@figma.com", "password": "password123",
            "firstName": "Bob", "lastName": "Smith", "role": UserProfileType.RECRUITER.value,
            "professionalTitle": "Hiring Manager", "createdAt": datetime.utcnow().isoformat(),
        },
        # --- APPLICANTS ---
        {
            "UserID": next_user_id(), "email": "applicant1@email.com", "password": "password123",
            "firstName": "Charlie", "lastName": "Brown", "role": UserProfileType.APPLICANT.value,
            "professionalTitle": "Software Engineer", "years_of_experience": 5,
            "skills": ["Python", "Flask", "React", "MongoDB"], "city": "San Francisco", "country": "USA",
            "linkedin_profile": "https://linkedin.com/in/charliebrown", "createdAt": datetime.utcnow().isoformat(),
        },
        {
            "UserID": next_user_id(), "email": "applicant2@email.com", "password": "password123",
            "firstName": "Diana", "lastName": "Prince", "role": UserProfileType.APPLICANT.value,
            "professionalTitle": "Product Manager", "years_of_experience": 8,
            "skills": ["Agile", "Product Strategy", "AI"], "city": "New York", "country": "USA",
            "linkedin_profile": "https://linkedin.com/in/dianaprince", "createdAt": datetime.utcnow().isoformat(),
        },
        {
            "UserID": next_user_id(), "email": "applicant3@email.com", "password": "password123",
            "firstName": "Ethan", "lastName": "Hunt", "role": UserProfileType.APPLICANT.value,
            "professionalTitle": "Data Scientist", "years_of_experience": 4,
            "skills": ["SQL", "Python", "Machine Learning", "PyTorch"], "city": "London", "country": "UK",
             "linkedin_profile": "https://linkedin.com/in/ethanhunt", "createdAt": datetime.utcnow().isoformat(),
        },
    ]

    for user_data in users_to_create:
        # Securely hash the password before insertion
        password = user_data.pop("password").encode('utf-8')
        user_data["password"] = bcrypt.hashpw(password, bcrypt.gensalt())
        
        # Initialize remaining fields to None if they don't exist
        user_model_fields = [
            "phone_number", "city", "state_province", "country", "linkedin_profile",
            "portfolio_url", "highest_qualification", "years_of_experience",
            "dob", "skills", "professionalTitle"
        ]
        for field in user_model_fields:
            if field not in user_data:
                user_data[field] = None
        
        db["users"].insert_one(user_data)
    print(f"  -> Successfully created {len(users_to_create)} users.")

    # --- 3. Create Sample Jobs ---
    print("Creating sample jobs...")
    jobs_to_create = [
        {
            "jobId": next_job_id(), "title": "Senior Python Developer", "company": "Google",
            "location": "Mountain View, CA", "skillsRequired": ["Python", "Django", "AWS", "Kubernetes"],
            "description": "Seeking an experienced backend developer to join our cloud infrastructure team.",
            "postedAt": datetime.utcnow().strftime('%Y-%m-%d')
        },
        {
            "jobId": next_job_id(), "title": "Senior UI/UX Designer", "company": "Figma",
            "location": "San Francisco, CA", "skillsRequired": ["Figma", "Prototyping", "User Research"],
            "description": "Design the future of collaborative tools with a world-class team.",
            "postedAt": datetime.utcnow().strftime('%Y-%m-%d')
        },
        {
            "jobId": next_job_id(), "title": "Product Manager, AI", "company": "Microsoft",
            "location": "Redmond, WA", "skillsRequired": ["Product Strategy", "Agile", "AI", "Machine Learning"],
            "description": "Lead the development of our next-generation AI Copilot features.",
            "postedAt": datetime.utcnow().strftime('%Y-%m-%d')
        },
        {
            "jobId": next_job_id(), "title": "Data Scientist", "company": "Netflix",
            "location": "Los Gatos, CA", "skillsRequired": ["SQL", "Python", "Machine Learning", "Statistics"],
            "description": "Analyze viewer data to drive content strategy and personalization algorithms.",
            "postedAt": datetime.utcnow().strftime('%Y-%m-%d')
        },
        {
            "jobId": next_job_id(), "title": "Frontend Engineer (React)", "company": "Vercel",
            "location": "Remote", "skillsRequired": ["React", "Next.js", "TypeScript", "CSS-in-JS"],
            "description": "Build beautiful and performant web experiences for a global audience.",
            "postedAt": datetime.utcnow().strftime('%Y-%m-%d')
        },
    ]
    db["jobs"].insert_many(jobs_to_create)
    print(f"  -> Successfully created {len(jobs_to_create)} jobs.")

    print("\n--- Seeding Complete! ---")
    print("You can now log in with the following test accounts:")
    print("  Recruiters:")
    print("    - Email: recruiter@google.com (Password: password123)")
    print("    - Email: hiring@figma.com (Password: password123)")
    print("  Applicants:")
    print("    - Email: applicant1@email.com (Password: password123)")
    print("    - Email: applicant2@email.com (Password: password123)")
    print("    - Email: applicant3@email.com (Password: password123)")
    print("-------------------------")

if __name__ == "__main__":
    seed_database()