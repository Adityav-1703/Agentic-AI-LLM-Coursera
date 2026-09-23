# CareerPilot — Multi-Agent AI Career & Interview Preparation Assistant

Portfolio-quality **Agentic AI** product built around IBM course themes
(**LangGraph, CrewAI, AutoGen, BeeAI**).

**Production orchestration uses LangGraph only.** CrewAI / AutoGen / BeeAI live
under `framework_demos/` as conceptual comparisons — not the live runtime path.

---

## Product

**CareerPilot** — AI-powered career preparation

> Turn your target role into a personalized learning and interview strategy.

Badge: *Powered by LangGraph · Multi-Agent AI · Human-in-the-Loop*

The default UI is a polished career workspace. Technical execution is available
via **Agent Inspector**.

---

## What this demonstrates

- 7 specialized agents + supervisor orchestration
- Tool calling with explicit schemas
- Typed shared state + short-term workflow memory / checkpoints
- Conditional LangGraph routing
- Human-in-the-loop plan confirmation (`interrupt`)
- Hierarchical skill assessments + week/day study plans
- Transparent interview evaluation with feedback into replanning
- Progress dashboard + structured final report
- Offline mode (no API key required)
- React dashboard with user vs technical activity views

---

## Quick start

```bash
cd "Agentic AI project"
python -m venv .venv
# Windows
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
copy .env.example .env
```

`.env` defaults:

```env
LLM_PROVIDER=offline
ENABLE_WEB_RESEARCH=true
```

### Backend

```bash
uvicorn app.main:app --app-dir backend --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://127.0.0.1:5173

### Tests

```bash
pytest backend/tests -q
cd frontend && npm run build
```

---

## Architecture (short)

See `docs/architecture.md`, `docs/agent_design.md`, `docs/workflow.md`.

```text
START → Orchestrator ⇄ specialists → Human gate (interrupt) → Interview → Evaluator
      ⇄ Study Planner (replan on weak evals) → Report → END
```

Agents communicate through shared `CareerState`, not direct RPC.

---

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health + LLM mode |
| POST | `/api/career/analyze` | Skill map preview |
| POST | `/api/career/start` | Start workflow |
| GET | `/api/career/status/{id}` | Session snapshot |
| POST | `/api/career/decide/{id}` | HITL approve/modify/restart/clarify |
| GET | `/api/study-plan/{id}` | Study plan |
| POST | `/api/interview/answer` | Submit answer |
| POST | `/api/interview/evaluate` | Run evaluator |
| POST | `/api/career/report/{id}` | Final report |

---

## LLM providers

| Value | Behavior |
|-------|----------|
| `offline` | Deterministic tools + OfflineLLM (default, no keys) |
| `openai` | Requires `OPENAI_API_KEY` |
| `anthropic` | Requires `ANTHROPIC_API_KEY` |

Never commit real keys. UI shows **AI Engine: Offline Demo Mode** when offline.

---

## Research honesty

- Live: DuckDuckGo when `ENABLE_WEB_RESEARCH=true`
- Fallback: clearly labelled **local knowledge / Offline resource catalog**
- Never presented as live web results when local

---

## Framework demos

`framework_demos/crewai_demo`, `autogen_demo`, `beeai_demo` — conceptual only.

---

## Why this is Agentic AI (not a chatbot)

Task decomposition, specialist roles, tools, typed state machine, conditional
routing, HITL interrupts, evaluator-driven replanning, and structured outputs —
versus a single LLM reply.

---

## License

MIT — build, learn, present.
