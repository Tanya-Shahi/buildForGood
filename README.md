# AWAAZ

AWAAZ (आवाज़, meaning "voice") is a women's safety platform we're building to handle the full lifecycle of a safety incident: route risk prediction before something happens, live sensor based threat detection during a journey, and an evidence and escalation pipeline after an SOS is triggered.

It's a monorepo with an Expo / React Native frontend and a FastAPI backend.

## Why we're building this

Most safety apps are either a single panic button or a static "report a crime" map. Neither helps you in the moment. AWAAZ tries to combine three things that usually live in separate apps:

* a risk score for a route, based on historical incident data and a trained ML model, so you can avoid a bad area before you're in it
* live sensor fusion (motion, location deviation, audio cues, a silent duress PIN) that can detect a threat without you needing to pull out your phone and tap anything
* a verified incident feed and an NGO / moderator layer so reports actually get checked instead of sitting in a database unvalidated

## Repo layout

```
buildForGood/
├── frontend/        Expo (React Native + web) app
└── backend/         FastAPI service
```

### frontend/

React Native app built on Expo SDK 54, written in TypeScript, with React Navigation for screen flow. Runs on iOS, Android, and web from the same codebase.

Key folders inside `frontend/src/`:

* `screens/`: Login, Register, Dashboard, Assistant, Incident reporting
* `components/`: `SafetyMap` and `RiskMonitor` are the two main pieces of UI logic
* `context/`: auth state and the telemetry stream that feeds the risk monitor
* `hooks/useLocationTracker.ts`: wraps `expo location` for continuous tracking
* `api/client.ts`: axios instance talking to the backend

### backend/

FastAPI service on Python 3.12, backed by Postgres with PostGIS for spatial queries, and Redis for telemetry caching. Alembic handles migrations.

Routers live under `app/api/v1/`:

| Router | What it does |
|---|---|
| `auth.py` | login and register, JWT issuance |
| `routes.py` | incident reporting (including voice note transcription via Gemini), NGO verify and flag actions |
| `telemetry.py` | ingests live sensor data from the app |
| `sensors.py` | device sensor endpoints |
| `escalation.py` | the actual SOS and escalation flow |
| `evidence_bridge.py` | ML feedback loop and evidence handling |
| `legal.py` | legal companion and resources |
| `support.py` | peer support forum |
| `contacts.py` | emergency contacts |

The interesting logic isn't really in the routers though, it's in `app/services/`:

* **`fusion_engine.py`**: takes a set of active sensor flags (route deviation, motion anomaly, audio scream detection, silent duress PIN) and weighs them against each other. A duress PIN alone is enough to escalate; a single motion anomaly isn't. This is what decides whether a real alert gets fired.
* **`risk_engine.py`**: loads a LightGBM model (`risk_v1.txt`) and scores locations and routes using historical incident density plus geospatial features.
* **`trust_engine.py`**: rewards or penalizes a user's trust score based on whether their reports get verified or flagged as false by an NGO moderator. This is meant to keep the incident feed from getting spammed with bad data.
* **`gemini_service.py`**: handles audio transcription for voice reported incidents.
* **`ml_feedback_service.py`**: retrains and reloads the risk model as new verified data comes in.

There's also a `scripts/` folder with `generate_synthetic_data.py` and `train_lgbm.py`, used to bootstrap the risk model before there's enough real incident data to train on directly.

## Running it locally

### Backend

You'll need Python 3.12, Docker (for Postgres and Redis), and a Gemini API key if you want voice transcription to actually work.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Spin up Postgres (with PostGIS) and Redis:

```bash
docker-compose up -d
```

Copy `.env.example` to `.env` and fill in the values:

```
GEMINI_API_KEY=
DATABASE_URL=
REDIS_URL=
SECRET_KEY=
ANONYMITY_SALT=
```

`DATABASE_URL` and `REDIS_URL` should point at the ports docker-compose exposes (5433 and 6380 by default, not the standard 5432 and 6379, which avoids clashing with anything you've already got running locally).

Run migrations, then start the server:

```bash
alembic upgrade head
python run.py
```

The API comes up on `http://localhost:8000`, with OpenAPI docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npx expo start
```

From there you can run it on iOS or Android simulators, a physical device via Expo Go, or in the browser with `npm run web`. Point `frontend/src/api/client.ts` at your local backend URL if it's not already set correctly.

## Deployment

The backend is set up for Railway (it reads `PORT` and `RAILWAY_ENVIRONMENT_NAME` from the environment in `run.py`, and there's an `Aptfile` for the `libgomp1` system dependency LightGBM needs).

The frontend deploys as a static web export. `npm run build` runs `expo export -p web`, and the output goes to `dist/`. Works fine on Vercel with the root directory set to `frontend/`.

## Status

Early stage, actively being built. Expect rough edges. Some routes are stubbed, the ML model is currently trained on synthetic data while we collect real incident reports, and there's no test suite yet beyond `test_ws_client.py` for manually poking at the websocket telemetry endpoint.

## License

See `frontend/LICENSE`.
