import os
import requests
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '../../.env')
print(f"Loading .env from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")
load_dotenv(dotenv_path=env_path)

from ..errors import json_error, unwrap_graphql_errors

# Ensure these are set to the cloud values
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY") # Read directly from env
print(f"OLLAMA_HOST loaded as: {OLLAMA_HOST}")
print(f"OLLAMA_MODEL loaded as: {OLLAMA_MODEL}")
print(f"OLLAMA_API_KEY loaded: {'Yes' if OLLAMA_API_KEY else 'No'}")
OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"


# --- ENHANCED FUNCTION: Small Talk Interceptor (Handles Small Talk, Vocatives, Discourse Markers, Idioms) ---
def handle_small_talk(user_text: str):
    """
    Checks for simple conversational phrases (greetings, interjections, etc.)
    and returns a predefined response to bypass the LLM.
    """
    
    # --- Category 1: Direct Matches (Small Talk & Interjections) ---
    small_talk_map = {
        # Greetings
        "hi": "Hello there! How can I assist with your job data today?",
        "hello": "Hi! I'm ready to convert your requests into GraphQL. What can I do?",
        "hey": "Hey! Let me know what data you need to query or update.",
        "greetings": "Greetings! I'm here to help with your job portal data via NL2GQL.",
        
        # Gratitude
        "thanks": "You're welcome! I'm happy to help.",
        "thank you": "My pleasure! Just ask if you have more queries.",
        
        # Interjections / Exclamations
        "wow": "Glad to impress! Do you have a query for me?",
        "cool": "I think so too! Ready for your next command.",
        "awesome": "I strive for excellence! Ready for a command.",
        "oops": "Mistakes happen! Please try your query again.",
        "sorry": "No worries at all. What is your request?",
        
        # Phatic Expressions (Conversation management)
        "how are you": "I'm a GraphQL assistant, but I'm operating perfectly! What query can I run?",
        "what's up": "Just monitoring the database for your requests. What can I do for you?",
        "how are you doing today": "I'm a GraphQL assistant, but I'm operating perfectly! What query can I run?",
    }
    
    # --- Category 2: Idioms, Common Phrases & Discourse Markers (Keyword Matching) ---
    keyword_responses = {
        "by the way": "Interesting point. Do you have a job or user query for me?",
        "i mean": "I understand. Please formulate your query clearly.",
        "just saying": "Got it. I'm waiting for a command that maps to GraphQL.",
        "you know": "I know what you mean. Focus on what data you need.",
        "hold on": "Okay, I'll hold. Let me know when you have a request.",
        "excuse me": "No problem. How can I help with the data?",
        "long time no see": "It's good to be back in the chat! Ready for a query.",
        "what the hell": "Please keep the conversation focused on data queries.",
        "what the f": "Please keep the conversation focused on data queries.",
        "can you help me": "Absolutely! I can help by converting your request into a GraphQL query.",
        "can i ask": "You can ask. I can answer if it involves querying or mutating job portal data.",
    }
    
    # Default conversational response if a simple greeting/interjection is matched
    default_response = (
        "Hello! I'm your GraphQL assistant. I can help you with job portal data. "
        "Try asking me to: \n- **Create** a user: *create a user named Jane Doe born on 1990-01-01*\n"
        "- **Find** jobs: *find jobs for Java developer in London*\n"
        "- **Apply** to a job: *apply user Raju B to Java Developer at MyCompany*"
    )
    
    # Normalize input
    clean_text = user_text.lower().strip()
    words = clean_text.split()
    
    # 1. Check for Direct Matches (Handles most greetings/interjections)
    if clean_text in small_talk_map:
        response = small_talk_map[clean_text]
        return {"graphql": "Small talk handled by service logic", "result": {"response": response}}, 200
        
    # Check for short multi-word exact match for "how are you doing today"
    if clean_text == "how are you doing today":
        return {"graphql": "Small talk handled by service logic", "result": {"response": small_talk_map["how are you doing today"]}}, 200

    # 2. Check for Keyword Matches (Handles Idioms, Discourse Markers, and multi-word Phatic)
    for key, response in keyword_responses.items():
        if key in clean_text:
            return {"graphql": "Small talk handled by service logic", "result": {"response": response}}, 200

    # 3. Check for multi-word short greetings/Vocatives
    if words:
        is_greeting = words[0] in ["hi", "hello", "hey"]
        is_vocative = "assistant" in words or "bot" in words
        
        if (is_greeting or is_vocative) and len(words) <= 5:
            # Return the default, guiding response
            return {"graphql": "Small talk handled by service logic", "result": {"response": default_response}}, 200
        
    return None

