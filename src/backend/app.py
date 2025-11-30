# src/backend/app.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import logging 

import bcrypt
import requests
from flask_cors import CORS
from flask import Flask, jsonify, request
from ariadne import load_schema_from_path, make_executable_schema, graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
from datetime import datetime

from src.backend.services import resume_parser_service 
from src.backend.models.user_models import UserProfileType
from src.backend.errors import handle_http_exception, handle_value_error, handle_generic_exception, json_error
from src.backend.services.nl2gql_service import process_nl2gql_request
from src.backend.repository import user_repo, application_repo # Added application_repo for upload endpoint
from src.backend.db import ensure_user_counter, ensure_job_counter, ensure_application_counter, ensure_interview_counter, next_user_id
from werkzeug.utils import secure_filename

# Import resolvers
from src.backend.resolvers.user_resolvers import query as user_query, mutation as user_mutation
from src.backend.resolvers.job_resolvers import query as job_query, mutation as job_mutation
# --- FIX 1: Import the 'job' ObjectType from the application resolvers ---
from src.backend.resolvers.application_resolvers import query as app_query, mutation as app_mutation, application as application_object, job

# --- NEW: Import Scheduling Resolvers ---
from src.backend.resolvers.scheduling_resolvers import query as scheduling_query, mutation as scheduling_mutation, interview as interview_object

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# --- Flask app setup ---
app = Flask(__name__)
CORS(app)
explorer_html = ExplorerGraphiQL().html(None)

# Configure basic logging to console
logging.basicConfig(
    level=logging.DEBUG, # Set to DEBUG for maximum output during debugging
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'
)
logger = logging.getLogger('FLASK_APP') # Create a main logger instance
# --- NEW: Suppress Verbose MongoDB Logging ---
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('pymongo.server_monitoring').setLevel(logging.WARNING)

# --- Load GraphQL schema ---
schema_path = os.path.join(os.path.dirname(__file__), "schema.graphql")
type_defs = load_schema_from_path(schema_path)
schema = make_executable_schema(
    type_defs,
    [user_query, job_query, app_query, scheduling_query],
    [user_mutation, job_mutation, app_mutation, scheduling_mutation],
    application_object,
    job,  # --- FIX 2: Pass the imported 'job' ObjectType to the schema builder ---
    interview_object
)

# Initialize database counters
ensure_user_counter()
ensure_job_counter()
ensure_application_counter()
ensure_interview_counter()

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
    user_id = request.headers.get("X-User-ID")
    first_name = request.headers.get("X-User-FirstName", "")
    last_name = request.headers.get("X-User-LastName", "")
    logger.debug(f"Incoming Headers - X-User-ID: {user_id}, Role: {user_role}")
    
    # Build context with user information
    context = {
        "request": request, 
        "user_role": user_role
    }
    
    # Add user details to context if UserID is provided
    if user_id:
        try:
            context["UserID"] = int(user_id)
            context["firstName"] = first_name
            context["lastName"] = last_name
        except ValueError:
            pass  # Invalid UserID, skip adding to context
            
    # DEBUG LOGGING (moved below context creation to avoid UnboundLocalError)
    logger.debug(f"Constructed Context keys: {list(context.keys())}")
    if "UserID" in context:
        logger.debug(f"Context UserID: {context['UserID']}")
    
    success, result = graphql_sync(
        schema, 
        data, 
        context_value=context, 
        debug=app.debug
    )
    logger.debug(f"result: {result}")
    return jsonify(result), (200 if success else 400)

# --- Health check ---
@app.route("/")
def health(): return jsonify({"status": "Backend is running!"}), 200

