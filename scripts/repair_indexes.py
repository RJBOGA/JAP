import pymongo
import sys

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "jobtracker"

def repair():
    print(f"Connecting to {MONGO_URI}...")
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
    except Exception as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        return

    print(f"Repairing database: {DB_NAME}")

    # 1. Drop the corrupted 'interviews' collection
    # This deletes the bad 'InterviewID_1' index
    print("1. Dropping 'interviews' collection to clear bad indexes...")
    db.interviews.drop()
    print("   ✅ Collection dropped.")

    # 2. Create the correct Unique Index on 'interviewId' (lowercase 'i')
    print("2. Creating correct index on 'interviewId'...")
    try:
        db.interviews.create_index("interviewId", unique=True)
        print("   ✅ Index 'interviewId_1' created.")
    except Exception as e:
        print(f"   ❌ Failed to create index: {e}")

    # 3. Create the Double-Booking Protection Index
    print("3. Creating double-booking protection...")
    try:
        db.interviews.create_index([("recruiterId", 1), ("startTime", 1)], unique=True)
        print("   ✅ Index 'recruiterId_1_startTime_1' created.")
    except Exception as e:
        print(f"   ❌ Failed to create index: {e}")

    print("\n🎉 REPAIR COMPLETE. You can now restart your backend.")

if __name__ == "__main__":
    repair()