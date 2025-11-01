from typing import Optional, Dict, Any, List
from pymongo import ReturnDocument
from ..db import applications_collection

def find_applications(q: Dict[str, Any]) -> List[dict]:
    """Finds multiple applications in the database."""
    return list(applications_collection().find(q, {"_id": 0}))

def find_application_by_id(app_id: int) -> Optional[dict]:
    """Finds a single application by its unique appId."""
    return applications_collection().find_one({"appId": int(app_id)}, {"_id": 0})

def insert_application(doc: dict) -> None:
    """Inserts a new application document into the database."""
    applications_collection().insert_one(doc)

def update_one_application(q: Dict[str, Any], set_fields: Dict[str, Any]) -> Optional[dict]:
    """Finds one application and updates it."""
    return applications_collection().find_one_and_update(
        q,
        {"$set": set_fields},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )