# ApplyFlow

A full-stack job application tracking platform built with React, TypeScript, FastAPI, and SQLite.

ApplyFlow helps users organize job applications, monitor interview progress, and manage their job search through a centralized dashboard.

## Features

- **Application tracking:** Add, view, update, and delete job applications.
- **Status management:** Track applications through Applied, Interview, Offer, and Rejected stages.
- **Interactive dashboard:** View application statistics and progress.
- **Search and filtering:** Find applications by company, role, or status.
- **Persistent storage:** Save application data in a SQLite database.
- **REST API:** Manage applications through FastAPI endpoints.
- **Automated testing:** Eight backend tests covering CRUD operations, validation, and error handling.

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite |
| Testing | pytest, HTTPX |
| Version Control | Git, GitHub |

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.13 or compatible version
- Git

### 1. Clone the repository

```bash
git clone https://github.com/FurkanT06/ApplyFlow.git
cd ApplyFlow
```

### 2. Start the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
fastapi dev main.py --host 127.0.0.1 --port 8000
```

The backend will run at `http://127.0.0.1:8000`.

API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API health |
| GET | `/api/applications` | List applications |
| POST | `/api/applications` | Create an application |
| PATCH | `/api/applications/{id}` | Update an application |
| DELETE | `/api/applications/{id}` | Delete an application |

## Testing

Run the backend tests:

```bash
cd backend
source .venv/bin/activate
python3 -m pytest -v
```

The project currently includes eight automated backend tests.

## Project Status

ApplyFlow is under active development. Core application management functionality is implemented and tested.

Planned improvements include cloud deployment, CI/CD, authentication, and production database configuration.

## Author

Developed by [FurkanT06](https://github.com/FurkanT06).