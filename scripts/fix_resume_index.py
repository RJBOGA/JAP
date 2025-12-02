import pymongo
import sys

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "jobtracker"

def repair_resume_indexes():
    print(f"Connecting to {MONGO_URI}...")
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
    except Exception as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        return

    print(f"Repairing collection: resumes")

    # 1. Check existing indexes
    try:
        indexes = list(db.resumes.list_indexes())
        print("Found indexes:", [i['name'] for i in indexes])
    except:
        print("Collection might not exist yet.")

    # 2. Drop the incorrect index
    try:
        db.resumes.drop_index("ResumeID_1")
        print("✅ Dropped incorrect index 'ResumeID_1'.")
    except Exception as e:
        print(f"ℹ️ Could not drop 'ResumeID_1' (it might not exist): {e}")

    # 3. Create the correct index (Optional but recommended)
    try:
        db.resumes.create_index("resumeId", unique=True)
        print("✅ Created correct unique index 'resumeId_1'.")
    except Exception as e:
        print(f"❌ Failed to create new index: {e}")

    # 4. Clean up corrupted data (Optional - removes docs with null resumeId)
    # result = db.resumes.delete_many({"resumeId": {"$exists": False}})
    # print(f"Cleaned up {result.deleted_count} records with missing IDs.")

    print("\n🎉 Repair Complete.")

if __name__ == "__main__":
    repair_resume_indexes()