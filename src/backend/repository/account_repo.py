# src/backend/repository/account_repo.py
from typing import Optional, Dict, Any
from ..db import get_db

def accounts_collection():
    """Returns a handle to the 'accounts' collection."""
    return get_db()["accounts"]

def find_account_by_email(email: str) -> Optional[dict]:
    """
    Finds a single account by its email (case-insensitive).
    """
    return accounts_collection().find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})

def insert_account(account_doc: Dict[str, Any]) -> None:
    """
    Inserts a new account document into the database.
    """
    accounts_collection().insert_one(account_doc)