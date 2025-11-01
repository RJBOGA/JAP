import re
from typing import Optional, Dict, Any

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def require_non_empty_str(value: Optional[str], field: str) -> str:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()

def validate_date_str(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    if not DATE_RE.match(value):
        raise ValueError("DateOfBirth must be in YYYY-MM-DD format")
    return value

def clean_update_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in (input_data or {}).items() if v is not None}
