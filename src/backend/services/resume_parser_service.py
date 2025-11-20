# src/backend/services/resume_parser_service.py
import os
import json
from typing import Optional, Dict
import pypdf
import docx

from .nl2gql_service import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_API_KEY # Reuse existing config
from ..repository import user_repo
import requests

def _extract_text_from_pdf(file_path: str) -> str:
    """Extracts text content from a PDF file."""
    with open(file_path, 'rb') as f:
        reader = pypdf.PdfReader(f)
        text = "".join(page.extract_text() for page in reader.pages)
    return text

def _extract_text_from_docx(file_path: str) -> str:
    """Extracts text content from a DOCX file."""
    doc = docx.Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs)

def _get_llm_parsed_data(resume_text: str) -> Optional[dict]:
    """Sends resume text to the LLM for structured data extraction."""
    # --- UPDATED, MORE DETAILED PROMPT ---
    prompt = (
        "You are an expert HR assistant. Analyze the following resume text and extract the "
        "specified fields into a valid JSON object. The fields are: "
        "'skills' (a list of key technical skills), "
        "'years_of_experience' (an integer, calculated if necessary), "
        "'is_us_citizen' (a boolean, infer this from phrases like 'US Citizen' or work authorization, default to false if unclear), "
        "'highest_degree_year' (an integer representing the graduation year of the highest degree mentioned), "
        "'professionalTitle' (the user's most recent job title, e.g., 'Software Engineer'), "
        "'city' (the user's city of residence), "
        "'country' (the user's country of residence), and "
        "'highest_qualification' (the name of the user's highest degree, e.g., 'Master of Science in Computer Science'). "
        "Respond ONLY with the JSON object and nothing else.\n\n"
        f"Resume Text:\n---\n{resume_text}"
    )
    
    headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
    api_url = f"{OLLAMA_HOST}/api/generate"

    try:
        response = requests.post(
            api_url,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
            headers=headers,
            timeout=120,
        )
        response.raise_for_status()
        
        json_string = response.json().get("response", "{}")
        return json.loads(json_string)
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Error parsing resume with LLM: {e}")
        return None

def parse_resume_and_update_user(file_path: str, user_id: int):
    """
    Orchestrates the resume parsing process and updates the user profile.
    """
    print(f"Starting resume parsing for user {user_id} from file {file_path}...")
    try:
        _, file_extension = os.path.splitext(file_path)
        raw_text = ""
        if file_extension.lower() == '.pdf':
            raw_text = _extract_text_from_pdf(file_path)
        elif file_extension.lower() == '.docx':
            raw_text = _extract_text_from_docx(file_path)
        else:
            print(f"Unsupported file type: {file_extension}")
            return

        if not raw_text:
            print("Could not extract text from resume.")
            return

        parsed_data = _get_llm_parsed_data(raw_text)
        if not parsed_data:
            print("LLM parsing failed or returned no data.")
            return
            
        # --- UPDATED: Allow more fields to be updated ---
        update_doc = {k: v for k, v in parsed_data.items() if k in [
            'skills', 'years_of_experience', 'is_us_citizen', 'highest_degree_year',
            'professionalTitle', 'city', 'country', 'highest_qualification'
        ]}

        if update_doc:
            if 'skills' in update_doc and isinstance(update_doc['skills'], list):
                user_repo.add_skills_to_user(user_id, update_doc.pop('skills'))

            if update_doc:
                user_repo.update_one({"UserID": user_id}, update_doc)
            
            print(f"Successfully updated user {user_id} profile from resume with data: {update_doc}")

    except Exception as e:
        print(f"An unexpected error occurred during resume processing: {e}")