import requests
import json

url = "http://localhost:8000/graphql"
headers = {"X-User-Role": "Recruiter"}

def run_query(query):
    try:
        response = requests.post(url, json={"query": query}, headers=headers)
        return response.status_code, response.json()
    except Exception as e:
        return None, {"error": str(e)}

def print_test(name, passed, details=""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if details:
        print(f"     {details}")

# Track results
total_tests = 0
passed_tests = 0

print("=" * 70)
print("HEAVY TESTING: Conversational Job Modification")
print("=" * 70)

# ============================================================================
# TEST SUITE 1: Basic CRUD Operations
# ============================================================================
print("\n[SUITE 1] Basic CRUD Operations")
print("-" * 70)

# Test 1.1: Create job without new fields
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Software Engineer"
    company: "TechCorp"
    location: "San Francisco"
    salaryRange: "120k-180k"
  }) {
    jobId
    title
    requires_us_citizenship
    minimum_degree_year
  }
}
""")
job1_id = None
if data.get("data") and data["data"].get("createJob"):
    job1_id = data["data"]["createJob"]["jobId"]
    passed = (data["data"]["createJob"]["requires_us_citizenship"] is None and 
              data["data"]["createJob"]["minimum_degree_year"] is None)
    if passed: passed_tests += 1
    print_test("1.1: Create job without new fields (should be null)", passed,
               f"Job ID: {job1_id}, Fields: {data['data']['createJob']}")
else:
    print_test("1.1: Create job without new fields", False, f"Error: {data}")

# Test 1.2: Update job with citizenship requirement only
total_tests += 1
if job1_id:
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job1_id}, input: {{
        requires_us_citizenship: true
      }}) {{
        jobId
        requires_us_citizenship
        minimum_degree_year
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        passed = (data["data"]["updateJob"]["requires_us_citizenship"] == True and
                  data["data"]["updateJob"]["minimum_degree_year"] is None)
        if passed: passed_tests += 1
        print_test("1.2: Update citizenship only", passed,
                   f"Citizenship: {data['data']['updateJob']['requires_us_citizenship']}")
    else:
        print_test("1.2: Update citizenship only", False, f"Error: {data}")
else:
    print_test("1.2: Update citizenship only", False, "Skipped - no job ID")

# Test 1.3: Update job with degree year only
total_tests += 1
if job1_id:
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job1_id}, input: {{
        minimum_degree_year: 2018
      }}) {{
        jobId
        requires_us_citizenship
        minimum_degree_year
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        passed = (data["data"]["updateJob"]["requires_us_citizenship"] == True and
                  data["data"]["updateJob"]["minimum_degree_year"] == 2018)
        if passed: passed_tests += 1
        print_test("1.3: Update degree year only", passed,
                   f"Degree Year: {data['data']['updateJob']['minimum_degree_year']}")
    else:
        print_test("1.3: Update degree year only", False, f"Error: {data}")
else:
    print_test("1.3: Update degree year only", False, "Skipped - no job ID")

# Test 1.4: Update both fields simultaneously
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Data Scientist"
    company: "DataCo"
  }) {
    jobId
  }
}
""")
job2_id = None
if data.get("data") and data["data"].get("createJob"):
    job2_id = data["data"]["createJob"]["jobId"]
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job2_id}, input: {{
        requires_us_citizenship: false
        minimum_degree_year: 2020
      }}) {{
        jobId
        requires_us_citizenship
        minimum_degree_year
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        passed = (data["data"]["updateJob"]["requires_us_citizenship"] == False and
                  data["data"]["updateJob"]["minimum_degree_year"] == 2020)
        if passed: passed_tests += 1
        print_test("1.4: Update both fields simultaneously", passed,
                   f"Citizenship: {data['data']['updateJob']['requires_us_citizenship']}, Year: {data['data']['updateJob']['minimum_degree_year']}")
    else:
        print_test("1.4: Update both fields simultaneously", False, f"Error: {data}")
else:
    print_test("1.4: Update both fields simultaneously", False, "Failed to create job")

# ============================================================================
# TEST SUITE 2: Edge Cases
# ============================================================================
print("\n[SUITE 2] Edge Cases")
print("-" * 70)

# Test 2.1: Set citizenship to false
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Remote Worker"
    company: "GlobalCo"
  }) {
    jobId
  }
}
""")
job3_id = None
if data.get("data") and data["data"].get("createJob"):
    job3_id = data["data"]["createJob"]["jobId"]
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job3_id}, input: {{
        requires_us_citizenship: false
      }}) {{
        requires_us_citizenship
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        passed = data["data"]["updateJob"]["requires_us_citizenship"] == False
        if passed: passed_tests += 1
        print_test("2.1: Set citizenship to false", passed,
                   f"Value: {data['data']['updateJob']['requires_us_citizenship']}")
    else:
        print_test("2.1: Set citizenship to false", False, f"Error: {data}")
else:
    print_test("2.1: Set citizenship to false", False, "Failed to create job")

# Test 2.2: Very old degree year (1950)
total_tests += 1
if job3_id:
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job3_id}, input: {{
        minimum_degree_year: 1950
      }}) {{
        minimum_degree_year
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        passed = data["data"]["updateJob"]["minimum_degree_year"] == 1950
        if passed: passed_tests += 1
        print_test("2.2: Very old degree year (1950)", passed,
                   f"Value: {data['data']['updateJob']['minimum_degree_year']}")
    else:
        print_test("2.2: Very old degree year (1950)", False, f"Error: {data}")
else:
    print_test("2.2: Very old degree year (1950)", False, "Skipped - no job ID")

# Test 2.3: Future degree year (2030)
total_tests += 1
if job3_id:
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job3_id}, input: {{
        minimum_degree_year: 2030
      }}) {{
        minimum_degree_year
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        passed = data["data"]["updateJob"]["minimum_degree_year"] == 2030
        if passed: passed_tests += 1
        print_test("2.3: Future degree year (2030)", passed,
                   f"Value: {data['data']['updateJob']['minimum_degree_year']}")
    else:
        print_test("2.3: Future degree year (2030)", False, f"Error: {data}")
else:
    print_test("2.3: Future degree year (2030)", False, "Skipped - no job ID")

# Test 2.4: Toggle citizenship multiple times
total_tests += 1
if job3_id:
    # Set to true
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job3_id}, input: {{
        requires_us_citizenship: true
      }}) {{
        requires_us_citizenship
      }}
    }}
    """)
    # Set back to false
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job3_id}, input: {{
        requires_us_citizenship: false
      }}) {{
        requires_us_citizenship
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        passed = data["data"]["updateJob"]["requires_us_citizenship"] == False
        if passed: passed_tests += 1
        print_test("2.4: Toggle citizenship multiple times", passed,
                   f"Final value: {data['data']['updateJob']['requires_us_citizenship']}")
    else:
        print_test("2.4: Toggle citizenship multiple times", False, f"Error: {data}")
else:
    print_test("2.4: Toggle citizenship multiple times", False, "Skipped - no job ID")

# ============================================================================
# TEST SUITE 3: Combined Updates
# ============================================================================
print("\n[SUITE 3] Combined Updates with Other Fields")
print("-" * 70)

# Test 3.1: Update title and citizenship together
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Junior Developer"
    company: "StartupCo"
  }) {
    jobId
  }
}
""")
job4_id = None
if data.get("data") and data["data"].get("createJob"):
    job4_id = data["data"]["createJob"]["jobId"]
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job4_id}, input: {{
        title: "Senior Developer"
        requires_us_citizenship: true
      }}) {{
        title
        requires_us_citizenship
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        passed = (data["data"]["updateJob"]["title"] == "Senior Developer" and
                  data["data"]["updateJob"]["requires_us_citizenship"] == True)
        if passed: passed_tests += 1
        print_test("3.1: Update title and citizenship together", passed,
                   f"Title: {data['data']['updateJob']['title']}, Citizenship: {data['data']['updateJob']['requires_us_citizenship']}")
    else:
        print_test("3.1: Update title and citizenship together", False, f"Error: {data}")
else:
    print_test("3.1: Update title and citizenship together", False, "Failed to create job")

# Test 3.2: Update all modifiable fields
total_tests += 1
if job4_id:
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job4_id}, input: {{
        title: "Principal Engineer"
        company: "MegaCorp"
        location: "New York"
        salaryRange: "200k-300k"
        description: "Lead technical initiatives"
        requires_us_citizenship: false
        minimum_degree_year: 2010
      }}) {{
        title
        company
        location
        salaryRange
        description
        requires_us_citizenship
        minimum_degree_year
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        job = data["data"]["updateJob"]
        passed = (job["title"] == "Principal Engineer" and
                  job["company"] == "MegaCorp" and
                  job["requires_us_citizenship"] == False and
                  job["minimum_degree_year"] == 2010)
        if passed: passed_tests += 1
        print_test("3.2: Update all modifiable fields", passed,
                   f"All fields updated correctly")
    else:
        print_test("3.2: Update all modifiable fields", False, f"Error: {data}")
else:
    print_test("3.2: Update all modifiable fields", False, "Skipped - no job ID")

# ============================================================================
# TEST SUITE 4: Query Verification
# ============================================================================
print("\n[SUITE 4] Query Verification")
print("-" * 70)

# Test 4.1: Query job by ID returns new fields
total_tests += 1
if job1_id:
    status, data = run_query(f"""
    query {{
      jobById(jobId: {job1_id}) {{
        jobId
        title
        requires_us_citizenship
        minimum_degree_year
      }}
    }}
    """)
    if data.get("data") and data["data"].get("jobById"):
        job = data["data"]["jobById"]
        passed = ("requires_us_citizenship" in job and "minimum_degree_year" in job)
        if passed: passed_tests += 1
        print_test("4.1: Query job by ID returns new fields", passed,
                   f"Fields present: {list(job.keys())}")
    else:
        print_test("4.1: Query job by ID returns new fields", False, f"Error: {data}")
else:
    print_test("4.1: Query job by ID returns new fields", False, "Skipped - no job ID")

# Test 4.2: Query all jobs returns new fields
total_tests += 1
status, data = run_query("""
query {
  jobs(limit: 1) {
    jobId
    title
    requires_us_citizenship
    minimum_degree_year
  }
}
""")
if data.get("data") and data["data"].get("jobs") and len(data["data"]["jobs"]) > 0:
    job = data["data"]["jobs"][0]
    passed = ("requires_us_citizenship" in job and "minimum_degree_year" in job)
    if passed: passed_tests += 1
    print_test("4.2: Query all jobs returns new fields", passed,
               f"Fields present in first job")
else:
    print_test("4.2: Query all jobs returns new fields", False, f"Error or no jobs: {data}")

# ============================================================================
# TEST SUITE 5: Null/Reset Tests
# ============================================================================
print("\n[SUITE 5] Null/Reset Behavior")
print("-" * 70)

# Test 5.1: Can we reset citizenship to null? (This might not work, testing behavior)
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Test Reset Job"
    company: "TestCo"
  }) {
    jobId
  }
}
""")
job5_id = None
if data.get("data") and data["data"].get("createJob"):
    job5_id = data["data"]["createJob"]["jobId"]
    # First set it to true
    run_query(f"""
    mutation {{
      updateJob(jobId: {job5_id}, input: {{
        requires_us_citizenship: true
        minimum_degree_year: 2015
      }}) {{
        jobId
      }}
    }}
    """)
    # Try to update without these fields (should keep existing values)
    status, data = run_query(f"""
    mutation {{
      updateJob(jobId: {job5_id}, input: {{
        title: "Updated Title"
      }}) {{
        title
        requires_us_citizenship
        minimum_degree_year
      }}
    }}
    """)
    if data.get("data") and data["data"].get("updateJob"):
        job = data["data"]["updateJob"]
        # Fields should persist (not reset to null)
        passed = (job["requires_us_citizenship"] == True and 
                  job["minimum_degree_year"] == 2015 and
                  job["title"] == "Updated Title")
        if passed: passed_tests += 1
        print_test("5.1: Fields persist when not included in update", passed,
                   f"Citizenship: {job['requires_us_citizenship']}, Year: {job['minimum_degree_year']}")
    else:
        print_test("5.1: Fields persist when not included in update", False, f"Error: {data}")
else:
    print_test("5.1: Fields persist when not included in update", False, "Failed to create job")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Total Tests: {total_tests}")
print(f"Passed: {passed_tests}")
print(f"Failed: {total_tests - passed_tests}")
print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
print("=" * 70)

if passed_tests == total_tests:
    print("\n[SUCCESS] All tests passed! ✓")
else:
    print(f"\n[WARNING] {total_tests - passed_tests} test(s) failed")
