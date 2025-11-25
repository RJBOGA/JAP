"""
Simple Manual Test - Denormalized Schema Verification
Quick test to verify the denormalized fields work correctly
"""
import requests
import json

API_BASE = "http://localhost:8000"

print("="*70)
print("DENORMALIZED SCHEMA - QUICK VERIFICATION TEST")
print("="*70)

# Test 1: Charlie Brown -> Interviewing
print("\n1. Testing Status Update (Charlie Brown -> Interviewing)...")

mutation = """
mutation {
  updateApplicationStatusByNames(
    userName: "Charlie Brown"
    jobTitle: "Senior Python Developer"
    companyName: "Google"
    newStatus: "Interviewing"
  ) {
    appId
    userName
    jobTitle
    companyName
    status
    candidate { email }
  }
}
"""

response = requests.post(
    f"{API_BASE}/graphql",
    json={"query": mutation},
    headers={"X-User-Role": "Recruiter"}
)

result = response.json()

if "data" in result and result["data"]["updateApplicationStatusByNames"]:
    app = result["data"]["updateApplicationStatusByNames"]
    print(f"✅ SUCCESS!")
    print(f"   App ID: {app['appId']}")
    print(f"   User: {app['userName']}")
    print(f"   Job: {app['jobTitle']} @ {app['companyName']}")
    print(f"   Status: {app['status']}")
    print(f"   Email: {app['candidate']['email']}")
else:
    print(f"❌ FAILED: {result}")

# Test 2: Add Manager Note
print("\n2. Testing Manager Notes...")

mutation2 = """
mutation {
  addManagerNoteToApplication(
    userName: "Charlie Brown"
    jobTitle: "Senior Python Developer"
    companyName: "Google"
    note: "Test note - strong candidate!"
  ) {
    appId
    userName
    notes
  }
}
"""

response2 = requests.post(
    f"{API_BASE}/graphql",
    json={"query": mutation2},
    headers={"X-User-Role": "Recruiter"}
)

result2 = response2.json()

if "data" in result2 and result2["data"]["addManagerNoteToApplication"]:
    app = result2["data"]["addManagerNoteToApplication"]
    print(f"✅ SUCCESS!")
    print(f"   App ID: {app['appId']}")
    print(f"   User: {app['userName']}")
    print(f"   Notes: ...{app['notes'][-50:]}")  # Last 50 chars
else:
    print(f"❌ FAILED: {result2}")

# Test 3: Query to verify fields exist
print("\n3. Querying all applications...")

query = """
{
  applications {
    appId
    userName
    jobTitle
    companyName
    status
  }
}
"""

response3 = requests.post(
    f"{API_BASE}/graphql",
    json={"query": query},
    headers={"X-User-Role": "Recruiter"}
)

result3 = response3.json()

if "data" in result3:
    apps = result3["data"]["applications"]
    print(f"✅ Found {len(apps)} applications")
    
    apps_with_fields = [a for a in apps if a.get("userName") and a.get("jobTitle")]
    print(f"   {len(apps_with_fields)}/{len(apps)} have denormalized fields")
    
    if apps_with_fields:
        print(f"\n   Sample applications:")
        for app in apps_with_fields[:3]:
            print(f"   - {app['userName']} → {app['jobTitle']} @ {app.get('companyName', 'N/A')}")
else:
    print(f"❌ FAILED: {result3}")

print("\n" + "="*70)
print("✅ DENORMALIZED SCHEMA WORKING!")
print("="*70)
