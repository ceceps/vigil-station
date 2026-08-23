# Vigil Station

AI-Powered Ground Station Scheduling Assistant | IBM Bob Space Exploration Hackathon

## What This Does

Vigil Station calculates satellite contact windows for three ground stations in Southeast Asia (Jakarta, Bandung, Singapore), detects scheduling overlaps, and generates AI recommendations for conflict resolution. Every recommendation includes plain-English reasoning that references actual elevation angles and timing. The operator always approves or overrides. Nothing executes autonomously.

## Features

### Scheduling
- Pass window calculations (AOS, LOS, Max Elevation, Duration) from real TLE orbital data via Space-Track.org
- SGP4 propagator for accurate orbital mechanics
- Color-coded elevation badges: green (above 45 degrees), yellow (30-44), red (below 30)
- Satellite and ground station filters with date range selection

### Conflict Detection
- Automatic overlap identification across all three ground stations
- Conflict cards showing both passes side-by-side with overlap duration badges
- Filter by ground station and date range

### AI Recommendations
- Claude Opus 5 generates resolution plans referencing actual data values
- Output includes suggested action, alternative time window, and reasoning
- Recommendations stored in PostgreSQL for audit trail

### Approval Workflow
- Approve AI suggestion or override with mandatory reason
- Stats cards tracking pending, approved, and overridden decisions
- Filter buttons to isolate items by status
- Full decision history logged to PostgreSQL

### Map
- Dark-themed Leaflet map with ground station pins (green)
- Animated satellite positions (blue dots)
- Active pass windows shown as orange dashed lines
- Zoom controls to see full Southeast Asian coverage

### Space Weather
- Solar flare, geomagnetic storm, and CME tracking from NASA DONKI API
- Automatic retry with DEMO_KEY fallback when API returns errors
- Communication impact assessment with risk factors

### Analytics
- Conflict resolution rates and station contention metrics
- Timeframe filters (Today, Last 7 Days, Last 30 Days, All Time, custom)
- AI-generated executive reports via Claude

### UI
- Dark/light theme toggle
- Shimmer loading states
- Responsive layout with Tailwind CSS

## Tech Stack

**Backend:**
- Python + FastAPI
- SQLAlchemy ORM + Alembic migrations
- Skyfield (SGP4 orbital mechanics)
- Anthropic Claude API (Opus 5)
- Space-Track.org (TLE data)
- Open-Meteo API (weather)
- NASA DONKI API (space weather)

**Frontend:**
- React 18 + Vite
- Tailwind CSS v4
- Leaflet (interactive map)
- Axios (HTTP client)
- Bun (package manager)

**Testing:**
- Vitest (frontend unit tests)
- Playwright (E2E demo recording)
- pytest (backend tests)

**Database:**
- SQLite (default, config: `sqlite:///./mission_planning.db`)
- PostgreSQL supported via `DATABASE_URL` env var

## Getting Started

### Prerequisites

- Python 3.9+
- Bun (install: `curl -fsSL https://bun.sh/install | bash`)
- Space-Track.org account (free: https://www.space-track.org/auth/createAccount)
- Anthropic API key (https://console.anthropic.com/)
- NASA API key (optional, free: https://api.nasa.gov/)

### Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd vigil-station

# Backend
cd apps/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials

# Frontend
cd ../frontend
bun install

# Run both
cd ../..
chmod +x start.sh
./start.sh
```

Backend runs on `http://localhost:8000`, frontend on `http://localhost:5173`.

### Scripts

| Script | What it does |
|--------|-------------|
| `./start.sh` | Starts backend + frontend, opens browser |
| `./stop.sh` | Kills processes, frees ports |
| `./test.sh` | HTTP health checks against running servers |
| `./generate-demo.sh` | Runs Playwright walkthrough + generates voiceover MP4 |

### Environment Variables

Create `apps/backend/.env`:

```env
SPACETRACK_USERNAME=your_username
SPACETRACK_PASSWORD=your_password
ANTHROPIC_API_KEY=your_api_key
NASA_API_KEY=DEMO_KEY
DATABASE_URL=sqlite:///./mission_planning.db
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/satellites` | List all tracked satellites |
| GET | `/ground-stations` | List all ground stations |
| GET | `/passes` | Calculate pass windows (params: satellite_id, ground_station_id, start, end) |
| GET | `/conflicts` | Detect scheduling conflicts |
| POST | `/recommendations` | Generate AI recommendation (body: {conflict_id}) |
| POST | `/schedule/{id}/approve` | Approve or override (body: {approved, override_reason}) |
| GET | `/space-weather` | Space weather events from NASA DONKI |
| GET | `/analytics/insights` | AI-driven operational analytics |

API docs at `http://localhost:8000/docs` when running.

## Ground Stations

| Station | Latitude | Longitude | Min Elevation |
|---------|----------|-----------|---------------|
| Jakarta | -6.2088 | 106.8456 | 10 degrees |
| Singapore | 1.3521 | 103.8198 | 10 degrees |
| Bandung | -6.9175 | 107.6191 | 10 degrees |

## Testing

```bash
# Backend
cd apps/backend
./venv/bin/python -m pytest tests/

# Frontend
cd apps/frontend
bun run test

# E2E demo (requires running servers)
cd apps/frontend
bunx playwright test
```

## Demo Video

Generate a walkthrough video with voiceover:

```bash
./generate-demo.sh
```

This runs Playwright through all tabs, captures screenshots, generates TTS audio (English male voice), and merges everything into `docs/demo/vigil-station-demo-voiceover.mp4`.

## Project Structure

```
vigil-station/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api/           # 8 routers
│   │   │   ├── core/          # config, cache
│   │   │   ├── services/      # orbit_calc, llm_reasoner, etc.
│   │   │   └── schemas/       # Pydantic models
│   │   ├── tests/
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── pages/         # 5 pages
│       │   ├── components/    # LeafletMap, Shimmer
│       │   └── api/client.js
│       └── package.json
├── docs/
│   ├── demo/                  # generated video + screenshots
│   └── AGENTS.md
│   └── PLANNING.md
├── generate-demo.sh
├── start.sh
├── stop.sh
└── test.sh
```

## Built With IBM Bob

This project was built entirely with IBM Bob (Claude Code agent). The agent handled architecture, code generation, debugging, and testing across 7+ PR cycles. It resolved issues like NASA API 503 errors (added retry with DEMO_KEY fallback), Playwright timeout problems, and TTS voiceover pipeline integration. The human reviewed decisions; the agent wrote the code.

## License

Created for the IBM Bob Space Exploration Hackathon.
