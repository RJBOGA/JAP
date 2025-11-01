from typing import Optional
from ariadne import QueryType, MutationType
# Corrected import for validators
from ..validators.common_validators import require_non_empty_str, validate_date_str, clean_update_input
# Corrected import for the user repository
from ..repository.user_repo import (
    next_user_id,
    to_user_output,
    build_filter,
    name_filter_ci,
    find_users,
    find_one_by_id,
    insert_user,
    update_one,
    update_many,
    delete_one,
    delete_many,
)

query = QueryType()
mutation = MutationType()

@query.field("users")
def resolve_users(*_, limit=None, skip=None, FirstName=None, LastName=None, DateOfBirth=None):
    if DateOfBirth:
        DateOfBirth = validate_date_str(DateOfBirth)
    q = build_filter(FirstName, LastName, DateOfBirth)
    docs = find_users(q, skip, limit)
    return [to_user_output(d) for d in docs]

@query.field("userById")
def resolve_user_by_id(*_, UserID):
    doc = find_one_by_id(int(UserID))
    return to_user_output(doc)

@mutation.field("createUser")
def resolve_create_user(*_, input):
    first = require_non_empty_str(input.get("FirstName"), "FirstName")
    last = require_non_empty_str(input.get("LastName"), "LastName")
    dob = validate_date_str(input.get("DateOfBirth"))
    title = (input.get("ProfessionalTitle") or None)
    summary = (input.get("Summary") or None)

    doc = {
        "UserID": next_user_id(),
        "FirstName": first,
        "LastName": last,
        "DateOfBirth": dob,
        "ProfessionalTitle": title,
        "Summary": summary,
    }
    insert_user(doc)
    return to_user_output(doc)

@mutation.field("updateUser")
def resolve_update_user(*_, UserID, input):
    if "FirstName" in input and input["FirstName"] is not None:
        require_non_empty_str(input["FirstName"], "FirstName")
    if "LastName" in input and input["LastName"] is not None:
        require_non_empty_str(input["LastName"], "LastName")
    if "DateOfBirth" in input and input["DateOfBirth"] is not None:
        input["DateOfBirth"] = validate_date_str(input["DateOfBirth"])

    set_fields = clean_update_input(input)
    if not set_fields:
        raise ValueError("No fields provided to update")

    updated = update_one({"UserID": int(UserID)}, set_fields)
    return to_user_output(updated)

@mutation.field("updateUserByName")
def resolve_update_user_by_name(*_, FirstName=None, LastName=None, input=None):
    if input and input.get("DateOfBirth") is not None:
        input["DateOfBirth"] = validate_date_str(input["DateOfBirth"])
    if input and input.get("FirstName") is not None:
        require_non_empty_str(input["FirstName"], "FirstName")
    if input and input.get("LastName") is not None:
        require_non_empty_str(input["LastName"], "LastName")

    q = name_filter_ci(FirstName, LastName)
    if not q:
        raise ValueError("Provide FirstName and/or LastName to identify the user")

    set_fields = clean_update_input(input or {})
    if not set_fields:
        raise ValueError("No fields provided to update")

    matches = find_users(q, None, None)
    if len(matches) == 0:
        raise ValueError("No user matched the provided name filter")
    if len(matches) > 1:
        raise ValueError("Multiple users matched; include both FirstName and LastName to disambiguate")

    updated = update_one(q, set_fields)
    return to_user_output(updated)

@mutation.field("updateUsersByName")
def resolve_update_users_by_name(*_, FirstName=None, LastName=None, input=None):
    if input and input.get("DateOfBirth") is not None:
        input["DateOfBirth"] = validate_date_str(input["DateOfBirth"])
    q = name_filter_ci(FirstName, LastName)
    if not q:
        raise ValueError("Provide FirstName and/or LastName to filter users")
    set_fields = clean_update_input(input or {})
    if not set_fields:
        raise ValueError("No fields provided to update")
    count = update_many(q, set_fields)
    return int(count)

@mutation.field("deleteUser")
def resolve_delete_user(*_, UserID):
    return delete_one({"UserID": int(UserID)}) == 1

@mutation.field("deleteUserByFields")
def resolve_delete_user_by_fields(*_, FirstName=None, LastName=None, DateOfBirth=None):
    if DateOfBirth:
        DateOfBirth = validate_date_str(DateOfBirth)
    q = build_filter(FirstName, LastName, DateOfBirth)
    if not q:
        raise ValueError("Provide at least one filter: FirstName, LastName, or DateOfBirth")
    matches = find_users(q, None, None)
    if len(matches) == 0:
        return False
    if len(matches) > 1:
        raise ValueError("Multiple users matched; add more filters to target a single user")
    return delete_one(q) == 1

@mutation.field("deleteUsersByFields")
def resolve_delete_users_by_fields(*_, FirstName=None, LastName=None, DateOfBirth=None):
    if DateOfBirth:
        DateOfBirth = validate_date_str(DateOfBirth)
    q = build_filter(FirstName, LastName, DateOfBirth)
    if not q:
        raise ValueError("Provide at least one filter: FirstName, LastName, or DateOfBirth")
    return int(delete_many(q))