# --- END ENHANCED FUNCTION ---


def build_nl2gql_prompt(user_text: str, schema_sdl: str) -> str:
    # ... (remains the same) ...
    return (
        "You are an expert GraphQL assistant. Your task is to convert the user's natural language request "
        "into a single, valid GraphQL operation that adheres strictly to the provided schema. "
        "Return ONLY the GraphQL operation with no explanations or markdown fences.\n\n"
        "Key Instructions:\n"
        "- When the user wants to 'apply' a person to a job, ALWAYS use the `apply` mutation. It takes a single `userName` string (e.g., 'Raju boo' or 'Priya Sharma'), a `jobTitle`, and an optional `companyName`.\n"
        "- For other actions, use the appropriate query or mutation (e.g., `users`, `jobs`, `createUser`, `createJob`).\n"
        "- If the user's request cannot be mapped to any field in the schema, return the single word: INVALID.\n"
        "- Do not make up fields or assume logic not present in the schema.\n\n"
        "Schema:\n"
        f"{schema_sdl}\n\n"
        "User request:\n"
        f"{user_text}"
    )

def extract_graphql(text: str) -> str:
    # ... (remains the same) ...
    if "```" in text:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            block = parts[i]
            if block.strip().startswith("graphql"):
                lines = block.splitlines()
                return "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        for i in range(1, len(parts), 2):
            if parts[i].strip():
                return parts[i].strip()
    return text.strip()

def process_nl2gql_request(user_text: str, schema_sdl: str, run_graphql: bool, graphql_executor_fn):
    """
    Processes a natural language query, converts to GraphQL, and optionally executes it.
    This function now consistently returns a tuple: (payload_dict, status_code).
    """
    
    # --- Check for small talk first ---
    small_talk_response = handle_small_talk(user_text)
    if small_talk_response:
        return small_talk_response
    # --- END CHECK ---
    
    # Pre-check for API key before making the call
    if not OLLAMA_API_KEY:
        return json_error("NL2GQL Service Error: OLLAMA_API_KEY is missing in environment configuration.", 500)
        
    prompt = build_nl2gql_prompt(user_text, schema_sdl)

    headers = {}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    try:
        resp = requests.post(
            OLLAMA_GENERATE_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            headers=headers,
            timeout=90,
        )
    except requests.exceptions.Timeout:
        return json_error("Upstream NL generation timed out", 504)
    except requests.exceptions.RequestException as e:
        # This catches general network errors like DNS failure or SSL/Cert issues
        return json_error(f"Ollama network error: {e}. Check OLLAMA_HOST/URL.", 502)

    if not resp.ok:
        try:
            err_details = resp.json().get("error", resp.text)
            if resp.status_code == 401 or resp.status_code == 403:
                msg = f"LLM Authorization Failed. Check OLLAMA_API_KEY. Details: {err_details}"
            else:
                msg = f"LLM Error {resp.status_code}: {err_details}"
            
            return json_error(msg, 502)

        except (json.JSONDecodeError, ValueError):
            return json_error(f"Ollama returned non-JSON error response (Status: {resp.status_code}).", 502)

    try:
        gen_body = resp.json()
    except ValueError:
        return json_error("Ollama returned non-JSON response on success.", 502)

    gen = gen_body.get("response", "")
    gql = extract_graphql(gen)

    if not gql or gql.strip().upper() == "INVALID":
        return json_error(
            "Out of scope. Your request could not be mapped to a valid operation. Try asking about users or jobs (or be more specific).",
            400
        )

    if not run_graphql:
        return {"graphql": gql}, 200

    # Execute generated GraphQL
    success, result = graphql_executor_fn({"query": gql})
    
    # Check for GraphQL-level errors (like our ValueErrors from the resolver)
    wrapped_error = unwrap_graphql_errors(result)
    if wrapped_error:
        return wrapped_error 

    # Success case
    return {"graphql": gql, "result": result}, (200 if success else 400)