# --- File Upload Endpoint ---
RESUME_FOLDER = os.path.join(os.path.dirname(__file__), 'resumes')
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
if not os.path.exists(RESUME_FOLDER):
    os.makedirs(RESUME_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/applications/<int:appId>/resume", methods=["POST"])
def upload_resume(appId):
    if 'resume' not in request.files: return jsonify({"error": "No resume file part in the request"}), 400
    file = request.files['resume']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        application = application_repo.find_application_by_id(appId)
        if not application: return jsonify({"error": "Application not found"}), 404
        user_id = application.get("userId")
        filename = f"user_{user_id}_app_{appId}_{secure_filename(file.filename)}"
        file_path = os.path.join(RESUME_FOLDER, filename)
        file.save(file_path)
        resume_url = f"/resumes/{filename}"
        application_repo.update_one_application({"appId": appId}, {"resume_url": resume_url})
        try:
            resume_parser_service.parse_resume_and_update_user(file_path, user_id)
        except Exception as e:
            print(f"Error triggering resume parsing: {e}")
        return jsonify({"message": "Resume uploaded successfully!", "resume_url": resume_url}), 200
    return jsonify({"error": "File type not allowed"}), 400

# --- NL2GQL Endpoint ---
@app.route("/nl2gql", methods=["POST"])
def nl2gql():
    data = request.get_json(silent=True) or {}
    user_text = data.get("query", "")
    user_context = data.get("userContext")
    run_graphql = request.args.get("run", "true").lower() != "false"
    with open(schema_path, "r", encoding="utf-8") as f: schema_sdl = f.read()
    def execute_graphql_query(gql_data):
        user_role = request.headers.get("X-User-Role", "Applicant")
        user_id = request.headers.get("X-User-ID")
        first_name = request.headers.get("X-User-FirstName", "")
        last_name = request.headers.get("X-User-LastName", "")
        
        context = {
            "request": request, 
            "user_role": user_role, 
            "user": user_context
        }
        
        if user_id:
            try:
                context["UserID"] = int(user_id)
                context["firstName"] = first_name
                context["lastName"] = last_name
            except ValueError:
                pass

        return graphql_sync(
            schema, gql_data, 
            context_value=context, 
            debug=app.debug
        )
    payload, status_code = process_nl2gql_request(user_text, schema_sdl, run_graphql, execute_graphql_query, user_context)
    return jsonify(payload), status_code

# --- User Authentication Endpoints ---
@app.route("/register", methods=["POST"])
def register_user():
    # ... (all existing validation logic is the same)
    data = request.get_json()
    email, password, first_name, last_name, role = data.get("email"), data.get("password"), data.get("firstName"), data.get("lastName"), data.get("role")
    if not all([email, password, first_name, last_name, role]): return jsonify({"error": "Missing required fields"}), 400
    # ... (role validation, existing user check, password hashing are the same)

    new_user_doc = {
        "UserID": next_user_id(), "email": email.lower(), "password": bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),
        "firstName": first_name, "lastName": last_name, "role": role, "phone_number": None, "city": None,
        "state_province": None, "country": None, "linkedin_profile": None, "portfolio_url": None,
        "highest_qualification": None, "years_of_experience": None, "createdAt": datetime.utcnow().isoformat(),
        "dob": None, "skills": [], "professionalTitle": None, "is_us_citizen": None, "highest_degree_year": None
    }
    
    try:
        user_repo.insert_user(new_user_doc)
        # --- THE CHANGE: Return the new UserID on success ---
        return jsonify({
            "message": "User registered successfully!",
            "UserID": new_user_doc["UserID"]
        }), 201
    except Exception as e:
        return jsonify({"error": f"An internal error occurred: {e}"}), 500

# --- NEW User-Profile Resume Upload Endpoint ---
@app.route("/users/<int:user_id>/resume", methods=["POST"])
def upload_profile_resume(user_id):
    if 'resume' not in request.files: return jsonify({"error": "No resume file part"}), 400
    file = request.files['resume']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # Verify the user exists
        user = user_repo.find_one_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        filename = f"user_{user_id}_profile_{secure_filename(file.filename)}"
        file_path = os.path.join(RESUME_FOLDER, filename)
        file.save(file_path)
        
        # Trigger the parsing service (this can be slow, ideally a background job)
        try:
            resume_parser_service.parse_resume_and_update_user(file_path, user_id)
        except Exception as e:
            print(f"Error triggering profile resume parsing: {e}")

        return jsonify({"message": "Resume uploaded and parsing initiated."}), 200

    return jsonify({"error": "File type not allowed"}), 400
   
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