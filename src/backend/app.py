import os
import sys
# Add project root (src/) to sys.path for absolute imports from src.backend.*
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import requests
from flask_cors import CORS
from flask import Flask, jsonify, request
from ariadne import load_schema_from_path, make_executable_schema, graphql_sync
from ariadne.explorer import ExplorerGraphiQL
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException

# Load environment variables from the src directory
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Import modules from the new structure
from src.backend.errors import (
    handle_http_exception,
    handle_value_error,
    handle_generic_exception,
    # unwrap_graphql_errors is now only used inside the service
    json_error,
)
# Import the NL2GQL service function
from src.backend.services.nl2gql_service import process_nl2gql_request

# Import resolvers for ALL entities
from src.backend.resolvers.user_resolvers import query as user_query, mutation as user_mutation
from src.backend.resolvers.job_resolvers import query as job_query, mutation as job_mutation
from src.backend.resolvers.application_resolvers import query as app_query, mutation as app_mutation, application as application_object

# Import for database counter initialization
from src.backend.db import ensure_user_counter, ensure_job_counter, ensure_application_counter

# --- Flask app setup ---
app = Flask(__name__)
CORS(app)
explorer_html = ExplorerGraphiQL().html(None)

# --- Load schema ---
schema_path = os.path.join(os.path.dirname(__file__), "schema.graphql")
type_defs = load_schema_from_path(schema_path)

# Combine resolvers from all modules into a list
schema = make_executable_schema(
    type_defs,
    [user_query, job_query, app_query],
    [user_mutation, job_mutation, app_mutation],
    application_object
)

# Initialize all database counters
ensure_user_counter()
ensure_job_counter()
ensure_application_counter()

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    return json_error("Not found", 404)

@app.errorhandler(405)
def method_not_allowed(e):
    return json_error("Method not allowed", 405)

@app.errorhandler(ValueError)
def value_error(e):
    return handle_value_error(e)

@app.errorhandler(Exception)
def unhandled_exception(e):
    if isinstance(e, HTTPException):
        return handle_http_exception(e)
    return handle_generic_exception(e)

# --- GraphQL endpoints (No Changes) ---
@app.route("/graphql", methods=["GET"])
def graphql_explorer():
    return explorer_html, 200

@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        # We call jsonify here because this is the final response layer
        payload, status = json_error("Body must be JSON with 'query' and optional 'variables'", 400)
        return jsonify(payload), status

    success, result = graphql_sync(
        schema,
        data,
        context_value={"request": request},
        debug=app.debug,
    )
    # The main graphql endpoint doesn't need unwrap_graphql_errors,
    # as it returns the standard GraphQL JSON response including the "errors" key.
    return jsonify(result), (200 if success else 400)

# --- Health check (No Changes) ---
@app.route("/")
def health():
    return jsonify({"status": "Backend is running!"}), 200

# --- NL2GQL Endpoint (Simplified) ---
@app.route("/nl2gql", methods=["POST"])
def nl2gql():
    data = request.get_json(silent=True) or {}
    user_text = data.get("query", "")
    run_graphql = request.args.get("run", "true").lower() != "false"

    if not isinstance(user_text, str) or not user_text.strip():
        payload, status = json_error("Missing 'query' in body", 400)
        return jsonify(payload), status

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sdl = f.read()
    except Exception as e:
        payload, status = json_error(f"Failed to read schema: {e}", 500)
        return jsonify(payload), status

    def execute_graphql_query(gql_data):
        return graphql_sync(
            schema,
            gql_data,
            context_value={"request": request},
            debug=app.debug,
        )

    # The service now reliably returns a (payload_dict, status_code) tuple
    payload, status_code = process_nl2gql_request(
        user_text, schema_sdl, run_graphql, execute_graphql_query
    )

    # We can now simply jsonify the payload and return it with its status
    return jsonify(payload), status_code

if __name__ == "__main__":
    print("🚀 Starting Flask server on http://localhost:8000 ...")
    app.run(host="0.0.0.0", port=8000, debug=True)