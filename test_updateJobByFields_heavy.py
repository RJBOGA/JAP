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

print("=" * 80)
print("ENHANCED HEAVY TESTING: updateJobByFields Mutation")
print("=" * 80)

# ============================================================================
# TEST SUITE 1: updateJobByFields - Basic Functionality
# ============================================================================
print("\n[SUITE 1] updateJobByFields - Basic Functionality")
print("-" * 80)

# Test 1.1: Update job by title only (no company specified)
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Unique Backend Engineer"
    company: "BackendCorp"
    location: "Remote"
  }) {
    jobId
    title
    company
  }
}
""")
if data.get("data") and data["data"].get("createJob"):
    created_job = data["data"]["createJob"]
    status, data = run_query("""
    mutation {
      updateJobByFields(
        title: "Unique Backend Engineer"
        input: { requires_us_citizenship: true }
      ) {
        jobId
        title
        requires_us_citizenship
      }
    }
    """)
    if data.get("data") and data["data"].get("updateJobByFields"):
        passed = data["data"]["updateJobByFields"]["requires_us_citizenship"] == True
        if passed: passed_tests += 1
        print_test("1.1: Update job by title only", passed,
                   f"Updated job {data['data']['updateJobByFields']['jobId']}")
    else:
        print_test("1.1: Update job by title only", False, f"Error: {data}")
else:
    print_test("1.1: Update job by title only", False, "Failed to create job")

# Test 1.2: Update job by title AND company
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Senior Data Engineer"
    company: "DataCorp"
  }) {
    jobId
  }
}
""")
if data.get("data") and data["data"].get("createJob"):
    status, data = run_query("""
    mutation {
      updateJobByFields(
        title: "Senior Data Engineer"
        company: "DataCorp"
        input: { minimum_degree_year: 2015 }
      ) {
        jobId
        title
        company
        minimum_degree_year
      }
    }
    """)
    if data.get("data") and data["data"].get("updateJobByFields"):
        job = data["data"]["updateJobByFields"]
        passed = (job["minimum_degree_year"] == 2015 and 
                  job["title"] == "Senior Data Engineer" and
                  job["company"] == "DataCorp")
        if passed: passed_tests += 1
        print_test("1.2: Update job by title AND company", passed,
                   f"Job {job['jobId']} updated correctly")
    else:
        print_test("1.2: Update job by title AND company", False, f"Error: {data}")
else:
    print_test("1.2: Update job by title AND company", False, "Failed to create job")

