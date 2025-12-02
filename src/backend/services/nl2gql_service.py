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


# --- RESTORED: The more comprehensive small talk handler ---
def handle_small_talk(user_text: str):
    """
    Checks for a wide range of conversational phrases (greetings, idioms, etc.)
    and returns a predefined friendly response to bypass the LLM.
    """
    clean_text = user_text.lower().strip()
    words = clean_text.split()
    
    # --- Category 1: Direct Matches (Greetings, Gratitude, Interjections) ---
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
    
    # --- Category 2: Idioms, Common Phrases & Discourse Markers (Keyword Matching) ---
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
    
    # 1. Check for Direct Matches
    if clean_text in small_talk_map:
        return {"graphql": "Small talk handled by service logic", "result": {"response": small_talk_map[clean_text]}}, 200
        
    # 2. Check for Keyword Matches
    for key, response in keyword_responses.items():
        if key in clean_text:
            return {"graphql": "Small talk handled by service logic", "result": {"response": response}}, 200

    # 3. Check for short multi-word greetings or questions to the bot
    if words:
        is_greeting = words[0] in ["hi", "hello", "hey"]
        is_vocative = "assistant" in words or "bot" in words or "jobchat" in words
        
        if (is_greeting or is_vocative) and len(words) <= 5:
            # Return the default, guiding response for these cases
            return default_response_payload, 200
        
    return None

