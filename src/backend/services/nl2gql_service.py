# src/backend/services/nl2gql_service.py
import os
import requests
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path=env_path)

from ..errors import json_error, unwrap_graphql_errors

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"


def handle_small_talk(user_text: str):
    clean_text = user_text.lower().strip()
    words = clean_text.split()
    
    small_talk_map = {
        "hi": "Hello there! How can I assist with your job data today?",
        "hello": "Hi! I'm ready to convert your requests into GraphQL. What can I do?",
        "hey": "Hey! Let me know what data you need to query or update.",
        "greetings": "Greetings! I'm here to help with your job portal data via NL2GQL.",
        "thanks": "You're welcome! I'm happy to help.",
        "thank you": "My pleasure! Just ask if you have more queries.",
        "wow": "Glad to impress! Do you have a query for me?",
        "cool": "I think so too! Ready for your next command.",
        "awesome": "I strive for excellence! Ready for a command.",
        "oops": "Mistakes happen! Please try your query again.",
        "sorry": "No worries at all. What is your request?",
        "how are you": "I'm a GraphQL assistant, operating perfectly! What query can I run for you?",
        "what's up": "Just monitoring the database for your requests. What can I do for you?",
        "how are you doing today": "I'm a GraphQL assistant, operating perfectly! What query can I run for you?",
    }
    
    keyword_responses = {
        "by the way": "Interesting point. Do you have a job or user query for me?",
        "i mean": "I understand. Please formulate your query clearly.",
        "just saying": "Got it. I'm waiting for a command that maps to GraphQL.",
        "you know": "I know what you mean. Focus on what data you need.",
        "hold on": "Okay, I'll hold. Let me know when you have a request.",
        "excuse me": "No problem. How can I help with the data?",
        "can you help me": "Absolutely! I can help by converting your request into a GraphQL query.",
        "can i ask": "You can ask. I can answer if it involves querying or mutating job portal data.",
    }
    
    default_response_payload = {
        "graphql": "Small talk handled by service logic", 
        "result": {
            "response": (
                "Hello! I'm your GraphQL assistant. I can help with job portal data. "
                "Try asking me to:\n- **Find** jobs: *find jobs for Java developer in London*\n"
                "- **Update** your profile: *update my professional title to Senior Developer*"
            )
        }
    }
    
    if clean_text in small_talk_map:
        return {"graphql": "Small talk handled by service logic", "result": {"response": small_talk_map[clean_text]}}, 200
        
    for key, response in keyword_responses.items():
        if key in clean_text:
            return {"graphql": "Small talk handled by service logic", "result": {"response": response}}, 200

    if words:
        is_greeting = words[0] in ["hi", "hello", "hey"]
        is_vocative = "assistant" in words or "bot" in words or "jobchat" in words
        
        if (is_greeting or is_vocative) and len(words) <= 5:
            return default_response_payload, 200
        
    return None

