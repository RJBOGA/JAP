import json
import os
import requests
import streamlit as st
# from dotenv import load_dotenv # Uncomment if you need to load .env in frontend locally for non-Streamlit Cloud use

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Job Seeker MVP — Chat", layout="wide")

# --- Environment and Endpoint Setup ---
# Use st.secrets for Streamlit Cloud deployment, fallback to os.getenv for local
# If running locally and using .env, ensure 'python-dotenv' is installed and uncomment load_dotenv
# load_dotenv(os.path.join(os.path.dirname(__file__), '.env')) # Load frontend .env if needed

NL2GQL_ENDPOINT = st.secrets.get("NL2GQL_ENDPOINT", os.getenv("NL2GQL_ENDPOINT", "http://localhost:8000/nl2gql"))

# --- Streamlit UI ---
st.title("Job Seeker Chat")

# Optional: Display the endpoint for debugging
# st.caption(f"NL→GQL endpoint: {NL2GQL_ENDPOINT}")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Ask me to create, list, update, or delete users in plain English."}
    ]

# Render chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Chat input
user_prompt = st.chat_input("Type a request like 'create a user named Raj etc.,'.")
if user_prompt:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Call backend NL2GQL and show response
    try:
        # Send the user prompt to the NL2GQL endpoint
        resp = requests.post(NL2GQL_ENDPOINT, json={"query": user_prompt}, timeout=90)

        # Handle non-200 responses from the backend
        if resp.status_code != 200:
            try:
                err = resp.json().get("error", {})
                err_msg = err.get("message") if isinstance(err, dict) else None
            except Exception:
                err_msg = None # Fallback if backend doesn't return valid JSON for error

            if not err_msg:
                err_msg = f"NL→GQL service returned status {resp.status_code}. Unable to parse error message."

            # Helpful examples to show under the message for user guidance
            examples = [
                "find user named Raju",
                "find user born on 2000-05-01",
                "update user Raju’s last name to Booo",
                "delete user named Raju born on 2000-05-01",
            ]

            assistant_text = f"**Error:** {err_msg}\n\n**Examples:**\n\n" + "\n\n".join([f'"{e}"' for e in examples])
        else:
            # Successfully got a 200 response
            data = resp.json()
            gql = data.get("graphql", "")
            result = data.get("result", {})

            # Format the assistant's response
            assistant_text = (
                f"**Generated GraphQL:**\n\n```graphql\n{gql}\n```\n\n"
                f"**Result:**\n\n```json\n{json.dumps(result, indent=2)}\n```"
            )
    except requests.exceptions.Timeout:
        assistant_text = "Error: Request to NL→GQL service timed out. Please try again."
    except requests.exceptions.ConnectionError:
        assistant_text = "Error: Could not connect to the NL→GQL service. Is the backend running?"
    except Exception as e:
        assistant_text = f"An unexpected error occurred: {e}"

    # Show assistant's response and add to chat history
    with st.chat_message("assistant"):
        st.markdown(assistant_text)
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})