# Test 1.3: Update both citizenship and degree year
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "ML Engineer"
    company: "AI Labs"
  }) {
    jobId
  }
}
""")
if data.get("data") and data["data"].get("createJob"):
    status, data = run_query("""
    mutation {
      updateJobByFields(
        title: "ML Engineer"
        company: "AI Labs"
        input: { 
          requires_us_citizenship: true
          minimum_degree_year: 2018
        }
      ) {
        jobId
        requires_us_citizenship
        minimum_degree_year
      }
    }
    """)
    if data.get("data") and data["data"].get("updateJobByFields"):
        job = data["data"]["updateJobByFields"]
        passed = (job["requires_us_citizenship"] == True and 
                  job["minimum_degree_year"] == 2018)
        if passed: passed_tests += 1
        print_test("1.3: Update both citizenship and degree year", passed,
                   f"Both fields updated: citizenship={job['requires_us_citizenship']}, year={job['minimum_degree_year']}")
    else:
        print_test("1.3: Update both citizenship and degree year", False, f"Error: {data}")
else:
    print_test("1.3: Update both citizenship and degree year", False, "Failed to create job")

# ============================================================================
# TEST SUITE 2: updateJobByFields - Error Handling
# ============================================================================
print("\n[SUITE 2] updateJobByFields - Error Handling")
print("-" * 80)

# Test 2.1: Job not found
total_tests += 1
status, data = run_query("""
mutation {
  updateJobByFields(
    title: "Non-Existent Job Title XYZ123"
    input: { requires_us_citizenship: true }
  ) {
    jobId
  }
}
""")
if data.get("errors"):
    passed = "not found" in str(data["errors"]).lower()
    if passed: passed_tests += 1
    print_test("2.1: Job not found error", passed,
               f"Correctly returned error")
else:
    print_test("2.1: Job not found error", False, "Should have returned error")

# Test 2.2: Multiple jobs match (ambiguous)
total_tests += 1
# Create two jobs with same title, different companies
status, data1 = run_query("""
mutation {
  createJob(input: {
    title: "Duplicate Title Job"
    company: "Company A"
  }) {
    jobId
  }
}
""")
status, data2 = run_query("""
mutation {
  createJob(input: {
    title: "Duplicate Title Job"
    company: "Company B"
  }) {
    jobId
  }
}
""")
if (data1.get("data") and data1["data"].get("createJob") and 
    data2.get("data") and data2["data"].get("createJob")):
    # Try to update without specifying company (should fail - ambiguous)
    status, data = run_query("""
    mutation {
      updateJobByFields(
        title: "Duplicate Title Job"
        input: { requires_us_citizenship: true }
      ) {
        jobId
      }
    }
    """)
    if data.get("errors"):
        passed = "multiple" in str(data["errors"]).lower()
        if passed: passed_tests += 1
        print_test("2.2: Multiple jobs matched error", passed,
                   f"Correctly detected ambiguous update")
    else:
        print_test("2.2: Multiple jobs matched error", False, "Should have returned error for ambiguous match")
else:
    print_test("2.2: Multiple jobs matched error", False, "Failed to create duplicate jobs")

# Test 2.3: Update with company specified resolves ambiguity
total_tests += 1
status, data = run_query("""
mutation {
  updateJobByFields(
    title: "Duplicate Title Job"
    company: "Company A"
    input: { requires_us_citizenship: true }
  ) {
    jobId
    company
    requires_us_citizenship
  }
}
""")
if data.get("data") and data["data"].get("updateJobByFields"):
    job = data["data"]["updateJobByFields"]
    passed = (job["company"] == "Company A" and 
              job["requires_us_citizenship"] == True)
    if passed: passed_tests += 1
    print_test("2.3: Company specified resolves ambiguity", passed,
               f"Updated correct job: {job['company']}")
else:
    print_test("2.3: Company specified resolves ambiguity", False, f"Error: {data}")

# ============================================================================
# TEST SUITE 3: updateJobByFields - Combined Field Updates
# ============================================================================
print("\n[SUITE 3] updateJobByFields - Combined Field Updates")
print("-" * 80)

# Test 3.1: Update title along with new fields
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Junior DevOps"
    company: "CloudCo"
  }) {
    jobId
  }
}
""")
if data.get("data") and data["data"].get("createJob"):
    status, data = run_query("""
    mutation {
      updateJobByFields(
        title: "Junior DevOps"
        company: "CloudCo"
        input: { 
          title: "Senior DevOps"
          requires_us_citizenship: true
          minimum_degree_year: 2016
        }
      ) {
        jobId
        title
        requires_us_citizenship
        minimum_degree_year
      }
    }
    """)
    if data.get("data") and data["data"].get("updateJobByFields"):
        job = data["data"]["updateJobByFields"]
        passed = (job["title"] == "Senior DevOps" and
                  job["requires_us_citizenship"] == True and
                  job["minimum_degree_year"] == 2016)
        if passed: passed_tests += 1
        print_test("3.1: Update title along with new fields", passed,
                   f"All fields updated: {job['title']}, citizenship={job['requires_us_citizenship']}, year={job['minimum_degree_year']}")
    else:
        print_test("3.1: Update title along with new fields", False, f"Error: {data}")
else:
    print_test("3.1: Update title along with new fields", False, "Failed to create job")

# Test 3.2: Update all fields at once
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Basic Job"
    company: "BasicCo"
  }) {
    jobId
  }
}
""")
if data.get("data") and data["data"].get("createJob"):
    status, data = run_query("""
    mutation {
      updateJobByFields(
        title: "Basic Job"
        company: "BasicCo"
        input: { 
          title: "Advanced Position"
          company: "AdvancedCo"
          location: "San Francisco"
          salaryRange: "150k-200k"
          description: "Exciting opportunity"
          requires_us_citizenship: false
          minimum_degree_year: 2020
        }
      ) {
        jobId
        title
        company
        location
        salaryRange
        description
        requires_us_citizenship
        minimum_degree_year
      }
    }
    """)
    if data.get("data") and data["data"].get("updateJobByFields"):
        job = data["data"]["updateJobByFields"]
        passed = (job["title"] == "Advanced Position" and
                  job["company"] == "AdvancedCo" and
                  job["location"] == "San Francisco" and
                  job["requires_us_citizenship"] == False and
                  job["minimum_degree_year"] == 2020)
        if passed: passed_tests += 1
        print_test("3.2: Update all fields at once", passed,
                   f"All fields updated successfully")
    else:
        print_test("3.2: Update all fields at once", False, f"Error: {data}")
else:
    print_test("3.2: Update all fields at once", False, "Failed to create job")

# ============================================================================
# TEST SUITE 4: Case Sensitivity Tests
# ============================================================================
print("\n[SUITE 4] Case Sensitivity Tests")
print("-" * 80)

# Test 4.1: Case-insensitive title matching
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Software Architect"
    company: "ArchCo"
  }) {
    jobId
  }
}
""")
if data.get("data") and data["data"].get("createJob"):
    # Try to update with different case
    status, data = run_query("""
    mutation {
      updateJobByFields(
        title: "software architect"
        company: "ArchCo"
        input: { requires_us_citizenship: true }
      ) {
        jobId
        title
        requires_us_citizenship
      }
    }
    """)
    if data.get("data") and data["data"].get("updateJobByFields"):
        passed = data["data"]["updateJobByFields"]["requires_us_citizenship"] == True
        if passed: passed_tests += 1
        print_test("4.1: Case-insensitive title matching", passed,
                   f"Matched despite case difference")
    else:
        print_test("4.1: Case-insensitive title matching", False, f"Error: {data}")
