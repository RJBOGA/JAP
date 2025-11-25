import requests
import json

# Test login
response = requests.post(
    "http://localhost:8000/login",
    json={
        "email": "recruiter@google.com",
        "password": "password123"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    print(f"\nParsed JSON:")
    print(json.dumps(data, indent=2))
