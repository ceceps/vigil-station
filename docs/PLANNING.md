# Design Spec: Mission Planning Assistant
### Ground Station Contact Scheduling with AI Decision-Support
**Challenge:** IBM Bob — Space Exploration Hackathon
**Status:** Draft v1 — for hackathon build (48–72 hours)

---

## 1. Problem Statement

Small satellite operators (CubeSats, small-sats) must schedule contact between satellites and ground stations within narrow time windows — a satellite is only "visible" from a ground station for a few minutes per orbit. This scheduling is complex because it has to account for several constraints at once: orbital elevation, scheduling conflicts between satellites competing for the same ground station, weather conditions affecting link quality, and space weather disturbances (solar flares, geomagnetic storms).

Today this process is often done manually or with disconnected tools (orbit calculators, weather reports, space weather feeds) without a single system that consolidates everything into an actionable recommendation. As a result, valuable contact windows can be missed, or reschedule decisions get made without fully weighing all the reliability-relevant factors.

**Impact of not solving this:** wasted communication windows, delayed mission data delivery, scheduling decisions made without comprehensive consideration of reliability factors.

---

## 2. Goals

1. The system accurately calculates contact windows (passes) between satellites and ground stations based on real orbital data (TLE).
2. The AI detects schedule conflicts (two satellites needing the same ground station at overlapping times) and provides a resolution recommendation with clear reasoning.
3. The AI incorporates at least two additional constraint sources (weather and/or space weather) into its recommendation — not just orbit calculation.
4. AI recommendations remain **human-in-the-loop**: the operator always approves/overrides, consistent with mission-reliability principles in the space industry.
5. The demo can narrate the "raw data → actionable insight" flow in under 2 minutes.

---

## 3. Non-Goals

- **Not a fully autonomous scheduler** — v1 will not execute commands to real satellites/ground stations. Reason: operational and security complexity is out of scope for the hackathon, and human-in-the-loop is more aligned with the "mission safety and reliability" theme.
- **Not a multi-tenant platform for multiple different operators** — v1 is single-context (one "operator" with several satellites and ground stations). Reason: focus hackathon time on reasoning depth rather than multi-user infrastructure.
- **Not a custom weather/space-weather prediction engine** — v1 consumes existing third-party APIs rather than building a new prediction model. Reason: out of scope for the timeline and not the project's core differentiator.
- **Not real-time 3D orbit visualization** — v1 is limited to a pass-window table/list and (optionally) a simple 2D map. Reason: prioritize time on the reasoning layer over a graphics engine.
- **Not integration with real physical ground station hardware** — v1 uses self-defined ground station coordinates (which may be hypothetical), not a connection to hardware. Reason: no hardware access available in the hackathon context.

---

## 4. User Stories

**Primary persona: Satellite Operations Planner**

- As an operator, I want to see all upcoming pass windows for my satellites, so I know when each satellite can be contacted.
- As an operator, I want the system to automatically alert me when two satellites need the same ground station at overlapping times, so I don't lose a contact window without realizing it.
- As an operator, I want the AI to provide a rescheduling recommendation with reasoning (e.g., elevation still meets threshold, better weather), so I can make a fast decision with enough context.
- As an operator, I want to see whether any space weather disturbance could affect link quality before a given pass, so I can adjust priorities accordingly.
- As an operator, I want to be able to approve or override the AI's recommendation, so the final decision stays in my hands.
- As an operator, I want the system to explain its recommendations in clear language (not just raw numbers), so I don't need to be an orbital mechanics expert to understand the decision.

---

## 5. Requirements

### Must-Have (P0) — required for the demo
- [x] Fetch and cache TLE data from CelesTrak/Space-Track for a limited satellite group (e.g., a specific weather/active group, not the entire catalog)
- [x] Calculate pass windows (start time, end time, max elevation) for each satellite × ground station combination
- [x] Detect schedule conflicts between overlapping pass windows at the same ground station
- [x] AI (LLM) generates a conflict-resolution recommendation in natural language, with reasoning grounded in actual data (elevation, alternative timing)
- [x] UI displays a table/list of scheduled passes with status (clear / conflict / rescheduled)
- [x] Operator can approve/override the recommendation

