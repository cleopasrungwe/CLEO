# CLEO — Cognitive Logic & Executive Operator

CLEO is a modular personal AI assistant ecosystem designed to connect computers and mobile devices through an intelligent assistant.

## Development Status

Version: 0.1.0
Stage: Backend Foundation

Current capabilities:
- FastAPI backend
- Welcome endpoint
- Health-check endpoint
- JSON chat endpoint
- Request validation using Pydantic
- Structured JSON responses

The AI reasoning engine is not yet connected. The chat endpoint currently returns a placeholder response.

## Technology Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- Git and GitHub

## Project Structure

    CLEO/
    ├── app/
    │   └── main.py
    ├── tests/
    ├── .gitignore
    ├── README.md
    └── requirements.txt

## Installation

Clone the repository:

    git clone https://github.com/cleopasrungwe/CLEO.git
    cd CLEO

Create a virtual environment:

    python -m venv venv

Activate it in Git Bash:

    source venv/Scripts/activate

Install dependencies:

    python -m pip install -r requirements.txt

Start CLEO:

    python -m uvicorn app.main:app --reload

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Welcome message |
| GET | /health | Backend health status |
| POST | /chat | Submit a message |

## API Documentation

While CLEO is running:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Roadmap

1. Backend foundation
2. Voice interaction
3. AI reasoning and memory
4. Controlled Windows automation
5. Android companion application
6. Unified interface
7. Security and advanced capabilities

## Security

Never commit passwords, API keys, access tokens, or other secrets.

## Author

Cleopas Rungwe

## License

No open-source license has been selected yet.
