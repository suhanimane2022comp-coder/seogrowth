# SEO Growth AI + SMM Growth AI — Feature Enhancements

This build adds 6 feature sets on top of the existing auth/dashboard/report-generation
codebase. Existing auth and the core SEO analysis pipeline are untouched.

## What was added

### Backend (`backend/`)
- **Models** (`db/models.py`): `Profile`, `AudiencePersona`, `Competitor`, `AgentProgress`,
  `PromptAgentOutput`, `SocialMediaCalendar`, `SocialMediaPost` (tracking fields are
  folded into the post row: `status`, `actual_posted_date`, `engagement_score`),
  `Notification`.
- **Agents** (`backend/agents/`): `audience_agent.py`, `competitor_agent.py`,
  `prompt_agent.py` (website prompt + seasonal content), `social_strategy_agent.py`
  (platform priority, calendar, prime times, engagement suggestions). All AI calls go
  through `services/ai_client.py`, which calls Groq and **gracefully falls back to
  sensible rule-based defaults** if the API call/parsing fails — so the product still
  works even if Groq is rate-limited or the key is missing.
- **API routers**: `api/profile.py`, `api/prompt_agent_api.py`, `api/social.py`,
  `api/analytics.py`, `api/notifications.py` — all registered in `main.py`.
- **`api/projects.py`** was modified so `/projects/ (POST)` now only requires
  `website_url`; everything else (business info, audience, competitors) is pulled
  from the user's `Profile`. The background analysis task now also updates
  `AgentProgress` and creates a `Notification` on completion/failure.
- **`requirements.txt`**: pinned `bcrypt==4.0.1` (newer bcrypt breaks passlib's
  backend detection — unrelated pre-existing issue, fixed here).

### Frontend (`frontend/src/`)
- **`app/profile/setup/`** — new onboarding page (Feature 1). On login, the
  dashboard/analyze layouts check for a profile and redirect here if missing.
- **`app/analyze/page.tsx`** — simplified to only ask for the Website URL (Feature 2).
- **`app/dashboard/page.tsx`** — added Profile Summary, Target Audience, Competitor
  table, Latest SEO Report, and Agent Progress cards (Feature 3).
- **`app/prompts/`** — Content & Website Prompt Agent UI: generate/view the Lovable
  website prompt and seasonal content per occasion (Feature 4).
- **`app/social/`** — Social Media Strategy Agent UI: platform selection, calendar
  generation, platform priority, prime times, engagement suggestions, and a
  paginated post table with status tracking + completion % (Feature 5).
- **`app/analytics/`** — Recharts dashboards for SEO trend, competitor comparison,
  audience pies, social media charts, and agent activity (Feature 6).
- **`components/Sidebar.tsx`** — added nav links + a notification bell with unread
  count and a dropdown list.
- **`lib/api.ts`** — added typed API functions for all the above.

## Running it

Backend:
```
cd backend
pip install -r requirements.txt
# .env needs GROQ_API_KEY (and optionally JWT_SECRET, DATABASE_URL)
uvicorn main:app --reload
```

Frontend:
```
cd frontend
npm install
npm run dev
```

Both `npm run build` (Next.js) and Python compilation were verified to pass. A full
backend smoke test (register → login → profile → audience/competitors →
analyze → prompt agent → social calendar → analytics → notifications) was run
end-to-end successfully.

## Notes / design decisions
- `social_media_tracking` from the spec was folded into `social_media_posts`
  (status/posted-date/engagement live on the post row) rather than a separate table,
  since each post has exactly one tracking record — simpler without losing any data.
- AI agents always have a deterministic fallback so the app is fully functional even
  without a working Groq key, with reduced personalization.
- This sandbox doesn't have `api.groq.com` in its egress allowlist, so live AI calls
  weren't reachable here — the fallback paths were what got exercised. In a normal
  deployment with a valid `GROQ_API_KEY` and network access, the AI-generated content
  is used instead.
