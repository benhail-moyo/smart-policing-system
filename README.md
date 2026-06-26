# Crime-Watch

> AI-driven spatiotemporal crime analytics and patrol optimization platform   
> **Author:** Benhail Moyo

---

## Academic Component Reference

| Dissertation Objective | Module | File |
|---|---|---|
| NLP triage (≥75% accuracy) | NLP Service | `backend/app/services/nlp/triage.py` |
| Language support (Shona/Ndebele) | Language Utils | `backend/app/services/nlp/language_utils.py` |
| GIS hotspot mapping (DBSCAN/KDE) | GIS Service | `backend/app/services/gis/hotspot_analysis.py` |
| Dijkstra patrol routing | Dijkstra Solver | `backend/app/services/routing/dijkstra_solver.py` |
| Genetic Algorithm routing | GA Solver | `backend/app/services/routing/genetic_solver.py` |
| Algorithm comparison (Chapter 4) | Route Engine | `backend/app/services/routing/route_engine.py` |
| Benchmark results generator | Benchmarks | `ml/routing/benchmarks/run_benchmarks.py` |
| NLP accuracy evaluator | Evaluator | `ml/nlp/evaluations/evaluate_triage.py` |

---

## Architecture

```
crime-watch/
├── backend/                    # Flask REST API
│   ├── app/
│   │   ├── api/v1/routes/      # Endpoints: incidents, hotspots, patrol, auth
│   │   ├── models/             # SQLAlchemy + PostGIS models
│   │   ├── services/
│   │   │   ├── nlp/            # Gemini triage + language detection
│   │   │   ├── gis/            # DBSCAN clustering + KDE heatmaps
│   │   │   └── routing/        # Dijkstra + Genetic Algorithm solvers
│   │   └── config/             # Dev/test/prod configuration
│   └── requirements.txt
├── frontend/                   # React dashboard
│   └── src/
│       ├── components/map/     # Leaflet.js crime map
│       ├── components/dashboard/
│       └── components/reports/ # Incident submission
├── ml/                         # Standalone ML scripts (academic benchmarking)
│   ├── nlp/corpus/             # Mock incident reports (200+ for evaluation)
│   ├── nlp/evaluations/        # NLP accuracy evaluation
│   └── routing/benchmarks/     # Algorithm comparison runner
└── infra/docker/               # Docker Compose + PostGIS setup
```

---

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY

# 2. Start infrastructure
docker-compose up db -d
# Wait for PostGIS to be healthy

# 3. Run backend
cd backend
pip install -r requirements.txt
flask db upgrade
flask run

# 4. Run frontend
cd frontend
npm install
npm start
```

---

## Running Academic Benchmarks

```bash
# Routing algorithm comparison (generates Chapter 4 results)
python -m ml.routing.benchmarks.run_benchmarks

# NLP triage accuracy evaluation
# First: populate ml/nlp/corpus/labeled_test_set.json (see corpus/README.md)
python -m ml.nlp.evaluations.evaluate_triage
```

---

## Key Design Decisions

**Why Dijkstra AND Genetic Algorithm?**  
The dissertation's academic contribution is a comparative analysis. Dijkstra is deterministic and fast (baseline). GA is stochastic and slower but can optimize for multiple objectives (distance + hotspot risk weighting). The tradeoff is the finding.

**Why Gemini 1.5 Flash for NLP?**  
Developing a custom NLP model requires thousands of labeled Zimbabwean crime reports — data that doesn't exist publicly. Using Gemini as the LLM backbone is academically defensible as a proof-of-concept, and is explicitly cited in Section 1.7 (Delimitations) of the dissertation.

**Why PostGIS?**  
All crime clustering (DBSCAN), heatmap generation (KDE), and route storage require spatial queries. PostGIS + GeoAlchemy2 handles this natively, avoiding manual coordinate math in application code.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login → JWT token |
| POST | `/api/v1/incidents/` | Submit + triage a crime report |
| GET | `/api/v1/incidents/` | List incidents |
| POST | `/api/v1/hotspots/analyze` | Run DBSCAN clustering |
| GET | `/api/v1/hotspots/heatmap` | Get KDE heatmap data |
| POST | `/api/v1/patrol/optimize` | Generate patrol route |
| POST | `/api/v1/patrol/compare` | **Dissertation results**: compare both algorithms |

---


