# Crime-Watch: Master Implementation Guide

> **Who this file is for:** You (Benhail) and Claude in every future session.  
> **What it does:** Defines the full system, tech stack, phase order, and rules  
> that every other prompt file must follow. Read this first. Always.

---

## 1. Project Identity

**System Name:** Crime-Watch  
**Type:** AI-driven Decision Support System (DSS) — NOT an autonomous policing system  
**Target User:** Zimbabwe Republic Police (ZRP) officers and verified community reporters  
**Academic Context:** BSc Computer Science Dissertation — Midlands State University  
**Authors:** Benhail Moyo (R2312487F) & Oslea Mukuhlani (R252775F)

**The three things this system must do:**
1. Accept a crime report in English, Shona, or Ndebele → classify it → store it
2. Analyze stored incidents spatially → generate crime hotspots on a map
3. Take those hotspots → generate a fuel-efficient patrol route using two algorithms → compare them

Everything else is secondary. If a feature doesn't serve one of these three things, it is out of scope.

---

## 2. Tech Stack (Final, Non-Negotiable)

| Layer | Technology | Why |
|---|---|---|
| Backend language | Python 3.11 | AI/ML library ecosystem |
| Web framework | Flask 3.x (app factory pattern) | Lightweight, easy to test, no magic |
| ORM | SQLAlchemy 2.x + GeoAlchemy2 | PostGIS integration |
| Database | PostgreSQL 15 + PostGIS 3.4 | Spatial queries (DBSCAN, KDE, routing) |
| AI/NLP | Google Gemini 1.5 Flash | LLM for report classification |
| Language detection | Custom dictionary (Shona/Ndebele) | langdetect doesn't support these |
| GIS clustering | scikit-learn DBSCAN | Standard, well-documented |
| KDE heatmaps | scipy gaussian_kde | Standard |
| Graph/routing | NetworkX | Dijkstra's shortest path |
| Genetic Algorithm | DEAP library | Industry standard GA framework |
| Auth | Flask-JWT-Extended | Stateless, testable |
| Frontend | React 18 | Component-based, industry standard |
| Mapping | Leaflet.js | Open source, works offline |
| Containerization | Docker + Docker Compose | Reproducible environment |
| Testing | pytest + pytest-flask | Standard Python testing |
| Version control | Git + GitHub | Non-negotiable |

**What is NOT in the stack (and why):**
- No Django: too much magic, harder to explain in a dissertation
- No Redux: React Context is sufficient for this scale
- No TensorFlow/PyTorch: we use Gemini API, not train models from scratch
- No Celery/Redis: async tasks are out of scope for proof-of-concept
- No facial recognition: explicitly excluded in dissertation delimitations

---

## 3. Repository Structure