def build_nl2gql_prompt(user_text: str, schema_sdl: str, user_context: Optional[dict]) -> str:
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_day = datetime.now().strftime("%A") 
    
    context_str = ""
    if user_context and user_context.get("UserID"):
        user_id = user_context["UserID"]
        first_name = user_context.get("firstName", "the user")
        role = user_context.get("role", "Unknown")
        context_str = (
            f"\n\nContext:\n"
            f"- The request is from a logged-in user named '{first_name}' with UserID: {user_id}.\n"
            f"- Role: {role}.\n"
            f"- When the user refers to 'me', 'my', or 'I', you MUST use their UserID ({user_id}) to target the operation.\n"
        )

    return (
        f"Current System Time: {current_time_str} ({current_day}).\n"
        "You are an expert GraphQL assistant. Convert the request into a single GraphQL operation.\n"
        f"{context_str}"
        "\nKey Instructions (ROLE SPECIFIC):\n"
        "- **RECRUITER ROLE:**\n"
        "  1. Can CREATE jobs: `createJob`. **Hiring Manager is REQUIRED**: If creating a job, you MUST extract the `hiringManagerName` (e.g., 'Sarah Connor') and include it in the input.\n"
        "  2. Can VIEW applications: `jobs { applicants { ... } }`.\n"
        "  3. CANNOT invite, hire, or schedule interviews.\n"
        
        "- **MANAGER ROLE:**\n"
        "  1. Can INVITE candidates: `updateApplicationStatusByNames(..., newStatus: \"InterviewInviteSent\")`. This triggers the candidate email.\n"
        "  2. Can EXTEND OFFERS: `updateApplicationStatusByNames(..., newStatus: \"Offered\")`.\n"
        "  3. Can HIRE: `updateApplicationStatusByNames(..., newStatus: \"Hired\")`.\n"
        "  4. Can REJECT: `updateApplicationStatusByNames(..., newStatus: \"Rejected\")`.\n"
        "  5. Can SET AVAILABILITY: `setMyAvailability(...)`.\n"
        "  6. Can VIEW SCHEDULE: `myBookedInterviews`.\n"
        "  7. Can ADD NOTES: `addManagerNoteToApplication`.\n"
        "  8. Can VIEW JOBS: use the `jobs` query WITHOUT the `posterUserId` argument (the system automatically filters for their managed jobs).\n"
        
        "- **APPLICANT ROLE:**\n"
        "  1. Apply: `apply`.\n"
        "  2. Apply with Resume: `applyWithResume`.\n"
        "  3. Accept Offer: `acceptOffer`.\n"
        "  4. Reject Offer: `rejectOffer`.\n"
        "  5. Schedule Interview: `selectInterviewSlot`.\n"
        
        "\nGeneral & Field Logic:\n"
        # --- FS.Y1.2: PERSONAL DASHBOARD LOGIC ---
        "- If the user asks to **'show my profile'**, **'my details'**, or **'who am I'**, use the `userById` query with their UserID from context.\n"
        # -----------------------------------------
        "- To filter users by experience, use the `yearsOfExperience_gte: Int` argument.\n"
        "- To filter users by citizenship, use the `isUSCitizen: Boolean` argument.\n"
        "- When a user wants to **ADD** skills to **their own profile**, you **MUST** use the `addSkillsToUser` mutation. For all other user profile updates, use `updateUser`.\n"
        "- When a user asks about **'my applications'**, you **MUST** use the `applications` query and filter it using the `userId` from the context.\n"
        "  **You MUST select and return these fields for each application:** `{ appId status userId jobId job { jobId title company } notes }`.\n"
        "- When a user wants to **'add a note'** to their application (Applicant only), use the `addNoteToApplicationByJob` mutation.\n"
        "- When a user asks **'how many applications'** or for a **'count of applicants'**, you **MUST** query the relevant job and include the `applicationCount` field.\n"
        
        "- When a user wants to see **applicants**, **candidates**, or people who **applied** for a job, you **MUST** query the `jobs` field. **You MUST select `jobId`, `title`, and `company` for the Job itself.** Then request the nested `applicants` field. **For every applicant, you MUST select:** `firstName`, `lastName`, `professionalTitle`, `skills`, `city`, `country`, `applicationStatus`, `resume_url`, `interviewTime`, and `UserID`.\n"
        
        "- When a user wants to **ADD** skills to a job, you **MUST** use the `addSkillsToJob` mutation. For all other job updates, use the `updateJob` mutation.\n"
        "- When a user wants to **UPDATE** a job by its title and company, you **MUST** use the `updateJobByFields` mutation.\n"
        
        "- **CITIZENSHIP LOGIC (CRITICAL):**\n"
        "  1. If the user asks to **CREATE** a job with 'US Citizen' requirements, use `createJob(input: {..., requires_us_citizenship: true})`.\n"
        "  2. If the user asks to **UPDATE** a job to require citizenship, use `updateJobByFields(..., input: {requires_us_citizenship: true})`.\n"
        
        "- To set a **minimum degree year** for a job, use `updateJobByFields(..., input: {minimum_degree_year: 2015})` or `updateJob(..., input: {minimum_degree_year: 2015})`.\n"
        "- When the user wants to 'apply' a person to a job, ALWAYS use the `apply` mutation. **You MUST return these specific fields inside the mutation block: { appId status job { title } }**.\n"
        "- If the user asks to 'apply with my resume' or mentions a specific resume, use the `applyWithResume` mutation.\n"
        "- When a user wants to **DELETE** or **REMOVE** a job using its title and company, you **MUST** use the `deleteJobByFields` mutation.\n"
        "- For other actions, use the appropriate query or mutation.\n"
        "- If the user's request cannot be mapped to any field in the schema, return the single word: INVALID.\n"
        "- Do not make up fields or assume logic not present in the schema.\n\n"
        "- **SCHEDULING:** If the user asks to **'schedule'**, **'book'**, or **'invite'** a candidate for an interview manually (Manager only), use the `bookInterviewByNaturalLanguage` mutation. Calculate the `startTimeISO` based on the Current System Time provided above.\n"
        "- Do not make up fields. Return only the GraphQL.\n\n"
        "Schema:\n"
        f"{schema_sdl}\n\n"
        "User request:\n"
        f"\"{user_text}\""
    )

def extract_graphql(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if "query" in part or "mutation" in part or "{" in part:
                return part.replace("graphql", "").strip()
    return text.strip()

def process_nl2gql_request(user_text: str, schema_sdl: str, run_graphql: bool, graphql_executor_fn, user_context: Optional[dict]):
    small_talk_response = handle_small_talk(user_text)
    if small_talk_response:
        return small_talk_response
    
    if not OLLAMA_API_KEY:
        return json_error("NL2GQL Service Error: OLLAMA_API_KEY is missing.", 500)
        
    prompt = build_nl2gql_prompt(user_text, schema_sdl, user_context)

    headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}

    try:
        resp = requests.post(
            OLLAMA_GENERATE_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            headers=headers,
            timeout=180, 
        )
    except requests.exceptions.RequestException as e:
        return json_error(f"Ollama network error: {e}", 502)

    if not resp.ok:
        try:
            err_details = resp.json().get("error", resp.text)
            return json_error(f"LLM Error {resp.status_code}: {err_details}", 502)
        except (json.JSONDecodeError, ValueError):
            return json_error(f"Ollama returned a non-JSON error (Status: {resp.status_code}).", 502)

    try:
        gen_body = resp.json()
        gen = gen_body.get("response", "")
        gql = extract_graphql(gen)
    except (ValueError, IndexError):
        return json_error("Failed to parse the response from the LLM.", 502)

    if not gql or gql.strip().upper() == "INVALID":
        return json_error("Invalid request.", 400)

    if not run_graphql:
        return {"graphql": gql}, 200

    success, result = graphql_executor_fn({"query": gql})
    wrapped_error = unwrap_graphql_errors(result)
    if wrapped_error: return wrapped_error 

    return {"graphql": gql, "result": result}, (200 if success else 400)
    
