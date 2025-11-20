# src/backend/resolvers/user_resolvers.py
from ariadne import QueryType, MutationType
from datetime import datetime
from ..validators.common_validators import require_non_empty_str, validate_date_str, clean_update_input
from ..repository import user_repo
from ..db import next_user_id

query = QueryType()
mutation = MutationType()

@query.field("users")
def resolve_users(*_, limit=None, skip=None, firstName=None, lastName=None, dob=None, skills=None):
    if dob:
        dob = validate_date_str(dob)
    # Pass all arguments to the filter builder
    q = user_repo.build_filter(firstName, lastName, dob, skills)
    docs = user_repo.find_users(q, skip, limit)
    return [user_repo.to_user_output(d) for d in docs]

@query.field("userById")
def resolve_user_by_id(*_, UserID):
    doc = user_repo.find_one_by_id(int(UserID))
    return user_repo.to_user_output(doc)

@mutation.field("createUser")
def resolve_create_user(*_, input):
    email = require_non_empty_str(input.get("email"), "email")
    if user_repo.find_user_by_email(email):
        raise ValueError(f"A user with the email '{email}' already exists.")

    doc = {
        "UserID": next_user_id(), "email": email.lower(), "password": None,
        "firstName": require_non_empty_str(input.get("firstName"), "firstName"),
        "lastName": require_non_empty_str(input.get("lastName"), "lastName"),
        "role": require_non_empty_str(input.get("role"), "role"),
        "createdAt": datetime.utcnow().isoformat(), "phone_number": input.get("phone_number"),
        "city": input.get("city"), "state_province": input.get("state_province"),
        "country": input.get("country"), "linkedin_profile": input.get("linkedin_profile"),
        "portfolio_url": input.get("portfolio_url"), "highest_qualification": input.get("highest_qualification"),
        "years_of_experience": input.get("years_of_experience"), "dob": validate_date_str(input.get("dob")),
        "skills": input.get("skills", []), "professionalTitle": input.get("professionalTitle")
    }
    user_repo.insert_user(doc)
    return user_repo.to_user_output(doc)

@mutation.field("updateUser")
def resolve_update_user(*_, UserID, input):
    if "dob" in input and input.get("dob") is not None: input["dob"] = validate_date_str(input["dob"])
    if "firstName" in input and input.get("firstName") is not None: require_non_empty_str(input["firstName"], "firstName")
    if "lastName" in input and input.get("lastName") is not None: require_non_empty_str(input["lastName"], "lastName")
    
    set_fields = clean_update_input(input)
    if not set_fields: raise ValueError("No fields provided to update")
    
    updated = user_repo.update_one({"UserID": int(UserID)}, set_fields)
    if not updated: raise ValueError(f"User with ID {UserID} not found for update.")
    return user_repo.to_user_output(updated)

@mutation.field("updateUserByName")
def resolve_update_user_by_name(*_, firstName=None, lastName=None, input=None):
    if input and input.get("dob") is not None: input["dob"] = validate_date_str(input["dob"])
    
    q = user_repo.build_filter(firstName, lastName, None)
    if not q: raise ValueError("Provide firstName and/or lastName to identify the user")
    
    set_fields = clean_update_input(input or {})
    if not set_fields: raise ValueError("No fields provided to update")

    matches = user_repo.find_users(q, None, None)
    if len(matches) == 0: raise ValueError("No user matched the provided name filter")
    if len(matches) > 1: raise ValueError("Multiple users matched; please be more specific to target a single user")

    target_user_id = matches[0]["UserID"]
    updated = user_repo.update_one({"UserID": target_user_id}, set_fields)
    return user_repo.to_user_output(updated)

@mutation.field("deleteUser")
def resolve_delete_user(*_, UserID):
    return user_repo.delete_one({"UserID": int(UserID)}) == 1

@mutation.field("deleteUserByFields")
def resolve_delete_user_by_fields(*_, firstName=None, lastName=None, dob=None):
    if dob: dob = validate_date_str(dob)
    q = user_repo.build_filter(firstName, lastName, dob)
    if not q: raise ValueError("Provide at least one filter: firstName, lastName, or dob")
    
    matches = user_repo.find_users(q, None, None)
    if len(matches) == 0: return False
    if len(matches) > 1: raise ValueError("Multiple users matched; add more filters to target a single user")
    
    return user_repo.delete_one(q) == 1

# --- ADD THIS NEW MUTATION RESOLVER AT THE END OF THE FILE ---
@mutation.field("addSkillsToUser")
def resolve_add_skills_to_user(obj, info, UserID, skills):
    # This is an example of a more detailed authorization check.
    # We get the full user object from the context, which we set in app.py.
    logged_in_user = info.context.get("user")
    
    # A user can only add skills to their own profile.
    if not logged_in_user or logged_in_user.get("UserID") != UserID:
        # Also check if the user is a recruiter, who should be allowed to edit anyone.
        if info.context.get("user_role") != "Recruiter":
            raise ValueError("Permission denied: You can only add skills to your own profile.")

    if not skills:
        raise ValueError("The 'skills' list cannot be empty.")

    updated_user = user_repo.add_skills_to_user(UserID, skills)
    
    if not updated_user:
        raise ValueError(f"User with ID {UserID} not found.")
        
    return user_repo.to_user_output(updated_user)