# src/backend/app.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import bcrypt
import requests
from flask_cors import CORS
from flask import Flask, jsonify, request
from ariadne import load_schema_from_path, make_executable_schema, graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
from datetime import datetime

# Import backend modules
from src.backend.models.user_models import UserProfileType
from src.backend.errors import handle_http_exception, handle_value_error, handle_generic_exception, json_error
from src.backend.services.nl2gql_service import process_nl2gql_request
from src.backend.repository import user_repo
from src.backend.db import ensure_user_counter, ensure_job_counter, ensure_application_counter, next_user_id

# Import resolvers
from src.backend.resolvers.user_resolvers import query as user_query, mutation as user_mutation
from src.backend.resolvers.job_resolvers import query as job_query, mutation as job_mutation
from src.backend.resolvers.application_resolvers import query as app_query, mutation as app_mutation, application as application_object

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# --- Flask app setup ---
app = Flask(__name__)
CORS(app)
explorer_html = ExplorerGraphiQL().html(None)

# --- Load GraphQL schema ---
schema_path = os.path.join(os.path.dirname(__file__), "schema.graphql")
type_defs = load_schema_from_path(schema_path)
schema = make_executable_schema(
    type_defs,
    [user_query, job_query, app_query],
    [user_mutation, job_mutation, app_mutation],
    application_object
)

# Initialize database counters
ensure_user_counter()
ensure_job_counter()
ensure_application_counter()

# --- Error Handlers ---
@app.errorhandler(HTTPException)
def http_error(e): return handle_http_exception(e)
@app.errorhandler(ValueError)
def value_error(e): return handle_value_error(e)
@app.errorhandler(Exception)
def unhandled_exception(e): return handle_generic_exception(e)

# --- GraphQL endpoints ---
@app.route("/graphql", methods=["GET"])
def graphql_explorer(): return explorer_html, 200
@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json(silent=True)
    user_role = request.headers.get("X-User-Role", "Applicant")
    success, result = graphql_sync(
        schema, 
        data, 
        context_value={"request": request, "user_role": user_role}, 
        debug=app.debug
    )
    return jsonify(result), (200 if success else 400)

# --- Health check ---
@app.route("/")
def health(): return jsonify({"status": "Backend is running!"}), 200

# --- NL2GQL Endpoint ---
@app.route("/nl2gql", methods=["POST"])
def nl2gql():
    data = request.get_json(silent=True) or {}
    user_text = data.get("query", "")
    user_context = data.get("userContext")
    run_graphql = request.args.get("run", "true").lower() != "false"
    with open(schema_path, "r", encoding="utf-8") as f: schema_sdl = f.read()

    # --- THIS IS THE FUNCTION THAT NEEDED TO BE FIXED ---
    def execute_graphql_query(gql_data):
        # 1. Read the role from the header within this function's scope
        user_role = request.headers.get("X-User-Role", "Applicant")
        
        # 2. Pass the role into the context for this specific execution
        return graphql_sync(
            schema, 
            gql_data, 
            context_value={"request": request, "user_role": user_role}, 
            debug=app.debug
        )

    payload, status_code = process_nl2gql_request(
        user_text, schema_sdl, run_graphql, execute_graphql_query, user_context
    )
    return jsonify(payload), status_code

# --- User Registration Endpoint ---
@app.route("/register", methods=["POST"])
def register_user():
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid JSON body"}), 400
    
    email, password, first_name, last_name, role = data.get("email"), data.get("password"), data.get("firstName"), data.get("lastName"), data.get("role")
    if not all([email, password, first_name, last_name, role]):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        validated_role = UserProfileType.from_str(role).value
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if user_repo.find_user_by_email(email):
        return jsonify({"error": f"An account with the email '{email}' already exists."}), 409

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user_doc = {
        "UserID": next_user_id(), "email": email.lower(), "password": hashed_password,
        "firstName": first_name, "lastName": last_name, "role": validated_role,
        "phone_number": None, "city": None, "state_province": None, "country": None,
        "linkedin_profile": None, "portfolio_url": None, "highest_qualification": None,
        "years_of_experience": None, "createdAt": datetime.utcnow().isoformat(),
        "dob": None, "skills": [], "professionalTitle": None
    }

    try:
        user_repo.insert_user(new_user_doc)
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"An internal error occurred: {e}"}), 500
    
# --- User Login Endpoint ---
@app.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid JSON body"}), 400
    email, password = data.get("email"), data.get("password")
    if not email or not password: return jsonify({"error": "Email and password are required"}), 400

    user = user_repo.find_user_by_email(email)
    if not user: return jsonify({"error": "Invalid email or password"}), 401

    if bcrypt.checkpw(password.encode('utf-8'), user.get("password")):
        user_data = user_repo.to_user_output(user)
        return jsonify({"message": "Login successful!", "user": user_data}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

if __name__ == "__main__":
    print("🚀 Starting Flask server on http://localhost:8000 ...")
    app.run(host="0.0.0.0", port=8000, debug=True)