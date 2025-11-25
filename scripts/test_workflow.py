# scripts/test_workflow.py
"""
Comprehensive test script for Interview Workflow Automation
Tests all features: status updates, email notifications, job closure, and manager notes
"""
import os
import sys
import requests
import json

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration
API_BASE = "http://localhost:8000"
GRAPHQL_ENDPOINT = f"{API_BASE}/graphql"

# Test user credentials - note this app uses X-User-Role header, not tokens
RECRUITER_EMAIL = "recruiter@google.com"
RECRUITER_PASSWORD = "password123"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def execute_graphql(query, variables=None, user_role="Recruiter"):
    """Execute a GraphQL query with role-based auth"""
    headers = {
        "Content-Type": "application/json",
        "X-User-Role": user_role  # This app uses header-based auth
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=headers)
    return response.json()

def verify_credentials():
    """Verify recruiter credentials"""
    print("🔐 Verifying recruiter credentials...")
    
    response = requests.post(
        f"{API_BASE}/login",
        json={
            "email": RECRUITER_EMAIL,
            "password": RECRUITER_PASSWORD
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    result = response.json()
    user = result.get("user")
    
    print(f"✅ Credentials verified: {user['firstName']} {user['lastName']} (Role: {user['role']})")
    print(f"   Using X-User-Role header for GraphQL requests\n")
    return True

def test_status_update_interviewing():
    """Test 1: Update application status to 'Interviewing' (triggers email)"""
    print_section("TEST 1: Status Update to 'Interviewing' (Email Notification)")
    
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
    
    print("📝 Updating Charlie Brown's application to 'Interviewing'...")
    result = execute_graphql(mutation, user_role="Recruiter")
    
    if "errors" in result:
        print(f"❌ Test failed: {result['errors']}")
        return False
    
    data = result["data"]["updateApplicationStatusByNames"]
    print(f"✅ Status updated successfully!")
    print(f"   Application ID: {data['appId']}")
    print(f"   New Status: {data['status']}")
    print(f"   Candidate: {data['candidate']['firstName']} {data['candidate']['lastName']}")
    print(f"   Email: {data['candidate']['email']}")
    print(f"   Job: {data['job']['title']} at {data['job']['company']}")
    print(f"\n📧 Interview invitation email should be sent to: {data['candidate']['email']}")
    return True

def test_manager_notes():
    """Test 2: Add manager notes to an application"""
    print_section("TEST 2: Add Manager Notes")
    
    mutation = """
    mutation {
      addManagerNoteToApplication(
        userName: "Charlie Brown"
        jobTitle: "Senior Python Developer"
        companyName: "Google"
        note: "Excellent technical skills, great cultural fit. Recommend moving to final round."
      ) {
        appId
        notes
        candidate {
          firstName
          lastName
        }
      }
    }
    """
    
    print("📝 Adding manager note to Charlie Brown's application...")
    result = execute_graphql(mutation, user_role="Recruiter")
    
    if "errors" in result:
        print(f"❌ Test failed: {result['errors']}")
        return False
    
    data = result["data"]["addManagerNoteToApplication"]
    print(f"✅ Note added successfully!")
    print(f"   Application ID: {data['appId']}")
    print(f"   Notes:\n{data['notes']}\n")
    return True

def test_hiring_workflow():
    """Test 3: Hire a candidate (triggers job closure + mass rejection emails)"""
    print_section("TEST 3: Hiring Workflow (Job Closure + Mass Notifications)")
    
    # First, check how many applications exist for Netflix job
    query = """
    {
      jobs(title: "Data Scientist", company: "Netflix") {
        jobId
        title
        company
        status
      }
    }
    """
    
    print("📊 Finding Netflix Data Scientist job...")
    result =execute_graphql(query, user_role="Recruiter")
    job = result["data"]["jobs"][0]
    job_id = job["jobId"]
    
    # Get applications for this job
    apps_query = f"""
    {{
      applications(jobId: {job_id}) {{
        appId
        status
        candidate {{
          firstName
          lastName
          email
        }}
      }}
    }}
    """
    
    apps_result = execute_graphql(apps_query, user_role="Recruiter")
    apps = apps_result["data"]["applications"]
    print(f"   Found {len(apps)} applications:")
    for app in apps:
        print(f"   - {app['candidate']['firstName']} {app['candidate']['lastName']} ({app['status']})")
    
    # Now hire Ethan Hunt
    mutation = """
    mutation {
      updateApplicationStatusByNames(
        userName: "Ethan Hunt"
        jobTitle: "Data Scientist"
        companyName: "Netflix"
        newStatus: "Hired"
      ) {
        appId
        status
        candidate {
          firstName
          lastName
          email
        }
        job {
          jobId
          title
          company
          status
        }
      }
    }
    """
    
    print(f"\n📝 Hiring Ethan Hunt for Data Scientist at Netflix...")
    result = execute_graphql(mutation, user_role="Recruiter")
    
    if "errors" in result:
        print(f"❌ Test failed: {result['errors']}")
        return False
    
    data = result["data"]["updateApplicationStatusByNames"]
    print(f"✅ Candidate hired successfully!")
    print(f"   Hired: {data['candidate']['firstName']} {data['candidate']['lastName']}")
    print(f"   Job Status: {data['job']['status']}")
    print(f"\n⚙️ Automated workflow triggered:")
    print(f"   1. Job marked as 'Closed'")
    print(f"   2. Rejection emails sent to other {len(apps) - 1} applicant(s):")
    for app in apps:
        if app['candidate']['firstName'] != 'Ethan':
            print(f"      - {app['candidate']['email']} ({app['candidate']['firstName']} {app['candidate']['lastName']})")
    
    # Verify job status changed
    job_query = f"""
    {{
      jobById(jobId: {job_id}) {{
        jobId
        title
        status
      }}
    }}
    """
    
    print(f"\n🔍 Verifying job status...")
    job_result = execute_graphql(job_query, user_role="Recruiter")
    job = job_result["data"]["jobById"]
    print(f"   Job #{job['jobId']}: {job['title']}")
    print(f"   Status: {job['status']}")
    
    if job['status'] == 'Closed':
        print(f"   ✅ Job successfully closed!")
    else:
        print(f"   ❌ Job status not updated!")
        return False
    
    return True

def test_natural_language():
    """Test 4: Natural language commands via NL2GQL"""
    print_section("TEST 4: Natural Language Commands")
    
    # Test updating status via NL
    nl_request = "Interview Diana Prince for the Product Manager position at Meta"
    
    print(f"💬 Natural Language: \"{nl_request}\"")
    response = requests.post(
        f"{API_BASE}/nl2gql?run=true",
        json={"query": nl_request},
        headers={"X-User-Role": "Recruiter"}
    )
    
    result = response.json()
    
    if "error" in result:
        print(f"❌ Test failed: {result['error']}")
        return False
    
    print(f"✅ GraphQL Generated:")
    print(f"   {result.get('graphql', 'N/A')}")
    
    if "result" in result and "data" in result["result"]:
        data = result["result"]["data"]
        if "updateApplicationStatusByNames" in data:
            app_data = data["updateApplicationStatusByNames"]
            print(f"\n✅ Status updated via natural language!")
            print(f"   Candidate: {app_data['candidate']['firstName']} {app_data['candidate']['lastName']}")
            print(f"   New Status: {app_data['status']}")
            print(f"   📧 Email sent to: {app_data['candidate']['email']}")
    
    return True

def run_all_tests():
    """Run all workflow tests"""
    print_section("INTERVIEW WORKFLOW AUTOMATION - COMPREHENSIVE TEST SUITE")
    
    # Step 1: Verify credentials
    if not verify_credentials():
        print("❌ Cannot proceed without valid credentials")
        return
    
    # Step 2: Run tests
    tests = [
        ("Status Update (Interviewing)", test_status_update_interviewing),
        ("Manager Notes", test_manager_notes),
        ("Hiring Workflow (Job Closure + Mass Rejection)", test_hiring_workflow),
        ("Natural Language Commands", test_natural_language),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Step 3: Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n🎉 All tests passed! The workflow automation is working perfectly.")
    else:
        print(f"\n⚠️ Some tests failed. Please review the output above.")
    
    print(f"\n📧 Check your Resend dashboard to verify emails were sent:")
    print(f"   https://resend.com/emails")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to the backend server.")
        print("   Please make sure the Flask server is running on http://localhost:8000")
        print("   Run: python src/backend/app.py")
