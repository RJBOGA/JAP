# JobChat.AI - Conversational Job Portal

**JobChat.AI** is a modern web application that redefines how users interact with a job portal.  
It features a **conversational AI interface** allowing users to find jobs, manage applications, and query user data using plain English.  
The backend service translates natural language into **GraphQL** queries, offering a seamless and intuitive user experience.

---

## 🚀 Key Features

- **Conversational AI Interface**  
  A React-based chat UI where users can type requests like  
  _"show me all python jobs in San Francisco"_ or _"create a user named Jane Doe"_.

- **NL2GQL Service**  
  A powerful backend service that uses an LLM (Large Language Model) to translate natural language into executable GraphQL queries in real time.

- **Secure User Authentication**  
  Full registration and login system with REST endpoints. Passwords are securely hashed using `bcrypt`.

- **Rich Frontend Experience**  
  A responsive single-page application built with React, featuring:
  - Client-side routing with React Router (`/login`, `/chat`)
  - Session management to keep users logged in
  - Clean, formatted results display for database queries
  - Collapsible view to inspect raw GraphQL and JSON data
  - Dark/Light mode theme toggle

- **Robust Backend (Python + Flask)**  
  - GraphQL API for structured data access (`/graphql`)
  - REST endpoints for authentication (`/login`, `/register`)
  - Dedicated endpoint for the NL2GQL service (`/nl2gql`)

---

## 🧠 Tech Stack

### Backend
- **Framework:** Python, Flask  
- **API:** Ariadne (GraphQL), REST  
- **Database:** MongoDB (via PyMongo)  
- **Security:** bcrypt  
- **AI Service:** Ollama (or any compatible LLM endpoint)

### Frontend
- **Library:** React  
- **Routing:** React Router (`react-router-dom`)  
- **HTTP Client:** Axios  
- **Styling:** Plain CSS with theme variables  

---

## 📁 Repository Layout

| Path | Description |
|------|--------------|
| `src/backend/app.py` | Main Flask app with REST and GraphQL endpoints |
| `src/backend/schema.graphql` | Defines the GraphQL schema |
| `src/backend/services/nl2gql_service.py` | Translates natural language → GraphQL |
| `src/backend/repository/` | Data access layer for MongoDB collections (`accounts`, `jobs`, etc.) |
| `src/backend/resolvers/` | Business logic for the GraphQL API |
| `src/frontend-react/src/App.js` | Main React component with routing |
| `src/frontend-react/src/LoginPage.js` | Login and registration form |
| `src/frontend-react/src/ResultsDisplay.js` | Renders formatted query results in chat |

---

## ⚙️ Prerequisites

- **Python 3.10+** and `pip`  
- **Node.js v16+** and `npm`  
- **MongoDB** (running instance)  
- **(Optional)** Git for cloning the repository  

---

## 🧩 Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-folder>


2️⃣ Backend Setup
Create Virtual Environment
# For Unix/macOS
python3 -m venv .venv
source .venv/bin/activate

# For Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

Install Dependencies
pip install -r requirements.txt

Configure Environment Variables

Create a file at src/backend/.env with the following:

# src/backend/.env

# MongoDB connection string
MONGO_URI=mongodb://localhost:2717/
DB_NAME=jobtracker

# LLM service endpoint and credentials
OLLAMA_HOST=https://ollama.com
OLLAMA_MODEL=your-chosen-model
OLLAMA_API_KEY=your-api-key

3️⃣ Frontend Setup

Navigate to the React app directory:

cd src/frontend-react


Install Node.js dependencies:

npm install


💡 If any dependencies are missing, check package.json and re-run npm install.

▶️ Running the Application

You must have both backend and frontend servers running.

Start the Backend
python src/backend/app.py


Server will run at http://localhost:8000

Start the Frontend
cd src/frontend-react
npm start


The React app will open at http://localhost:3000

You’ll be redirected to the chat page after login or sign-up.

🤝 Contributing

Fork the repository

Create a feature branch (git checkout -b feature-name)

Add tests for new features or bug fixes

Submit a pull request with a clear description

📜 License & Author

This project is maintained by RJBOGA
Licensed under the MIT License