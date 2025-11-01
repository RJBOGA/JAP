from flask import jsonify
from werkzeug.exceptions import HTTPException

def json_error(message: str, status: int):
    """Creates a standard JSON error payload and returns it as a tuple."""
    error_payload = {"error": {"message": message, "status": status}}
    # In this new version, we return the payload and status,
    # letting the final route handler call jsonify.
    return error_payload, status

def handle_http_exception(e: HTTPException):
    message = getattr(e, "description", None) or getattr(e, "name", "HTTP Error")
    status = getattr(e, "code", None) or 500
    # Create the JSON response directly here for Flask's error handler
    payload, status_code = json_error(message, status)
    return jsonify(payload), status_code

def handle_value_error(e: ValueError):
    # Create the JSON response directly here for Flask's error handler
    payload, status_code = json_error(str(e), 400)
    return jsonify(payload), status_code

def handle_generic_exception(e: Exception):
    # Create the JSON response directly here for Flask's error handler
    payload, status_code = json_error("Internal server error", 500)
    return jsonify(payload), status_code

def unwrap_graphql_errors(result: dict):
    """
    Normalizes GraphQL error payloads into our standard shape.
    Returns a tuple of (error_payload, status_code) or None.
    """
    if not result:
        return json_error("Empty GraphQL response", 500)

    errors = result.get("errors") if isinstance(result, dict) else None
    if errors:
        msgs = []
        for err in errors:
            msg = err.get("message") if isinstance(err, dict) else str(err)
            if msg:
                msgs.append(msg)
        message = "; ".join(msgs) if msgs else "GraphQL execution error"
        return json_error(message, 400)

    return None