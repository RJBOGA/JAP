# MANUAL TESTING GUIDE - Interview Workflow Automation
## Complete End-to-End Testing Scenarios

This guide provides step-by-step instructions to manually test all features of the job application system, including the new interview workflow automation with email notifications.

---

## PREREQUISITES

1. **Start MongoDB** (make sure it's running on localhost:27017)
2. **Start the Backend Server**:
   ```bash
   python src/backend/app.py
   ```
   Server should be running at: http://localhost:8000

3. **Seed the Database** (optional - creates test data):
   ```bash
   python scripts/seed_db.py
   ```

4. **Tools Needed**:
   - Terminal/PowerShell
   - API testing tool (Postman, Insomnia, or curl)
   - OR GraphQL Explorer at: http://localhost:8000/graphql

---

## SCENARIO 1: RECRUITER WORKFLOW

### Step 1.1: Create Recruiter Account

**Endpoint**: `POST http://localhost:8000/register`

**Request Body**:
```json
{
  "email": "jane.recruiter@techcorp.com",
  "password": "SecurePass123",
  "firstName": "Jane",
  "lastName": "Recruiter",
  "role": "Recruiter"
}
```

**Expected Response** (201 Created):
```json
{
  "message": "User registered successfully!",
  "UserID": 251
}
```

**Save the UserID** - you'll need it later!

---

### Step 1.2: Login as Recruiter

**Endpoint**: `POST http://localhost:8000/login`

**Request Body**:
```json
{
  "email": "jane.recruiter@techcorp.com",
  "password": "SecurePass123"
}
```

**Expected Response** (200 OK):
```json
{
  "message": "Login successful!",
  "user": {
    "UserID": 251,
    "firstName": "Jane",
    "lastName": "Recruiter",
    "role": "Recruiter",
    "email": "jane.recruiter@techcorp.com"
  }
}
```

**IMPORTANT**: For all subsequent GraphQL requests, add this header:
```
X-User-Role: Recruiter
```

---

### Step 1.3: Post a New Job

**Endpoint**: `POST http://localhost:8000/graphql`

**Headers**:
```
Content-Type: application/json
X-User-Role: Recruiter
```

**GraphQL Mutation**:
```graphql
mutation {
  createJob(input: {
    title: "Senior Full Stack Developer"
    company: "TechCorp"
    location: "San Francisco, CA"
    salaryRange: "$150k - $200k"
    skillsRequired: ["React", "Node.js", "TypeScript", "AWS"]
    description: "We are seeking an experienced full stack developer to join our innovative team. You will work on cutting-edge projects using modern technologies."
  }) {
    jobId
    title
    company
    location
    status
    postedAt
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "createJob": {
      "jobId": 6,
      "title": "Senior Full Stack Developer",
      "company": "TechCorp",
      "location": "San Francisco, CA",
      "status": null,
      "postedAt": "2025-11-23"
    }
  }
}
```

**Save the jobId** (e.g., 6) - you'll need it!

---

### Step 1.4: View All Posted Jobs

**GraphQL Query**:
```graphql
{
  jobs(company: "TechCorp") {
    jobId
    title
    company
    location
    applicationCount
    status
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "jobs": [
      {
        "jobId": 6,
        "title": "Senior Full Stack Developer",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "applicationCount": 0,
        "status": null
      }
    ]
  }
}
```

---

## SCENARIO 2: APPLICANT WORKFLOW

### Step 2.1: Create Applicant Account

**Endpoint**: `POST http://localhost:8000/register`

**Request Body**:
```json
{
  "email": "john.developer@email.com",
  "password": "DevPass123",
  "firstName": "John",
  "lastName": "Developer",
  "role": "Applicant"
}
```

**Expected Response** (201 Created):
```json
{
  "message": "User registered successfully!",
  "UserID": 252
}
```

**Save the UserID** (e.g., 252)!

---

### Step 2.2: Update Applicant Profile

**Endpoint**: `POST http://localhost:8000/graphql`

**Headers**:
```
Content-Type: application/json
X-User-Role: Applicant
```

**GraphQL Mutation** (use your UserID):
```graphql
mutation {
  updateUser(UserID: 252, input: {
    city: "San Francisco"
    country: "USA"
    professionalTitle: "Full Stack Developer"
    years_of_experience: 6
    skills: ["React", "Node.js", "TypeScript", "MongoDB", "AWS"]
    linkedin_profile: "https://linkedin.com/in/johndeveloper"
    highest_qualification: "Bachelor of Science in Computer Science"
  }) {
    UserID
    firstName
    lastName
    professionalTitle
    skills
    years_of_experience
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "updateUser": {
      "UserID": 252,
      "firstName": "John",
      "lastName": "Developer",
      "professionalTitle": "Full Stack Developer",
      "skills": ["React", "Node.js", "TypeScript", "MongoDB", "AWS"],
      "years_of_experience": 6
    }
  }
}
```

---

### Step 2.3: Apply to the Job

**GraphQL Mutation**:
```graphql
mutation {
  apply(
    userName: "John Developer"
    jobTitle: "Senior Full Stack Developer"
    companyName: "TechCorp"
  ) {
    appId
    status
    submittedAt
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
```

**Expected Response**:
```json
{
  "data": {
    "apply": {
      "appId": 7,
      "status": "Applied",
      "submittedAt": "2025-11-23T05:15:00Z",
      "candidate": {
        "firstName": "John",
        "lastName": "Developer",
        "email": "john.developer@email.com"
      },
      "job": {
        "title": "Senior Full Stack Developer",
        "company": "TechCorp"
      }
    }
  }
}
```

**Save the appId** (e.g., 7)!

---

### Step 2.4: Add a Note to Your Application (Applicant)

**GraphQL Mutation**:
```graphql
mutation {
  addNoteToApplicationByJob(
    jobTitle: "Senior Full Stack Developer"
    companyName: "TechCorp"
    note: "I am particularly excited about this role because I have 6 years of experience with the exact tech stack you're using. I recently led a migration to TypeScript at my current company."
  ) {
    appId
    notes
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "addNoteToApplicationByJob": {
      "appId": 7,
      "notes": "I am particularly excited about this role..."
    }
  }
}
```

---

## SCENARIO 3: RECRUITER REVIEWS APPLICATIONS

### Step 3.1: Switch Back to Recruiter

**IMPORTANT**: Change your header to:
```
X-User-Role: Recruiter
```

### Step 3.2: View All Applications for Your Job

**GraphQL Query** (use your jobId):
```graphql
{
  jobs(title: "Senior Full Stack Developer", company: "TechCorp") {
    jobId
    title
    applicationCount
    applicants {
      UserID
      firstName
      lastName
      email
      professionalTitle
      skills
      years_of_experience
    }
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "jobs": [
      {
        "jobId": 6,
        "title": "Senior Full Stack Developer",
        "applicationCount": 1,
        "applicants": [
          {
            "UserID": 252,
            "firstName": "John",
            "lastName": "Developer",
            "email": "john.developer@email.com",
            "professionalTitle": "Full Stack Developer",
            "skills": ["React", "Node.js", "TypeScript", "MongoDB", "AWS"],
            "years_of_experience": 6
          }
        ]
      }
    ]
  }
}
```

---

### Step 3.3: View Application Details

**GraphQL Query**:
```graphql
{
  applications(jobId: 6) {
    appId
    status
    submittedAt
    notes
    candidate {
      firstName
      lastName
      email
      skills
    }
  }
}
```

---

## SCENARIO 4: INTERVIEW WORKFLOW (EMAIL NOTIFICATION)

### Step 4.1: Update Application Status to "Interviewing"

**CRITICAL**: This will **SEND AN EMAIL** to the candidate!

**GraphQL Mutation**:
```graphql
mutation {
  updateApplicationStatusByNames(
    userName: "John Developer"
    jobTitle: "Senior Full Stack Developer"
    companyName: "TechCorp"
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
```

**Expected Response**:
```json
{
  "data": {
    "updateApplicationStatusByNames": {
      "appId": 7,
      "status": "Interviewing",
      "candidate": {
        "firstName": "John",
        "lastName": "Developer",
        "email": "john.developer@email.com"
      },
      "job": {
        "title": "Senior Full Stack Developer",
        "company": "TechCorp"
      }
    }
  }
}
```

**✅ CHECK**: 
1. Look at your backend console - you should see:
   ```
   Interview invitation sent to john.developer@email.com
   ```

2. Check your Resend dashboard at: https://resend.com/emails
   - You should see an email sent to: john.developer@email.com
   - Subject: "Interview Invitation for the Senior Full Stack Developer position at TechCorp"

---

### Step 4.2: Add Manager Notes After Interview

**GraphQL Mutation**:
```graphql
mutation {
  addManagerNoteToApplication(
    userName: "John Developer"
    jobTitle: "Senior Full Stack Developer"
    companyName: "TechCorp"
    note: "Excellent technical interview. Strong knowledge of React and Node.js. Good cultural fit. Recommend moving to final round."
  ) {
    appId
    notes
    candidate {
      firstName
      lastName
    }
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "addManagerNoteToApplication": {
      "appId": 7,
      "notes": "I am particularly excited about this role...\n--- Recruiter Note (2025-11-23): Excellent technical interview. Strong knowledge of React and Node.js. Good cultural fit. Recommend moving to final round.",
      "candidate": {
        "firstName": "John",
        "lastName": "Developer"
      }
    }
  }
}
```

Notice the notes are **timestamped** and **appended**!

---

## SCENARIO 5: HIRING WORKFLOW (AUTOMATED JOB CLOSURE + MASS EMAILS)

### Step 5.1: Create Additional Applicants (for mass rejection test)

Let's create 2 more applicants who also applied:

**Applicant 2**:
```json
POST /register
{
  "email": "sarah.engineer@email.com",
  "password": "Pass123",
  "firstName": "Sarah",
  "lastName": "Engineer",
  "role": "Applicant"
}
```

**Applicant 3**:
```json
POST /register
{
  "email": "mike.coder@email.com",
  "password": "Pass123",
  "firstName": "Mike",
  "lastName": "Coder",
  "role": "Applicant"
}
```

### Step 5.2: Have Them Apply

**As Sarah** (X-User-Role: Applicant):
```graphql
mutation {
  apply(
    userName: "Sarah Engineer"
    jobTitle: "Senior Full Stack Developer"
    companyName: "TechCorp"
  ) {
    appId
    status
  }
}
```

**As Mike** (X-User-Role: Applicant):
```graphql
mutation {
  apply(
    userName: "Mike Coder"
    jobTitle: "Senior Full Stack Developer"
    companyName: "TechCorp"
  ) {
    appId
    status
  }
}
```

---

### Step 5.3: Hire John Developer

**CRITICAL**: This will:
1. Mark John as "Hired"
2. Close the job automatically
3. Send rejection emails to Sarah and Mike

**As Recruiter** (X-User-Role: Recruiter):
```graphql
mutation {
  updateApplicationStatusByNames(
    userName: "John Developer"
    jobTitle: "Senior Full Stack Developer"
    companyName: "TechCorp"
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
      status
    }
  }
}
```

**Expected Response**:
```json
{
  "data": {
    "updateApplicationStatusByNames": {
      "appId": 7,
      "status": "Hired",
      "candidate": {
        "firstName": "John",
        "lastName": "Developer",
        "email": "john.developer@email.com"
      },
      "job": {
        "jobId": 6,
        "title": "Senior Full Stack Developer",
        "status": "Closed"
      }
    }
  }
}
```

**✅ CHECK**:
1. Backend console should show:
   ```
   Triggering side-effects for hired status on job 6...
   Rejection notification sent to sarah.engineer@email.com
   Rejection notification sent to mike.coder@email.com
   Hired status side-effects complete.
   ```

2. Check Resend dashboard: https://resend.com/emails
   - Should see 2 rejection emails sent
   - Subject: "Update on your application for Senior Full Stack Developer at TechCorp"

3. Verify job is closed:
   ```graphql
   {
     jobById(jobId: 6) {
       jobId
       title
       status
     }
   }
   ```
   Response should show: `"status": "Closed"`

---

## SCENARIO 6: NATURAL LANGUAGE TESTING

### Test Natural Language Commands

**Endpoint**: `POST http://localhost:8000/nl2gql?run=true`

**Headers**:
```
Content-Type: application/json
X-User-Role: Recruiter
```

### Example 1: Interview a Candidate

**Request Body**:
```json
{
  "query": "Interview Charlie Brown for the Senior Python Developer position at Google"
}
```

**Expected Response**:
```json
{
  "graphql": "mutation { updateApplicationStatusByNames(...) { ... } }",
  "result": {
    "data": {
      "updateApplicationStatusByNames": {
        "appId": 1,
        "status": "Interviewing",
        ...
      }
    }
  }
}
```

### Example 2: Add a Note

**Request Body**:
```json
{
  "query": "Add a note to Charlie Brown's Google application: Great technical skills, recommend final round"
}
```

### Example 3: Hire Someone

**Request Body**:
```json
{
  "query": "Hire Diana Prince for the Product Manager job at Meta"
}
```

---

## TESTING WITH SEEDED DATA

If you ran `python scripts/seed_db.py`, you have these test accounts:

### Recruiters:
- **Email**: recruiter@google.com | **Password**: password123
- **Email**: hiring@meta.com | **Password**: password123

### Applicants:
- **Charlie Brown** - charlie.brown@email.com | password123
- **Diana Prince** - diana.prince@email.com | password123  
- **Ethan Hunt** - ethan.hunt@email.com | password123
- **Frank Miller** - frank.miller@email.com | password123
- **Grace Hopper** - grace.hopper@email.com | password123

### Pre-existing Jobs:
1. Senior Python Developer @ Google
2. Senior UI/UX Designer @ Figma
3. Product Manager @ Meta
4. Data Scientist @ Netflix (has 3 applicants - perfect for mass rejection test!)
5. Frontend Engineer @ Vercel

### Quick Test with Seeded Data:

**Interview Charlie**:
```graphql
mutation {
  updateApplicationStatusByNames(
    userName: "Charlie Brown"
    jobTitle: "Senior Python Developer"
    companyName: "Google"
    newStatus: "Interviewing"
  ) {
    appId status
    candidate { email }
  }
}
```
Email sent to: charlie.brown@email.com ✅

**Hire Ethan (triggers mass rejection)**:
```graphql
mutation {
  updateApplicationStatusByNames(
    userName: "Ethan Hunt"
    jobTitle: "Data Scientist"
    companyName: "Netflix"
    newStatus: "Hired"
  ) {
    appId status
    job { status }
  }
}
```
- Job closed ✅
- Frank and Grace get rejection emails ✅

---

## EMAIL VERIFICATION CHECKLIST

After running the workflows above, verify in Resend Dashboard:

1. ✅ Interview invitation to john.developer@email.com
2. ✅ Rejection email to sarah.engineer@email.com
3. ✅ Rejection email to mike.coder@email.com
4. ✅ (If using seeded data) Email to charlie.brown@email.com
5. ✅ (If using seeded data) Emails to frank.miller@email.com and grace.hopper@email.com

**Resend Dashboard**: https://resend.com/emails

---

## TROUBLESHOOTING

### No emails being sent?
1. Check backend console for error messages
2. Verify RESEND_API_KEY in `src/backend/.env`
3. Make sure you're using X-User-Role: Recruiter header
4. Check that status is exactly "Interviewing" or "Hired" (case-sensitive)

### GraphQL errors?
1. Verify you're using the correct X-User-Role header
2. Check that user/job names match exactly (case-sensitive)
3. Make sure the application exists before updating status

### Authorization errors?
- Only Recruiters can:
  - updateApplicationStatusByNames
  - addManagerNoteToApplication
- Applicants can:
  - addNoteToApplicationByJob (only their own applications)

---

## SUCCESS CRITERIA

After completing this guide, you should have:
- ✅ Created recruiter and applicant accounts
- ✅ Posted a job
- ✅ Applied to a job
- ✅ Updated application status to "Interviewing" (email sent)
- ✅ Added manager notes
- ✅ Hired a candidate (job closed, mass emails sent)
- ✅ Verified emails in Resend dashboard
- ✅ Tested natural language commands

**All features working perfectly!** 🎉
