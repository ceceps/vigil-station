# Changelog

All notable changes to Vigil Station (formerly Mission Planning Assistant).

## [1.2.0] — 2026-08-24

### Added
- Date picker restrictions: all date inputs capped to today (no future/past drift)
- Retry logic for NASA DONKI API (2 attempts, DEMO_KEY fallback)
- `data_available` field on SpaceWeatherResponse (UNAVAILABLE vs QUIET status)
- Demo recording pipeline: Playwright test + edge-tts voiceover + ffmpeg merge
- Full walkthrough video with voiceover at `docs/demo/vigil-station-demo-voiceover.mp4`
- Start/stop scripts (`start.sh`, `stop.sh`, `test.sh`, `generate-demo.sh`)

### Fixed
- Space weather "UNAVAILABLE" state shown when NASA API fails (was showing misleading "quiet")
- Default `endTime` in ScheduleTable and ConflictPanel (was set to tomorrow)

### Changed
- Rebranded from "Mission Planning Assistant" to **Vigil Station**
- Backend `@app.on_event` deprecated startup → `@asynccontextmanager` lifespan
- README rewritten (~180 lines) to match current project state
- NASA API timeout reduced from 15s to 10s

## [1.1.0] — 2026-08-23

### Added
- Analytics panel with AI-powered insights and date range filtering
- Space weather panel (NASA DONKI integration)
- Dark/light mode toggle with theme switcher
- Leaflet 2D map showing ground stations and satellite ground tracks
- Shimmer loading components for better UX
- E2E workflow tests and comprehensive test suite
- Approval state persistence across tab switches
- Conflict detection persistence to database
- AI recommendations persistence to database
- Stop script to free backend/frontend ports
- Loading spinner on Generate Recommendation button

### Fixed
- Auto-load satellite passes on Schedule tab initial render
- Auto-load conflicts on Conflicts tab initial render
- Duplicate parallel API fetching and transient error status in UI
- Calculating badge display bug and satellite name 3LE prefix sanitization
- Pass matching and overlap validation in recommendation endpoint
- Weather timezone bug
- Analytics layout and data issues

### Changed
- Tailwind CSS v4 upgrade
- Schedule table range selector with end date for broader data
- Backend response delay handling (background readiness check)

## [1.0.0] — 2026-08-22

### Added
- TLE fetch + cache from Space-Track.org (Iridium group, 6h validity)
- Pass window calculation via Skyfield/SGP4
- Schedule conflict detection (overlap at same ground station)
- LLM-powered conflict resolution recommendations (Claude Opus 5)
- AI reasoning grounded in elevation, timing, weather/space-weather data
- Approve/override workflow with human-in-the-loop design
- Schedule table with status badges (clear / conflict / recommended)
- Open-Meteo weather integration
- NASA DONKI space weather integration
- FastAPI backend with PostgreSQL cache
- React frontend (Vite + Tailwind)
- Axios HTTP client with 30s timeout
- Monorepo structure (`apps/backend`, `apps/frontend`)

---

*Format based on [Keep a Changelog](https://keepachangelog.com/).*
