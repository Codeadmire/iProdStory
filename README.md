# Product Marketing AI

## Overview
This is Phase 1 of the Product Marketing AI platform, which crawls a given product URL, extracts basic features, and takes screenshots.

## Prerequisites
- Node.js (v18+)
- Python 3.11+
- PostgreSQL (Optional for Phase 1 as SQLite is default configured)

## Setup Instructions

### 1. Backend Setup (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic pydantic-settings playwright python-dotenv
playwright install chromium
```

### 2. Environment Variables
Copy `.env.example` to `backend/.env` and update the values as needed.

### 3. Starting the Backend
From the `backend` directory with the virtual environment activated:
```bash
uvicorn main:app --reload --port 8000
```
This will automatically create the SQLite database and tables on startup.

### 4. Frontend Setup (Next.js)
```bash
cd frontend
npm install
```

### 5. Starting the Frontend
```bash
cd frontend
npm run dev
```

### 6. Testing the Pipeline
1. Go to `http://localhost:3000` (Frontend Dashboard) or use the API docs at `http://localhost:8000/docs`.
2. Submit a Product URL to `/api/products` to create a product.
3. Submit a POST request to `/api/products/{id}/crawl` to start the background Playwright crawler.
4. Check `/api/products/{id}/features` to see the extracted features and evidence.
