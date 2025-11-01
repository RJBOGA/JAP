import os
import requests
import json
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '../../.env')
print(f"Loading .env from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")
load_dotenv(dotenv_path=env_path)

from ..errors import json_error, unwrap_graphql_errors

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "2a5870ffa8ab469b879ab02999b684db.28nZHl4ZWnBXzrvzWFpiJ7DT")
print(f"OLLAMA_HOST loaded as: {OLLAMA_HOST}")
print(f"OLLAMA_MODEL loaded as: {OLLAMA_MODEL}")
print(f"OLLAMA_API_KEY loaded: {'Yes' if OLLAMA_API_KEY else 'No'}")
OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"

def build_nl2gql_prompt(user_text: str, schema_sdl: str) -> str:
    """Builds the prompt for the LLM to convert natural language to GraphQL."""
    # Updated instructions to reflect the new 'apply(userName: ...)' mutation
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
    """Extract GraphQL code block from model output."""
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
        return json_error(f"Ollama network error: {e}", 502)

    if not resp.ok:
        return json_error(f"Ollama error {resp.status_code}", 502)

    try:
        gen_body = resp.json()
    except ValueError:
        return json_error("Ollama returned non-JSON response", 502)

    gen = gen_body.get("response", "")
    gql = extract_graphql(gen)

    if not gql or gql.strip().upper() == "INVALID":
        return json_error(
            "Out of scope. Your request could not be mapped to a valid operation. Try asking about users or jobs.",
            400
        )

    if not run_graphql:
        return {"graphql": gql}, 200

    # Execute generated GraphQL
    success, result = graphql_executor_fn({"query": gql})
    
    # Check for GraphQL-level errors (like our ValueErrors from the resolver)
    wrapped_error = unwrap_graphql_errors(result)
    if wrapped_error:
        return wrapped_error # This is now a clean (payload, status) tuple

    # Success case
    return {"graphql": gql, "result": result}, (200 if success else 400)