# --- UPDATED Prompt Builder (Keeps the userContext logic) ---
def build_nl2gql_prompt(user_text: str, schema_sdl: str, user_context: Optional[dict]) -> str:
    # 1. Get Current Context for the AI
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_day = datetime.now().strftime("%A") # e.g., "Monday"
    
    context_str = ""
    if user_context and user_context.get("UserID"):
        user_id = user_context["UserID"]
        first_name = user_context.get("firstName", "the user")
        context_str = (
            f"\n\nContext:\n"
            f"- The request is from a logged-in user named '{first_name}' with UserID: {user_id}.\n"
            f"- When the user refers to 'me', 'my', or 'I', you MUST use their UserID ({user_id}) to target the operation (e.g., in an `updateUser` mutation).\n"
        )

    return (
        f"Current System Time: {current_time_str} ({current_day}).\n"
        "You are an expert GraphQL assistant. Your task is to convert the user's natural language request "
        "into a single, valid GraphQL operation that adheres strictly to the provided schema. "
        "Return ONLY the GraphQL operation with no explanations or markdown fences."
        f"{context_str}"
        "\n\nKey Instructions:\n"
        "- To filter users by experience, use the `yearsOfExperience_gte: Int` argument. For '5 years of experience', use `users(yearsOfExperience_gte: 5)`.\n"
        "- To filter users by citizenship, use the `isUSCitizen: Boolean` argument. For 'who are US citizens', use `users(isUSCitizen: true)`.\n"
        "- When a user wants to **ADD** skills to **their own profile**, you **MUST** use the `addSkillsToUser` mutation. For all other user profile updates, use `updateUser`.\n"
        "- When a user asks about **'my applications'**, you **MUST** use the `applications` query and filter it using the `userId` from the context.\n"
        "- When a user wants to **'add a note'** to their application, you **MUST** use the `addNoteToApplicationByJob` mutation.\n"
        "- When a user asks **'how many applications'** or for a **'count of applicants'**, you **MUST** query the relevant job and include the `applicationCount` field.\n"
        "- If the user says **'Hire [Name]'** or **'Lets hire [Name]'**, you MUST use the `updateApplicationStatusByNames` mutation with `newStatus: \"Hired\"`. Extract the `jobTitle` and `companyName` from the user's request.\n"
        "- If the user says **'Reject [Name]'**, use `updateApplicationStatusByNames` with `newStatus: \"Rejected\"`.\n"
        "- When a user wants to **UPDATE the STATUS** of an application (e.g., 'interview', 'reject', 'hire'), you **MUST** use the `updateApplicationStatusByNames` mutation. **For this mutation, you MUST extract the candidate's full name, the exact job title, and the company name.**\n"
        "- When a user wants to see **applicants**, **candidates**, or people who **applied** for a job, you **MUST** query the `jobs` field. **You MUST select `jobId`, `title`, and `company` for the Job itself.** Then request the nested `applicants` field. **For every applicant, you MUST select:** `firstName`, `lastName`, `professionalTitle`, `skills`, `city`, `country`, `applicationStatus`, `resume_url`, `interviewTime`, and `UserID`.\n\n"
        "- When a user wants to **ADD** skills to a job, you **MUST** use the `addSkillsToJob` mutation. For all other job updates, use the `updateJob` mutation.\n"
        "- When a user wants to **UPDATE** a job by its title and company (e.g., 'update the Senior Python Developer job at Google'), you **MUST** use the `updateJobByFields` mutation with the title and company as identifiers.\n"
        # --- FIXED CITIZENSHIP LOGIC INSTRUCTIONS ---
        "- **CITIZENSHIP LOGIC (CRITICAL):**\n"
        "  1. If the user asks to **CREATE** a job with 'US Citizen' requirements, use `createJob(input: {..., requires_us_citizenship: true})`.\n"
        "  2. If the user asks to **UPDATE** a job to require citizenship, use `updateJobByFields(..., input: {requires_us_citizenship: true})`.\n"
        # ---------------------------------------------
        "- To set a **minimum degree year** for a job, use `updateJobByFields(..., input: {minimum_degree_year: 2015})` or `updateJob(..., input: {minimum_degree_year: 2015})`.\n"
        "- When the user wants to 'apply' a person to a job, ALWAYS use the `apply` mutation.\n"
        "- When a user wants to **DELETE** or **REMOVE** a job using its title and company, you **MUST** use the `deleteJobByFields` mutation.\n"
        "- For other actions, use the appropriate query or mutation.\n"
        "- If the user's request cannot be mapped to any field in the schema, return the single word: INVALID.\n"
        "- Do not make up fields or assume logic not present in the schema.\n\n"
        "- If the user asks to **'schedule'**, **'book'**, or **'invite'** a candidate for an interview, you MUST use the `bookInterviewByNaturalLanguage` mutation. Calculate the `startTimeISO` based on the Current System Time provided above (e.g., 'next friday 10am' -> 'YYYY-MM-DDTHH:MM:00').\n"
        "- Do not make up fields. Return only the GraphQL.\n\n"
        "Schema:\n"
        f"{schema_sdl}\n\n"
        "User request:\n"
        f"\"{user_text}\""
    )

def extract_graphql(text: str) -> str:
    """Extracts a GraphQL query from a markdown block or plain text."""
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if "query" in part or "mutation" in part or "{" in part:
                return part.replace("graphql", "").strip()
    return text.strip()

# --- UPDATED Service Processor (Keeps the userContext logic) ---
def process_nl2gql_request(user_text: str, schema_sdl: str, run_graphql: bool, graphql_executor_fn, user_context: Optional[dict]):
    small_talk_response = handle_small_talk(user_text)
    if small_talk_response:
        return small_talk_response
    
    if not OLLAMA_API_KEY:
        return json_error("NL2GQL Service Error: OLLAMA_API_KEY is missing in environment configuration.", 500)
        
    prompt = build_nl2gql_prompt(user_text, schema_sdl, user_context)

    headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}

    try:
        resp = requests.post(
            OLLAMA_GENERATE_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            headers=headers,
            timeout=90,
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
        return json_error("Your request could not be mapped to a valid operation. Please try rephrasing.", 400)

    if not run_graphql:
        return {"graphql": gql}, 200

    success, result = graphql_executor_fn({"query": gql})
    
    wrapped_error = unwrap_graphql_errors(result)
    if wrapped_error:
        return wrapped_error 

    return {"graphql": gql, "result": result}, (200 if success else 400)