```
crime-watch/
├── backend/
│   ├── app/
│   │   ├── __init__.py              ← App factory (create_app)
│   │   ├── api/v1/routes/           ← Flask Blueprints (one per domain)
│   │   │   ├── auth.py
│   │   │   ├── incidents.py
│   │   │   ├── hotspots.py
│   │   │   └── patrol.py
│   │   ├── models/
│   │   │   └── models.py            ← SQLAlchemy + PostGIS models
│   │   ├── services/
│   │   │   ├── nlp/
│   │   │   │   ├── triage.py        ← Gemini classification pipeline
│   │   │   │   ├── language_utils.py← Shona/Ndebele detection
│   │   │   │   └── dictionaries/    ← .txt word lists
│   │   │   ├── gis/
│   │   │   │   └── hotspot_analysis.py ← DBSCAN + KDE
│   │   │   └── routing/
│   │   │       ├── route_engine.py  ← Orchestrator + compare_algorithms()
│   │   │       ├── dijkstra_solver.py
│   │   │       └── genetic_solver.py
│   │   └── config/
│   │       └── settings.py          ← Dev/test/prod config classes
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── migrations/                  ← Flask-Migrate auto-generated
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── map/                 ← Leaflet crime map
│       │   ├── dashboard/           ← Stats + charts
│       │   ├── reports/             ← Incident submission form
│       │   └── shared/              ← Navbar, buttons, etc
│       ├── pages/                   ← Route-level page components
│       ├── hooks/                   ← Custom React hooks
│       ├── services/                ← API call functions (axios)
│       └── store/                   ← React Context state
├── ml/
│   ├── nlp/
│   │   ├── corpus/                  ← labeled_test_set.json (200+ reports)
│   │   └── evaluations/             ← evaluate_triage.py
│   ├── routing/
│   │   └── benchmarks/              ← run_benchmarks.py → Chapter 4 data
│   └── data/
│       ├── raw/                     ← Original dataset (gitignored)
│       ├── processed/               ← Cleaned data
│       └── synthetic/               ← Harare seed data (committed)
├── infra/
│   └── docker/
│       ├── Dockerfile.backend
│       ├── Dockerfile.frontend
│       └── init_db.sql
├── docs/
│   └── dissertation/                ← Architecture diagrams, ERDs
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. Data Models (Single Source of Truth)

These four models are the entire database schema. Do not add new models without updating this file.

### `User`
```
id, email, password_hash, role (community|officer|admin), is_active, created_at
```

### `Incident`
```
id, raw_text, language_detected, category, severity (HIGH|MEDIUM|LOW),
triage_confidence (float), triage_summary, status (PENDING|TRIAGED|ASSIGNED|RESOLVED),
location (PostGIS POINT), location_description, reported_by (FK→User), created_at
```

### `Hotspot`
```
id, boundary (PostGIS POLYGON), centroid (PostGIS POINT),
incident_count, risk_score (float 0-1), dominant_category,
analysis_date, created_at
```

### `PatrolRoute`
```
id, algorithm (dijkstra|genetic), route_geometry (PostGIS LINESTRING),
total_distance_km, estimated_fuel_litres, estimated_time_minutes,
hotspots_covered, computation_time_ms, hotspot_ids (JSON), created_at
```

---

## 5. API Contract

All endpoints use JSON. All protected endpoints require `Authorization: Bearer <jwt_token>`.

```
POST   /api/v1/auth/register        → { email, password, role }
POST   /api/v1/auth/login           → { email, password }

POST   /api/v1/incidents/           → { raw_text, location_lat, location_lng, location_description }
GET    /api/v1/incidents/           → ?severity=HIGH&limit=50
GET    /api/v1/incidents/<id>

POST   /api/v1/hotspots/analyze     → { days_back: 30 }
GET    /api/v1/hotspots/            → list all hotspots
GET    /api/v1/hotspots/heatmap     → ?min_lng&min_lat&max_lng&max_lat

POST   /api/v1/patrol/optimize      → { hotspot_ids, algorithm, start_lat, start_lng }
POST   /api/v1/patrol/compare       → { hotspot_ids }     ← Chapter 4 endpoint
GET    /api/v1/patrol/routes        → recent patrol routes

