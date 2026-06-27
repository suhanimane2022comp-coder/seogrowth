@echo off
echo === SEO Growth AI Agent - Backend Setup ===
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo.
echo === Starting Backend on http://localhost:8000 ===
uvicorn main:app --reload --host 0.0.0.0 --port 8000