**Acceptance criteria (example):**
- Given two satellites have overlapping pass windows at the same ground station
- When the system runs scheduling
- Then the system displays the conflict and the AI provides a valid alternative-time recommendation (elevation above the minimum threshold)

### Nice-to-Have (P1) — if time allows
- [x] Integrate weather data (cloud cover) as an additional recommendation factor
- [x] Integrate space weather data (NASA DONKI) to flag potential link disturbances
- [x] Simple 2D map showing ground station positions and satellite ground tracks
- [x] Decision history log (approve/override) for transparency

### Future Considerations (P2) — out of scope for v1, but architecturally anticipated
- [ ] Multi-operator/multi-tenant support
- [ ] Long-range conflict prediction (30 days ahead) with automatic optimization
- [ ] Automatic execution to ground stations (with an approval workflow)

---

## 6. Technical Feasibility Assessment

**Feasibility for a hackathon build: Feasible, with tightly managed scope.**

| Component | Data Source | Status |
|---|---|---|
| Satellite orbital data | CelesTrak/Space-Track (TLE/GP data, limited group) | Public, free — requires local caching due to rate limits |
| Pass window calculation | SGP4 library (available in nearly every language) | Deterministic math, well-tested |
| Space weather (optional) | NASA DONKI via api.nasa.gov | Public, requires a free API key |
| Weather (optional) | General weather API (e.g., Open-Meteo) | Public, no API key required |
| Reasoning/recommendation | LLM (via IBM Bob as the dev environment) | Depends on the chosen agent architecture |

**Biggest risk:** CelesTrak recently transitioned to a 6-digit catalog format for new objects — make sure the TLE library/parser you use supports the newer GP data format, not just the classic 5-digit TLE format. Verify this early, before much logic is built on top of it.

**Chosen stack:** Python backend, React frontend as a pure admin panel (not a full-stack framework). IBM Bob is used as the development environment (agentic coding assistant), not as something that dictates the application's runtime architecture.

### 6.1 Architecture

```
┌─────────────────────┐         ┌──────────────────────────────┐
│  React (Admin UI)   │ ◄─────► │  Python Backend (API)         │
│  - Pass window table │  REST/  │  - FastAPI                    │
│  - Conflict panel     │  JSON   │  - spacetrack client (fetch)   │
│  - Approve/override  │         │  - Skyfield/SGP4 (pass calc)  │
└─────────────────────┘         │  - LLM call (reasoning)        │
                                  │  - Cache layer (local TLE)     │
                                  └──────────────────────────────┘
                                              │
                                              ▼
                          Space-Track.org · NASA DONKI · Weather API
```

**Technical choices:**
- **FastAPI** — chosen because its native async support is useful for waiting on several external APIs at once (Space-Track, DONKI, weather, LLM), and it auto-generates OpenAPI documentation.
- **Skyfield** (built on SGP4) — for pass window calculation with a friendlier API than a raw SGP4 implementation, already handling coordinate conversion and elevation.
- **Cache TLEs in a lightweight database** (SQLite is enough for the hackathon) — fetch from Space-Track once at startup/on a schedule, not on every user request, to avoid rate limits.
- **Space-Track library:** the Python `spacetrack` package (PyPI) — supports all request classes, predicate validation, and built-in automatic rate limiting.

### 6.2 Tech Stack Table

