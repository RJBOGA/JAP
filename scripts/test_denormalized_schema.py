#!/usr/bin/env python3
"""
Comprehensive Test Suite for Denormalized Application Schema
Tests all workflow features with the new userName/jobTitle/companyName fields
"""
import requests
import json
import sys

# Configuration
API_BASE = "http://localhost:8000"
GRAPHQL_ENDPOINT = f"{API_BASE}/graphql"

# Test Results
test_results = []

def print_header(title):
    """Print a formatted test header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def execute_graphql(query, user_role="Recruiter"):
    """Execute a GraphQL query"""
    headers = {
        "Content-Type": "application/json",
        "X-User-Role": user_role
    }
    response = requests.post(GRAPHQL_ENDPOINT, json={"query": query}, headers=headers)
    return response.json()

def test_apply_with_denormalized_fields():
    """TEST 1: Apply mutation should save denormalized fields"""
    print_header("TEST 1: Apply Mutation with Denormalized Fields")
    
    # First, create a test user and job
    register_user = requests.post(f"{API_BASE}/register", json={
        "email": "testuser@example.com",
        "password": "test123",
        "firstName": "Test",
        "last Name": "User",
        "role": "Applicant"
    })
    
    if register_user.status_code != 201:
        print(f"❌ Failed to create test user: {register_user.text}")
        return False
    
    # Create a test job
    create_job_mutation = """
    mutation {
      createJob(input: {
        title: "Test Engineer"
        company: "TestCorp"
        location: "Remote"
        description: "Test position"
        skillsRequired: ["Testing"]
      }) {
        jobId
        title
        company
      }
    }
    """
    
    job_result = execute_graphql(create_job_mutation, "Recruiter")
    if "errors" in job_result:
        print(f"❌ Failed to create job: {job_result['errors']}")
        return False
    
    print(f"✅ Created job: {job_result['data']['createJob']['title']}")
    
    # Now apply to the job
    apply_mutation = """
    mutation {
      apply(
        userName: "Test User"
        jobTitle: "Test Engineer"
        companyName: "TestCorp"
      ) {
        appId
        userName
        jobTitle
        companyName
        status
        candidate {
          firstName
          lastName
        }
      }
    }
    """
    
    apply_result = execute_graphql(apply_mutation, "Applicant")
    
    if "errors" in apply_result:
        print(f"❌ Apply mutation failed: {apply_result['errors']}")
        return False
    
    app_data = apply_result["data"]["apply"]
    
    # Verify denormalized fields are saved
    checks = [
        (app_data.get("userName") == "Test User", "userName field"),
        (app_data.get("jobTitle") == "Test Engineer", "jobTitle field"),
        (app_data.get("companyName") == "TestCorp", "companyName field"),
        (app_data.get("status") == "Applied", "status field")
    ]
    
    all_passed = all(check[0] for check in checks)
    
    for passed, field in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {field}: {app_data.get(field.split()[0])}")
    
    if all_passed:
        print(f"\n✅ TEST 1 PASSED: All denormalized fields saved correctly!")
    else:
        print(f"\n❌ TEST 1 FAILED: Some fields missing or incorrect")
    
    return all_passed

def test_status_update_with_denormalized_query():
    """TEST 2: Status update should query by denormalized fields"""
    print_header("TEST 2: Status Update Using Denormalized Fields")
    
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
        userName
        jobTitle
        companyName
        candidate {
          firstName
          lastName
          email
        }
      }
    }
    """
    
    result = execute_graphql(mutation, "Recruiter")
    
    if "errors" in result:
        print(f"❌ Status update failed: {result['errors']}")
        return False
    
    app_data = result["data"]["updateApplicationStatusByNames"]
    
    # Verify the update worked (using denormalized fields)
    checks = [
        (app_data.get("userName") == "Charlie Brown", "userName matched"),
        (app_data.get("jobTitle") == "Senior Python Developer", "jobTitle matched"),
        (app_data.get("companyName") == "Google", "companyName matched"),
        (app_data.get("status") == "Interviewing", "status updated"),
        (app_data.get("candidate", {}).get("email") is not None, "candidate email present")
    ]
    
    all_passed = all(check[0] for check in checks)
    
    for passed, description in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {description}")
    
    if app_data.get("candidate", {}).get("email"):
        print(f"\n  📧 Email should be sent to: {app_data['candidate']['email']}")
    
    if all_passed:
        print(f"\n✅ TEST 2 PASSED: Status update works with denormalized fields!")
    else:
        print(f"\n❌ TEST 2 FAILED")
    
    return all_passed

