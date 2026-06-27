# SEO Growth AI Agent

An autonomous SEO assistant powered by **LangGraph**, **Groq AI**, **FastAPI**, and **Next.js 15**.

---

## 🏗️ Architecture

```
seo-growth-agent/
├── backend/                  # FastAPI + LangGraph
│   ├── agents/               # 8 AI agents
│   │   ├── business_agent.py
│   │   ├── crawler_agent.py
│   │   ├── audit_agent.py
│   │   ├── keyword_agent.py
│   │   ├── content_gap_agent.py
│   │   ├── content_agent.py
│   │   ├── score_agent.py
│   │   └── report_agent.py
│   ├── api/                  # REST endpoints
│   │   ├── auth.py
│   │   ├── projects.py
│   │   └── reports.py
│   ├── core/                 # Config & security
│   ├── db/                   # SQLAlchemy + SQLite
│   ├── models/               # Pydantic schemas
│   ├── services/             # Workflow + PDF
│   ├── main.py
│   └── requirements.txt
└── frontend/                 # Next.js 15 + Tailwind
    └── src/
        ├── app/
        │   ├── page.tsx          # Landing
        │   ├── login/
        │   ├── register/
        │   ├── dashboard/
        │   ├── analyze/
        │   └── reports/
        ├── components/
        └── lib/
```

---

## ⚡ Quick Start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| npm | 8+ | Included with Node.js |

---

### 1. Clone / Extract the project

```bash
cd seo-growth-agent
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# The .env file is already configured with your Groq key
# Verify it looks correct:
cat .env
```

### 3. Start the Backend

```bash
# From backend/ directory with venv activated:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Test it: open http://localhost:8000 in your browser — you should see `{"message":"SEO Growth AI Agent API"}`

### 4. Frontend Setup

Open a **new terminal**:

```bash
cd seo-growth-agent/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open http://localhost:3000

---

## 🔑 Environment Variables

### Backend (`backend/.env`) — already configured:
```
GROQ_API_KEY=gsk_k0UZFAugqRkseVEe0iYi...
JWT_SECRET=super-secret-jwt-key-change-in-production-2024
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
DATABASE_URL=sqlite:///seo_agent.db
```

### Frontend (`frontend/.env.local`) — already configured:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Using the App

1. **Register** at http://localhost:3000/register
2. Click **New Analysis**
3. Fill in:
   - Business Name
   - Business Description
   - Products/Services
   - Target Audience
   - Target Location
   - Website URL *(optional — enables real crawling)*
   - Competitor URLs *(optional)*
4. Click **Launch SEO Analysis**
5. Watch the dashboard — status updates every 5 seconds
6. When **Completed**, click **Report** to see full results
7. Download as **PDF** or **JSON**

---

## 🤖 The 8 AI Agents

| # | Agent | What It Does |
|---|-------|-------------|
| 1 | Business Understanding | Industry, audience, pain points, search intent |
| 2 | Website Crawler | Crawls up to 10 pages, extracts all SEO elements |
| 3 | SEO Audit | Finds technical issues, missing tags, thin content |
| 4 | Keyword Research | 30+ keywords across 6 categories via Groq |
| 5 | Content Gap | Missing pages, topics, FAQs, landing pages |
| 6 | Content Generation | Metadata, FAQs, blog ideas, CTAs, schema hints |
| 7 | SEO Score | Scores across 4 dimensions (0–100) |
| 8 | Report Generation | Full report with improvement plan |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login |
| POST | `/projects/` | Create project & start analysis |
| GET | `/projects/` | List all projects |
| GET | `/projects/{id}` | Get project details |
| DELETE | `/projects/{id}` | Delete project |
| GET | `/reports/{id}` | Get report JSON |
| GET | `/reports/{id}/pdf` | Download PDF report |
| GET | `/reports/{id}/json` | Download JSON report |

API docs: http://localhost:8000/docs

---

## 🐛 Troubleshooting

**`ModuleNotFoundError`** — Make sure your venv is activated and you ran `pip install -r requirements.txt`

**`CORS error` in browser** — Make sure backend is running on port 8000 and frontend on port 3000

**Analysis stays "running"** — Check the backend terminal for error logs. Common cause: Groq API rate limit. Wait 30 seconds and retry.

**`lxml` install fails on Windows** — Run: `pip install lxml --no-binary lxml` or use `pip install beautifulsoup4 html.parser`

**Port already in use** — Change port: `uvicorn main:app --reload --port 8001` and update `.env.local`

---

## 🔒 Production Notes

- Change `JWT_SECRET` to a long random string
- Set `FRONTEND_URL` to your actual domain in `backend/.env`
- Use PostgreSQL instead of SQLite for production
- Add rate limiting to the API