| Layer | Technology | Rationale |
|---|---|---|
| Backend framework | Python + FastAPI | Native async for multiple external API calls, auto OpenAPI docs |
| Orbital mechanics | Skyfield (built on SGP4) | Ready-made pass window, elevation, and coordinate conversion |
| Space-Track client | `spacetrack` (PyPI) | Built-in session auth, rate limiting, and query builder |
| Database | SQLite (hackathon) → PostgreSQL (if continued post-hackathon) | Local TLE cache, stores ground stations & schedules, light enough for demo scope |
| AI/LLM reasoning | LLM via API (model chosen based on available access) | Generates natural-language conflict-resolution recommendations |
| Weather data | Open-Meteo API | Free, no API key, sufficient for ground station cloud cover |
| Space weather data | NASA DONKI (api.nasa.gov) | Flags solar flares/geomagnetic storms as an additional constraint |
| Frontend | React (admin panel) | Schedule table, conflict panel, approve/override flow |
| Frontend HTTP client | Axios or native fetch | Consumes the backend REST API |
| Dev tool | IBM Bob | Agentic coding assistant during development (challenge requirement) |
| Task runner / local orchestration | `venv` + `npm`/`pnpm` per package | Keeps backend and frontend dependencies separate within the monorepo |

### 6.3 Monorepo Structure

```
mission-planning-assistant/
├── apps/
│   ├── backend/                      # Python FastAPI service
│   │   ├── app/
│   │   │   ├── main.py               # FastAPI entry point
│   │   │   ├── api/
│   │   │   │   ├── satellites.py     # Router: /satellites
│   │   │   │   ├── ground_stations.py# Router: /ground-stations
│   │   │   │   ├── passes.py         # Router: /passes
│   │   │   │   ├── conflicts.py      # Router: /conflicts
│   │   │   │   ├── recommendations.py# Router: /recommendations
│   │   │   │   └── schedule.py       # Router: /schedule
│   │   │   ├── core/
│   │   │   │   ├── config.py         # Env vars, settings
│   │   │   │   └── cache.py          # TLE cache layer (SQLite)
│   │   │   ├── services/
│   │   │   │   ├── spacetrack_client.py  # Auth + TLE fetch wrapper
│   │   │   │   ├── orbit_calc.py         # Skyfield pass window calc
│   │   │   │   ├── conflict_detector.py  # Schedule overlap detection logic
│   │   │   │   ├── weather_client.py     # Open-Meteo wrapper
│   │   │   │   ├── space_weather_client.py # NASA DONKI wrapper
│   │   │   │   └── llm_reasoner.py       # Prompt + LLM call for recommendations
│   │   │   ├── models/
│   │   │   │   ├── satellite.py
│   │   │   │   ├── ground_station.py
│   │   │   │   └── schedule.py
│   │   │   └── schemas/              # Pydantic request/response schemas
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── .env.example
│   │
│   └── frontend/                     # React admin panel
│       ├── src/
│       │   ├── pages/
│       │   │   ├── ScheduleTable.jsx
│       │   │   ├── ConflictPanel.jsx
│       │   │   └── Approvals.jsx
│       │   ├── components/
│       │   ├── api/
│       │   │   └── client.js         # Axios instance + endpoint calls
│       │   └── App.jsx
│       ├── package.json
│       └── .env.example
│
├── packages/
│   └── shared-types/                 # (optional) shared FE-BE types/schemas, if time allows
│
├── docs/
│   └── mission-planning-assistant-spec.md   # This document
│
├── .gitignore
└── README.md
```

**Structural note:** `apps/` separates backend and frontend as independent units (each with its own dependency management — `venv`/`requirements.txt` for the backend, `package.json` for the frontend), while `packages/shared-types` is optional and only worth creating if time allows, to keep the API contract in sync between FE and BE.

### 6.4 API Design (Detailed Request/Response)

**`GET /satellites`**
Response:
```json
{
  "satellites": [
    { "norad_id": 43613, "name": "IRIDIUM 106", "group": "iridium" }
  ]
}
```

