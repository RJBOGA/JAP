
# Job Portal App

Lightweight job portal backend and Streamlit frontend for demo/testing purposes. This repository contains a Python-based GraphQL backend and a Streamlit frontend used to interact with job postings, applications and user data. It includes services for authentication, resume parsing and other helper components.

## Key features

- GraphQL backend (schema under `src/backend/schema.graphql`) exposing jobs, users and applications.
- Streamlit frontend demo app in `src/frontend/app_streamlit.py`.
- Simple services for auth, resume parsing, embeddings and NL2GQL utilities.
- Modular repository layout separating models, repositories, resolvers and services for easy testing and extension.

## Tech stack

- Python 3.10+ (recommended)
- Streamlit for the frontend demo
- GraphQL for the backend API
- Pytest for tests

## Repository layout (important files)

- `src/backend/app.py` — backend application entrypoint
- `src/backend/db.py` — database helpers
- `src/backend/schema.graphql` — GraphQL schema
- `src/backend/models/` — datamodels for jobs, users, applications
- `src/backend/repository/` — repository layer (data access)
- `src/backend/resolvers/` — GraphQL resolvers
- `src/backend/services/` — application services (auth, resume_parser, embeddings, etc.)
- `src/frontend/app_streamlit.py` — Streamlit demo frontend
- `tests/` — unit tests for backend, frontend and services

## Prerequisites

- Python 3.10 or newer installed and available on PATH as `python`.
- A working PowerShell (this README includes PowerShell commands).
- (Optional) Git to clone the repository.

## Setup (Windows PowerShell)

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you plan to run only the frontend demo, installing the full `requirements.txt` is the simplest choice.

## Running the backend

Start the backend (from repository root):

```powershell
python .\src\backend\app.py
```

This will start the backend service. The GraphQL endpoint and the exact host/port will depend on the implementation in `src/backend/app.py` (check that file for details). If the app exposes a `/graphql` endpoint, you can query it with a GraphQL client.

## Running the Streamlit frontend

Start the demo frontend (from repository root):

```powershell
streamlit run .\src\frontend\app_streamlit.py
```

The Streamlit UI should open in your default browser and interact with the running backend (or mock data depending on configuration).

## Tests

Run the test suite with pytest (from repository root):

```powershell
pytest -q
```

The `tests/` folder includes unit tests for repositories, resolvers and services.

## Development notes

- Code is organized to separate concerns: models → repositories → resolvers → services.
- If you add new dependencies, update `requirements.txt` and include them in the virtualenv.
- Small, focused unit tests are included — please add tests for new behavior.

## Contributing

1. Fork the repository and create a feature branch.
2. Add tests for any new feature or bug fix.
3. Submit a pull request with a clear description of changes.

## License & Author

This repository is maintained by RJBOGA. Include your preferred license file if you want to open-source this project (e.g., MIT, Apache-2.0).

## Contact

For questions or help, open an issue in the repository or contact the maintainer.