else:
    print_test("4.1: Case-insensitive title matching", False, "Failed to create job")

# Test 4.2: Case-insensitive company matching
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "QA Engineer"
    company: "TestCorp"
  }) {
    jobId
  }
}
""")
if data.get("data") and data["data"].get("createJob"):
    status, data = run_query("""
    mutation {
      updateJobByFields(
        title: "QA Engineer"
        company: "testcorp"
        input: { minimum_degree_year: 2019 }
      ) {
        jobId
        company
        minimum_degree_year
      }
    }
    """)
    if data.get("data") and data["data"].get("updateJobByFields"):
        passed = data["data"]["updateJobByFields"]["minimum_degree_year"] == 2019
        if passed: passed_tests += 1
        print_test("4.2: Case-insensitive company matching", passed,
                   f"Matched company despite case difference")
    else:
        print_test("4.2: Case-insensitive company matching", False, f"Error: {data}")
else:
    print_test("4.2: Case-insensitive company matching", False, "Failed to create job")

# ============================================================================
# TEST SUITE 5: Comparison with updateJob (ID-based)
# ============================================================================
print("\n[SUITE 5] Comparison: updateJobByFields vs updateJob")
print("-" * 80)

# Test 5.1: Both methods produce same result
total_tests += 1
status, data = run_query("""
mutation {
  createJob(input: {
    title: "Comparison Test Job A"
    company: "CompareA"
  }) {
    jobId
  }
}
""")
job_a_id = None
if data.get("data") and data["data"].get("createJob"):
    job_a_id = data["data"]["createJob"]["jobId"]

status, data = run_query("""
mutation {
  createJob(input: {
    title: "Comparison Test Job B"
    company: "CompareB"
  }) {
    jobId
  }
}
""")
job_b_id = None
if data.get("data") and data["data"].get("createJob"):
    job_b_id = data["data"]["createJob"]["jobId"]

if job_a_id and job_b_id:
    # Update A using updateJob (ID-based)
    status, data_a = run_query(f"""
    mutation {{
      updateJob(jobId: {job_a_id}, input: {{
        requires_us_citizenship: true
        minimum_degree_year: 2017
      }}) {{
        requires_us_citizenship
        minimum_degree_year
      }}
    }}
    """)
    
    # Update B using updateJobByFields (field-based)
    status, data_b = run_query("""
    mutation {
      updateJobByFields(
        title: "Comparison Test Job B"
        company: "CompareB"
        input: {
          requires_us_citizenship: true
          minimum_degree_year: 2017
        }
      ) {
        requires_us_citizenship
        minimum_degree_year
      }
    }
    """)
    
    if (data_a.get("data") and data_a["data"].get("updateJob") and
        data_b.get("data") and data_b["data"].get("updateJobByFields")):
        job_a = data_a["data"]["updateJob"]
        job_b = data_b["data"]["updateJobByFields"]
        passed = (job_a["requires_us_citizenship"] == job_b["requires_us_citizenship"] and
                  job_a["minimum_degree_year"] == job_b["minimum_degree_year"])
        if passed: passed_tests += 1
        print_test("5.1: Both methods produce same result", passed,
                   f"updateJob and updateJobByFields behave identically")
    else:
        print_test("5.1: Both methods produce same result", False, "One or both updates failed")
else:
    print_test("5.1: Both methods produce same result", False, "Failed to create comparison jobs")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY - updateJobByFields Enhanced Tests")
print("=" * 80)
print(f"Total Tests: {total_tests}")
print(f"Passed: {passed_tests}")
print(f"Failed: {total_tests - passed_tests}")
print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
print("=" * 80)

if passed_tests == total_tests:
    print("\n[SUCCESS] All updateJobByFields tests passed! ✓")
else:
    print(f"\n[WARNING] {total_tests - passed_tests} test(s) failed")
