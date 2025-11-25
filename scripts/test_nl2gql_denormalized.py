"""
Test Natural Language Understanding with Denormalized Fields
Verifies the AI can extract userName, jobTitle, companyName from natural language
"""
import requests
import json

API_BASE = "http://localhost:8000"

print("="*70)
print("NATURAL LANGUAGE - DENORMALIZED FIELDS TEST")
print("="*70)

test_queries = [
    {
        "name": "Interview with full details",
        "query": "Interview Charlie Brown for the Senior Python Developer position at Google",
        "expected_mutation": "updateApplicationStatusByNames",
        "expected_fields": {
            "userName": "Charlie Brown",
            "jobTitle": "Senior Python Developer",
            "companyName": "Google"
        }
    },
    {
        "name": "Add manager note",
        "query": "Add a note to Diana Prince's Product Manager application at Meta saying she was excellent",
        "expected_mutation": "addManagerNoteToApplication",
        "expected_fields": {
            "userName": "Diana Prince",
            "jobTitle": "Product Manager",
            "companyName": "Meta"
        }
    },
    {
        "name": "Apply to job",
        "query": "Apply Test User to the Test Engineer job at TestCorp",
        "expected_mutation": "apply",
        "expected_fields": {
            "userName": "Test User",
            "jobTitle": "Test Engineer",
            "companyName": "TestCorp"
        }
    },
    {
        "name": "Hire candidate",
        "query": "Hire Ethan Hunt for Data Scientist at Netflix",
        "expected_mutation": "updateApplicationStatusByNames",
        "expected_fields": {
            "userName": "Ethan Hunt",
            "jobTitle": "Data Scientist",
            "companyName": "Netflix",
            "newStatus": "Hired"
        }
    }
]

for i, test in enumerate(test_queries, 1):
    print(f"\n{i}. {test['name']}")
    print(f"   Query: \"{test['query']}\"")
    
    response = requests.post(
        f"{API_BASE}/nl2gql?run=false",  # Don't run, just generate
        json={"query": test["query"]},
        headers={"X-User-Role": "Recruiter"}
    )
    
    if response.status_code == 200:
        result = response.json()
        graphql = result.get("graphql", "")
        
        # Check if correct mutation
        has_mutation = test["expected_mutation"] in graphql
        
        # Check if all expected fields are present
        all_fields_present = all(
            field in graphql and value in graphql
            for field, value in test["expected_fields"].items()
        )
        
        if has_mutation and all_fields_present:
            print(f"   ✅ PASS - Correct mutation and fields extracted")
            print(f"   Generated: {graphql[:80]}...")
        else:
            print(f"   ❌ FAIL")
            print(f"   Expected mutation: {test['expected_mutation']}")
            print(f"   Expected fields: {test['expected_fields']}")
            print(f"   Got: {graphql}")
    else:
        print(f"   ❌ ERROR: {response.text}")

print("\n" + "="*70)
print("Natural language processing test complete!")
print("="*70)