**`GET /ground-stations`**
Response:
```json
{
  "ground_stations": [
    { "id": 1, "name": "Ground Station A", "lat": -6.9, "lon": 107.6, "min_elevation_deg": 10 }
  ]
}
```

**`GET /passes?satellite_id=43613&ground_station_id=1&start=2026-08-11T00:00:00Z&end=2026-08-12T00:00:00Z`**
Response:
```json
{
  "passes": [
    {
      "id": "pass_001",
      "satellite_id": 43613,
      "ground_station_id": 1,
      "start_time": "2026-08-11T02:14:00Z",
      "end_time": "2026-08-11T02:26:00Z",
      "max_elevation_deg": 47.3
    }
  ]
}
```

**`GET /conflicts?ground_station_id=1&start=...&end=...`**
Response:
```json
{
  "conflicts": [
    {
      "ground_station_id": 1,
      "pass_ids": ["pass_001", "pass_007"],
      "overlap_start": "2026-08-11T02:20:00Z",
      "overlap_end": "2026-08-11T02:24:00Z"
    }
  ]
}
```

**`POST /recommendations`**
Request:
```json
{ "conflict_id": "pass_001-pass_007" }
```
Response:
```json
{
  "recommendation": {
    "conflict_id": "pass_001-pass_007",
    "suggested_action": "reschedule",
    "target_pass_id": "pass_007",
    "alternative_window": {
      "start_time": "2026-08-11T03:57:00Z",
      "end_time": "2026-08-11T04:09:00Z"
    },
    "reasoning": "The alternative pass still reaches a maximum elevation of 32° (above the 10° threshold), and does not overlap with any other schedule at the same ground station."
  }
}
```

**`POST /schedule/{id}/approve`**
Request:
```json
{ "approved": true, "override_reason": null }
```
Response:
```json
{ "status": "approved", "schedule_id": "pass_007" }
```

**API design principle:** every `/recommendations` response must include a `reasoning` field in natural language — this is what distinguishes the system from a plain orbit calculator, and is a key point when demoing to judges.

---

## 7. Success Metrics (hackathon context, not a production product)

Since this isn't being launched to real users, "success" here is measured by demo readiness and narrative strength:

- **Leading indicator:** end-to-end demo runs without errors in the prepared scenario (target: 100% reliable during the presentation)
- **Leading indicator:** the "raw data → insight" flow can be explained in the demo in ≤ 2 minutes
- **Qualitative:** judges can understand *why* the AI made its recommendation (reasoning transparency), not just see the output

---

## 8. Open Questions

- **[Stakeholder/team]** Will the demo ground stations use hypothetical coordinates, or reference a real location (e.g., a university/amateur radio community)?
- **[Engineering]** Does IBM Bob impose any specific architectural constraints/preferences (e.g., requiring a particular model or agent framework from IBM) that need confirming before coding starts?
- **[Engineering]** How many satellites and ground stations are realistic to set up for the demo so that a schedule conflict emerges naturally (rather than being forced)?
- **[Team]** Is the weather and space-weather feature (P1) worth scoping into the available time, or better allocated to polishing P0 and demo storytelling?

---

## 9. Timeline & Phasing (adapted for a hackathon)

**Phase 1 — Data foundation (early priority):**
Set up TLE fetch + cache, implement pass window calculation with SGP4, validate the data format (especially the 6-digit catalog issue).

**Phase 2 — Conflict detection & reasoning:**
Build the schedule-overlap detection logic, integrate the LLM to generate recommendations grounded in the already-calculated data.

**Phase 3 — UI & demo polish:**
Schedule table, recommendation panel, approve/override flow, prepare a demo scenario that clearly showcases a conflict.

**Phase 4 (if time remains) — P1 features:**
Add the weather and/or space weather layer to the reasoning.

**Scope-control principle:** if Phases 1–3 are not solid by 70% of remaining time, skip Phase 4 entirely — a demo with strong reasoning on orbital data alone is stronger than a demo with many features but fragile execution.
