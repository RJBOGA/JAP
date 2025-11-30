from flask import jsonify
from werkzeug.exceptions import HTTPException
import traceback

def json_error(message: str, status: int):
    return {"error": {"message": message, "status": status}}, status

def handle_http_exception(e: HTTPException):
    message = getattr(e, "description", None) or getattr(e, "name", "HTTP Error")
    status = getattr(e, "code", None) or 500
    payload, status_code = json_error(message, status)
    return jsonify(payload), status_code

def handle_value_error(e: ValueError):
    payload, status_code = json_error(str(e), 400)
    return jsonify(payload), status_code

def handle_generic_exception(e: Exception):
    # --- PRINT FULL ERROR TO CONSOLE ---
    print("!!! UNHANDLED EXCEPTION !!!")
    traceback.print_exc()
    # -----------------------------------
    payload, status_code = json_error("Internal server error", 500)
    return jsonify(payload), status_code

def unwrap_graphql_errors(result: dict):
    if not result:
        return json_error("Empty GraphQL response", 500)

    errors = result.get("errors") if isinstance(result, dict) else None
    if errors:
        msgs = [str(err.get("message", err)) for err in errors]
        return json_error("; ".join(msgs), 400)

    return None