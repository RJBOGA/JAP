import re
from typing import Optional, Dict, Any, List
from pymongo import ReturnDocument
from ..db import users_collection, counters_collection
from ..db import get_db  # if you need raw DB access

def ensure_user_counter():
    counters = counters_collection()
    counters.update_one(
        {"_id": "UserID"},
        {"$setOnInsert": {"sequence_value": 0}},
        upsert=True,
    )

def next_user_id() -> int:
    counters = counters_collection()
    result = counters.find_one_and_update(
        {"_id": "UserID"},
        {"$inc": {"sequence_value": 1}},
        return_document=ReturnDocument.AFTER,
        upsert=True,
    )
    return int(result["sequence_value"])

def to_user_output(doc: dict) -> dict:
    if not doc:
        return None
    return {
        "UserID": int(doc.get("UserID")) if doc.get("UserID") is not None else None,
        "FirstName": doc.get("FirstName"),
        "LastName": doc.get("LastName"),
        "DateOfBirth": doc.get("DateOfBirth"),
        "ProfessionalTitle": doc.get("ProfessionalTitle"),
        "Summary": doc.get("Summary"),
    }

def name_filter_ci(first_name: Optional[str], last_name: Optional[str]) -> Dict[str, Any]:
    q: Dict[str, Any] = {}
    if first_name:
        q["FirstName"] = {"$regex": f"^{re.escape(first_name)}$", "$options": "i"}
    if last_name:
        q["LastName"] = {"$regex": f"^{re.escape(last_name)}$", "$options": "i"}
    return q

def build_filter(first_name: Optional[str], last_name: Optional[str], dob: Optional[str]) -> Dict[str, Any]:
    q = name_filter_ci(first_name, last_name)
    if dob:
        q["DateOfBirth"] = dob
    return q

def find_users(q: Dict[str, Any], skip: Optional[int], limit: Optional[int]) -> List[dict]:
    col = users_collection()
    cursor = col.find(q, {"_id": 0})
    if skip is not None:
        cursor = cursor.skip(int(skip))
    if limit is not None:
        cursor = cursor.limit(int(limit))
    return list(cursor)

def find_one_by_id(user_id: int) -> Optional[dict]:
    col = users_collection()
    return col.find_one({"UserID": int(user_id)}, {"_id": 0})

def insert_user(doc: dict) -> None:
    users_collection().insert_one(doc)

def update_one(q: Dict[str, Any], set_fields: Dict[str, Any]) -> Optional[dict]:
    col = users_collection()
    return col.find_one_and_update(
        q,
        {"$set": set_fields},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )

def update_many(q: Dict[str, Any], set_fields: Dict[str, Any]) -> int:
    res = users_collection().update_many(q, {"$set": set_fields})
    return int(res.modified_count)

def delete_one(q: Dict[str, Any]) -> int:
    res = users_collection().delete_one(q)
    return int(res.deleted_count)

def delete_many(q: Dict[str, Any]) -> int:
    res = users_collection().delete_many(q)
    return int(res.deleted_count)
