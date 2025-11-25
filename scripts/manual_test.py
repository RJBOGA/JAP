import requests
import json

API_BASE = "http://localhost:8000"

# Test 1: Charlie Brown -> Interviewing
print("="*70)
print("TEST: Update Charlie to Interviewing")
print("="*70)

mutation = """
mutation {
  updateApplicationStatusByNames(
    userName: "Charlie Brown"
    jobTitle: "Senior Python Developer"
    companyName: "Google"
    newStatus: "Interviewing"
  ) {
    appId
    status
    candidate {
      firstName
      lastName
      email
    }
    job {
      title
      company
    }
  }
}
"""

response = requests.post(
    f"{API_BASE}/graphql",
    json={"query": mutation},
    headers={"X-User-Role": "Recruiter"}
)

result = response.json()
print("\nResponse:")
print(json.dumps(result, indent=2))

if "data" in result and result["data"]["updateApplicationStatusByNames"]:
    print("\n✅ SUCCESS! Email should be sent to:", result["data"]["updateApplicationStatusByNames"]["candidate"]["email"])