GET    /health                      → { status: "ok" }
```

---

## 6. Role-Based Access Control

| Action | community | officer | admin |
|---|---|---|---|
| Submit incident | ✓ | ✓ | ✓ |
| View incidents | own only | all | all |
| Run hotspot analysis | ✗ | ✓ | ✓ |
| View heatmap | ✓ | ✓ | ✓ |
| Generate patrol route | ✗ | ✓ | ✓ |
| Compare algorithms | ✗ | ✓ | ✓ |
| Manage users | ✗ | ✗ | ✓ |

---

## 7. Implementation Phase Order

Follow this order exactly. Do not jump ahead. Each phase has a clear "done" definition.

| Phase | Prompt File | Done When |
|---|---|---|
| **1** | `01_AUTH_AND_DATABASE.md` | `flask db upgrade` runs clean, JWT login returns token, roles enforced |
| **2** | `02_NLP_TRIAGE_ENGINE.md` | POST /incidents classifies a Shona report with ≥LOW confidence |
| **3** | `03_GIS_HOTSPOT_ANALYSIS.md` | DBSCAN clusters seed data into ≥1 hotspot, heatmap endpoint returns data |
| **4** | `04_PATROL_OPTIMIZATION_ENGINE.md` | /patrol/compare returns both algorithm results with all 5 metrics |
| **5** | `05_FRONTEND_DASHBOARD.md` | Map renders hotspots, incidents form submits successfully |
| **6** | `06_ACADEMIC_BENCHMARKING.md` | run_benchmarks.py outputs CSV, evaluate_triage.py outputs accuracy ≥75% |
| **7** | `07_TESTING_SUITE.md` | pytest passes with ≥80% coverage on services/ |
| **8** | Final integration + demo prep | All 4 objectives demonstrable end-to-end |

---

## 8. Dissertation Objective → Code Mapping

This table is critical. Every chapter in your dissertation must be traceable to code.

| Dissertation Objective | Code Component | Measurable Output |
|---|---|---|
| NLP module: categorize + prioritize reports, ≥75% accuracy | `services/nlp/triage.py` | `evaluate_triage.py` accuracy score |
| GIS interface: real-time hotspot mapping | `services/gis/hotspot_analysis.py` + Leaflet map | Hotspot polygons on map |
| Patrol engine: ≥15% fuel reduction | `services/routing/route_engine.py` | `compare_algorithms()` fuel delta % |
| Unified system integration | Flask app + React frontend | End-to-end demo |
| Evaluate against historical datasets | `ml/routing/benchmarks/` + NLP corpus | Benchmark CSV + evaluation JSON |

---

## 9. Academic Defensibility Rules

These are real constraints. Break them and your examiner will flag them.

1. **Data privacy:** The system must only use synthetic or publicly available data. Never commit real crime records. The `ml/data/raw/` folder is gitignored for this reason.

2. **Gemini API privacy note:** In your dissertation methodology, you MUST acknowledge that using an external LLM API means incident text leaves your system. Propose a self-hosted model as future work.

3. **Algorithm honesty:** Do not claim Dijkstra "optimizes" patrol routes in the TSP sense — it finds shortest paths between nodes. Your nearest-neighbor tour using Dijkstra is a heuristic. Name it correctly.

4. **GA reproducibility:** The GA uses `random.seed(42)`. This is intentional. Without a fixed seed, you get different results every run, which makes dissertation results non-reproducible. Document this.

5. **Performance claims:** Your dissertation claims ≥15% fuel reduction. This claim must come from actual benchmark data, not from theory. Run `compare_algorithms()` across all 4 scenarios and use the average.

---

## 10. Common Errors and Their Fixes

Keep this section updated as you encounter issues.

```bash
# PostGIS not installed in DB
docker-compose down -v && docker-compose up db -d
# The init_db.sql runs automatically on first start

# GeoAlchemy2 import error
pip install GeoAlchemy2==0.15.1
# Requires libgdal-dev system package (see Dockerfile.backend)

# Gemini quota exceeded during testing
# Set GEMINI_API_KEY= empty → triggers keyword fallback automatically

# DBSCAN finds 0 clusters
# epsilon too small OR not enough incidents
# Run: python scripts/seed_harare_data.py first

# GA DEAP creator conflict in pytest
# DEAP registers global creators — use if not hasattr(creator, "FitnessMin") guard
# Already handled in genetic_solver.py

# Flask-Migrate can't find models
# Ensure models.py is imported in app/__init__.py before db.init_app(app)
```

---

## 11. Out of Scope (Do Not Build)

- Real-time WebSocket push notifications
- Mobile app (React web is sufficient for dissertation)
- Facial recognition or biometric integration
- Integration with real ZRP internal systems
- Automated dispatch (system is a DSS, not autonomous)
- Multi-city deployment infrastructure
- Payment processing of any kind

---

## 12. Skills You Are Building

For each phase you complete, you are practicing:

| Phase | Skill |
|---|---|
| Auth + DB | REST API design, JWT auth, relational database modeling, migrations |
| NLP | Prompt engineering, API integration, fault-tolerant JSON parsing |
| GIS | Spatial data, DBSCAN clustering, KDE, coordinate systems |
| Routing | Graph theory, evolutionary algorithms, benchmarking methodology |
| Frontend | React component design, API integration, map rendering |
| Benchmarking | Scientific method applied to software: controlled tests, metrics |
| Testing | Unit vs integration testing, mocking, test-driven thinking |

These are real senior engineering skills. Employers and examiners will respect them.