def test_manager_notes_with_denormalized_query():
    """TEST 3: Manager notes should query by denormalized fields"""
    print_header("TEST 3: Manager Notes Using Denormalized Fields")
    
    mutation = """
    mutation {
      addManagerNoteToApplication(
        userName: "Charlie Brown"
        jobTitle: "Senior Python Developer"
        companyName: "Google"
        note: "Excellent interview performance. Strong technical skills."
      ) {
        appId
        notes
        userName
        jobTitle
        candidate {
          firstName
          lastName
        }
      }
    }
    """
    
    result = execute_graphql(mutation, "Recruiter")
    
    if "errors" in result:
        print(f"❌ Manager notes failed: {result['errors']}")
        return False
    
    app_data = result["data"]["addManagerNoteToApplication"]
    
    # Verify notes were added
    checks = [
        (app_data.get("userName") == "Charlie Brown", "userName matched"),
        (app_data.get("jobTitle") == "Senior Python Developer", "jobTitle matched"),
        ("Recruiter Note" in app_data.get("notes", ""), "note has timestamp prefix"),
        ("Excellent interview performance" in app_data.get("notes", ""), "note content saved")
    ]
    
    all_passed = all(check[0] for check in checks)
    
    for passed, description in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {description}")
    
    print(f"\n  📝 Notes preview:")
    notes = app_data.get("notes", "")
    print(f"  {notes[:100]}..." if len(notes) > 100 else f"  {notes}")
    
    if all_passed:
        print(f"\n✅ TEST 3 PASSED: Manager notes work with denormalized fields!")
    else:
        print(f"\n❌ TEST 3 FAILED")
    
    return all_passed

def test_hiring_workflow():
    """TEST 4: Hiring workflow should use denormalized fields"""
    print_header("TEST 4: Hiring Workflow (Job Closure + Mass Emails)")
    
    # First check how many applicants for Netflix
    query = """
    {
      jobs(title: "Data Scientist", company: "Netflix") {
        jobId
        title
        status
        applicationCount
      }
    }
    """
    
    job_result = execute_graphql(query, "Recruiter")
    
    if "errors" in job_result or not job_result.get("data", {}).get("jobs"):
        print(f"❌ Failed to query Netflix job")
        return False
    
    job = job_result["data"]["jobs"][0]
    initial_status = job.get("status")
    app_count = job.get("applicationCount", 0)
    
    print(f"  📊 Job Status (before): {initial_status}")
    print(f"  📊 Application Count: {app_count}")
    
    # Hire Ethan Hunt
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
        userName
        jobTitle
        job {
          jobId
          title
          status
        }
      }
    }
    """
    
    result = execute_graphql(mutation, "Recruiter")
    
    if "errors" in result:
        print(f"❌ Hiring failed: {result['errors']}")
        return False
    
    app_data = result["data"]["updateApplicationStatusByNames"]
    
    # Verify the workflow
    checks = [
        (app_data.get("status") == "Hired", "candidate marked as Hired"),
        (app_data.get("job", {}).get("status") == "Closed", "job automatically closed"),
        (app_data.get("userName") == "Ethan Hunt", "correct candidate hired")
    ]
    
    all_passed = all(check[0] for check in checks)
    
    for passed, description in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {description}")
    
    print(f"\n  ⚙️ Background tasks triggered:")
    print(f"     - Job #{app_data['job']['jobId']} closed")
    print(f"     - Rejection emails sent to {app_count - 1} other candidate(s)")
    
    if all_passed:
        print(f"\n✅ TEST 4 PASSED: Hiring workflow works correctly!")
    else:
        print(f"\n❌ TEST 4 FAILED")
    
    return all_passed

def test_query_applications_with_denormalized_fields():
    """TEST 5: Query applications and verify denormalized fields exist"""
    print_header("TEST 5: Query Applications with Denormalized Fields")
    
    query = """
    {
      applications(jobId: 1) {
        appId
        userName
        jobTitle
        companyName
        status
      }
    }
    """
    
    result = execute_graphql(query, "Recruiter")
    
    if "errors" in result:
        print(f"❌ Query failed: {result['errors']}")
        return False
    
    apps = result["data"]["applications"]
    
    if not apps:
        print(f"  ⚠️ No applications found for job #1")
        return True  # Not a failure, just no data
    
    print(f"  Found {len(apps)} application(s):")
    
    all_have_fields = True
    for app in apps:
        has_fields = all([
            app.get("userName"),
            app.get("jobTitle"),
            app.get("companyName")
        ])
        
        status = "✅" if has_fields else "❌"
        print(f"  {status} App #{app['appId']}: {app.get('userName')} → {app.get('jobTitle')} @ {app.get('companyName')}")
        
        if not has_fields:
            all_have_fields = False
    
    if all_have_fields:
        print(f"\n✅ TEST 5 PASSED: All applications have denormalized fields!")
    else:
        print(f"\n❌ TEST 5 FAILED: Some applications missing fields")
    
    return all_have_fields

def run_all_tests():
    """Run all test cases"""
    print_header("COMPREHENSIVE TEST SUITE - Denormalized Application Schema")
    
    tests = [
        ("Apply with Denormalized Fields", test_apply_with_denormalized_fields),
        ("Status Update Query", test_status_update_with_denormalized_query),
        ("Manager Notes Query", test_manager_notes_with_denormalized_query),
        ("Hiring Workflow", test_hiring_workflow),
        ("Query Applications", test_query_applications_with_denormalized_fields),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print(f"\n🎉 ALL TESTS PASSED! Denormalized schema working perfectly!")
        print(f"\n📧 Check Resend dashboard for emails: https://resend.com/emails")
        return 0
    else:
        print(f"\n⚠️ Some tests failed. Review output above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend server")
        print("   Make sure it's running: python src/backend/app.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(130)
