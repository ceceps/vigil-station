# AGENTS.md — Mission Planning Assistant

This document is the working instructions for the agent (IBM Bob) building this application. Read this entire file before creating or modifying any code. The full spec lives in `docs/mission-planning-assistant-spec.md` — this document is an operational summary of that spec, not a replacement for it.

## 1. Project Summary

A **ground station contact scheduling assistant** built for a Space Exploration hackathon. The system calculates contact windows (passes) between satellites and ground stations from real orbital data, detects scheduling conflicts, and provides conflict-resolution recommendations via AI reasoning — with clear justification, not just raw numbers.

**Core principles that must be upheld:**
- **Human-in-the-loop.** The system must NOT execute anything autonomously. The operator always approves or overrides.
- **Data must be real**, not permanently mocked. Fixtures are fine for testing, but the production path must connect to Space-Track.org.
- **Every AI recommendation must include a `reasoning` field** in natural language that references actual data (elevation, timing, weather/space-weather status). This is the project's main differentiator — never build a recommendation endpoint that returns only numbers without an explanation.

## 2. Tech Stack (mandatory — do not improvise a change without strong justification)

| Layer | Technology |
|---|---|
| Backend | Python + FastAPI |
| Orbital mechanics | Skyfield (built on SGP4) |
| Space-Track client | `spacetrack` package (PyPI) |
| Database | SQLite for the hackathon |
| LLM reasoning | via API, called from `services/llm_reasoner.py` |
| Weather data | Open-Meteo API |
| Space weather data | NASA DONKI (`api.nasa.gov`) |
| Frontend | React (pure admin panel, not a full framework) |
| Frontend HTTP client | Axios or native fetch |

## 3. Monorepo Structure (mandatory)

```
mission-planning-assistant/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api/            # one router file per resource
│   │   │   ├── core/            # config.py, cache.py
│   │   │   ├── services/        # spacetrack_client, orbit_calc, conflict_detector,
│   │   │   │                    # weather_client, space_weather_client, llm_reasoner
│   │   │   ├── models/
│   │   │   └── schemas/         # Pydantic request/response
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── frontend/
│       ├── src/
│       │   ├── pages/           # ScheduleTable, ConflictPanel, Approvals
│       │   ├── components/
│       │   └── api/client.js
│       ├── package.json
│       └── .env.example
├── packages/shared-types/       # optional
├── docs/mission-planning-assistant-spec.md
└── README.md
```

Do not create files outside this structure without an explicit reason. Backend and frontend are separate dependency units — do not mix `node_modules` with `venv`/`requirements.txt` at the root.

## 4. API Contract (follow exactly — field names and JSON structure)

- `GET /satellites` → `{ "satellites": [{ "norad_id", "name", "group" }] }`
- `GET /ground-stations` → `{ "ground_stations": [{ "id", "name", "lat", "lon", "min_elevation_deg" }] }`
- `GET /passes?satellite_id&ground_station_id&start&end` → `{ "passes": [{ "id", "satellite_id", "ground_station_id", "start_time", "end_time", "max_elevation_deg" }] }`
- `GET /conflicts?ground_station_id&start&end` → `{ "conflicts": [{ "ground_station_id", "pass_ids", "overlap_start", "overlap_end" }] }`
- `POST /recommendations` body `{ "conflict_id" }` → `{ "recommendation": { "conflict_id", "suggested_action", "target_pass_id", "alternative_window": { "start_time", "end_time" }, "reasoning" } }`
- `POST /schedule/{id}/approve` body `{ "approved", "override_reason" }` → `{ "status", "schedule_id" }`

Full example payloads are in section 6.4 of the spec document. All timestamps use ISO 8601 UTC.

## 5. Data Sources & Technical Gotchas (important — do not skip)

- **Space-Track.org**: authentication uses a session cookie (POST `identity` + `password` to `/ajaxauth/login`), NOT a static API key. Log in once, reuse the cookie, do not log in on every request.
- **Satellite group**: start with the **Iridium** group (LEO), **3LE** format.
- **6-digit catalog number gotcha**: CelesTrak/Space-Track recently transitioned to 6-digit catalog numbers for new objects. Make sure the TLE parser used (via the `spacetrack` package) supports the newer GP data format — do not assume all IDs are always 5-digit.
- **Caching is mandatory**: fetch TLEs from Space-Track once at startup or on a schedule (store in SQLite), not on-demand for every user request — they enforce strict rate limits.
- **NASA DONKI**: requires a free API key from `api.nasa.gov`.
- **Open-Meteo**: no API key required.

## 6. Build Priorities (follow this order — do not jump to P1 before P0 is done)

**P0 — required for the demo:**
1. Fetch + cache TLEs (Iridium group) from Space-Track
2. Calculate pass windows per satellite × ground station (Skyfield)
3. Detect schedule conflicts (overlap at the same ground station)
4. LLM generates a recommendation + `reasoning` grounded in actual data
5. UI: schedule table + status (clear/conflict/recommended)
6. Operator approve/override

**P1 — if time permits:**
- Integrate weather (Open-Meteo) into the reasoning
- Integrate space weather (DONKI) into the reasoning
- Simple 2D map of ground station positions + satellite ground tracks

**P2 — do not build now, but do not make architectural decisions that would foreclose these options later:**
- Multi-tenant / multi-operator support
- Automatic execution to ground stations

**Scope-control rule:** if P0 is not solid by 70% of remaining time, skip P1 entirely. A demo with strong reasoning on orbital data alone beats a demo with many features that's fragile.

## 7. Non-Goals (do not build these)

- A fully autonomous system that executes without human approval
- A custom weather/space-weather prediction model (always consume third-party APIs)
- Real-time 3D orbit visualization
- A connection to physical ground station hardware

## 8. Code Conventions

- Python: follow PEP 8, use Pydantic for all request/response schemas, explicit typing in every service function.
- One service = one responsibility (`spacetrack_client.py` only handles fetch+auth, `orbit_calc.py` only handles calculations, etc.).
- Every new endpoint must have verifiable acceptance criteria — see section 5 of the spec document for the Given/When/Then format example.
- Environment variables (API keys, credentials) always go through `.env`, never hardcoded. Update `.env.example` whenever a new variable is added.
- Commit small and often, per functional unit (e.g., "add pass window calculation service" rather than one large commit for the entire backend).

## 9. Open Questions (undecided — confirm with the user before making major decisions in these areas)

- Ground station coordinates: hypothetical or referencing a real location?
- Specific LLM model/provider to use for `llm_reasoner.py`?
- Final number of satellites and ground stations for the demo scenario?
