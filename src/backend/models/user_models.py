# JPA/src/backend/models/user_models.py

from enum import Enum

class UserProfileType(Enum):
    APPLICANT = "Applicant"
    RECRUITER = "Recruiter"

    @classmethod
    def from_str(cls, value: str):
        try:
            return cls(value.title())
        except ValueError:
            raise ValueError(f"Invalid ProfileType: {value}. Must be one of: Applicant, Recruiter")
            
def get_user_profile_types():
    return [e.value for e in UserProfileType]