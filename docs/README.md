# Crime-Watch

**AI-driven spatiotemporal crime analytics and patrol optimization system**

A Decision Support System (DSS) for the Zimbabwe Republic Police that transforms community-sourced incident reports into actionable patrol intelligence using Natural Language Processing, spatial clustering, and comparative route optimization algorithms.

> **Academic Context:** BSc Computer Science Dissertation — Midlands State University  
> **Authors:** Benhail Moyo (R2312487F) & Oslea Mukuhlani (R252775F)

---

## What It Does

Crime-Watch addresses three concrete operational problems facing urban law enforcement in resource-constrained environments:

**1. Report Triage**  
Officers receive unstructured incident reports in English, Shona, and Ndebele. The NLP module classifies each report by severity (HIGH/MEDIUM/LOW) and category, using Google Gemini 1.5 Flash with a keyword-based fallback, enabling immediate priority dispatch decisions.

**2. Crime Hotspot Mapping**  
Historical incidents are clustered using DBSCAN to identify crime concentration zones. KDE (Kernel Density Estimation) generates a continuous heatmap surface. Both are rendered on an interactive Leaflet.js map overlaid on Harare.

**3. Patrol Route Optimization**  
Given a set of identified hotspots, the system generates patrol routes using two algorithms and compares them directly:
- **Dijkstra's Algorithm** — greedy nearest-neighbor heuristic baseline (deterministic, ~2ms)
- **Genetic Algorithm** — stochastic multi-objective optimizer (~150ms, targets both distance and hotspot risk coverage)

The output is a side-by-side comparison of fuel consumption, estimated time, distance, and computation speed — enabling data-led resource allocation decisions.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                          │
│  Crime Map (Leaflet.js) │ Dashboard │ Reports │ Patrol Compare  │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (JSON)
┌────────────────────────────┴────────────────────────────────────┐
│                        Flask REST API                           │
│  /auth  │  /incidents  │  /hotspots  │  /patrol                │
├──────────────────────────────────────────────────────────────────┤
│  NLP Service         │  GIS Service       │  Routing Engine     │
│  Gemini 1.5 Flash    │  DBSCAN + KDE      │  Dijkstra + GA      │
│  Shona/Ndebele dict  │  Risk scoring      │  DEAP framework     │
│  Keyword fallback    │  PostGIS queries   │  Haversine distance │
├──────────────────────────────────────────────────────────────────┤
│                    PostgreSQL + PostGIS                         │
│         Incident │ Hotspot │ PatrolRoute │ User                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.x (app factory pattern) |
| Database | PostgreSQL 15 + PostGIS 3.4 via GeoAlchemy2 |
| NLP/AI | Google Gemini 1.5 Flash API |
| Clustering | scikit-learn DBSCAN, scipy KDE |
| Routing | NetworkX (Dijkstra), DEAP (Genetic Algorithm) |
| Auth | JWT via Flask-JWT-Extended |
| Frontend | React 18, Leaflet.js via react-leaflet, recharts |
| Containers | Docker + Docker Compose |
| Testing | pytest, pytest-flask, unittest.mock |

---

## Quick Start

**Prerequisites:** Docker Desktop, Python 3.11+, Node.js 20+

```bash
# 1. Clone and configure
git clone https://github.com/yourusername/crime-watch.git
cd crime-watch
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY from https://aistudio.google.com/

# 2. Start PostGIS database
docker-compose up db -d

# 3. Set up backend
cd backend
pip install -r requirements.txt
flask db upgrade
python scripts/seed_harare_incidents.py  # Loads synthetic Harare crime data

# 4. Start API server
flask run
# → http://localhost:5000

# 5. Start frontend (separate terminal)
cd ../frontend
npm install
npm start
# → http://localhost:3000
```

**Default credentials after seeding:**
```
Admin:     admin@crimewatch.zw     / Admin1234!
Officer:   officer@crimewatch.zw   / Officer1234!
Community: community@crimewatch.zw / Community1234!
```

---

## API Reference

All protected endpoints require `Authorization: Bearer <token>` header.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Public | Register user |
| POST | `/api/v1/auth/login` | Public | Login → JWT |
| POST | `/api/v1/incidents/` | Any | Submit + triage incident report |
| GET | `/api/v1/incidents/` | Any | List incidents |
| GET | `/api/v1/incidents/stats` | Any | Incident counts by severity |
| POST | `/api/v1/hotspots/analyze` | Officer+ | Run DBSCAN clustering |
| GET | `/api/v1/hotspots/` | Any | List hotspot polygons |
| GET | `/api/v1/hotspots/heatmap` | Any | KDE heatmap grid |
| POST | `/api/v1/patrol/optimize` | Officer+ | Generate patrol route |
| **POST** | **`/api/v1/patrol/compare`** | **Officer+** | **Compare Dijkstra vs GA** |
| GET | `/health` | Public | Health check |

---

## Running Academic Evaluations

```bash
# Routing algorithm benchmark (generates Chapter 4 comparison table)
python -m ml.routing.benchmarks.run_benchmarks
# Output: ml/routing/benchmarks/results/benchmark_results.csv

# NLP triage accuracy evaluation (requires labeled corpus)
# First build: ml/nlp/corpus/labeled_test_set.json (see corpus/README.md)
python -m ml.nlp.evaluations.evaluate_triage
# Output: ml/nlp/evaluations/evaluation_report.json

# Backend test suite
cd backend && pytest --cov=app --cov-report=term-missing
```

---

## Key Design Decisions

**Why two routing algorithms?**  
The academic contribution is the comparative analysis. Dijkstra provides a deterministic shortest-path baseline in O(n²). The Genetic Algorithm explores a larger solution space and optimizes for both distance and weighted hotspot coverage simultaneously. The tradeoff — better routes at higher computational cost — is the dissertation finding.

**Why Gemini 1.5 Flash for NLP?**  
Training a custom NLP model requires thousands of labeled Zimbabwean crime reports in Shona/Ndebele — data that doesn't publicly exist. Using Gemini as an LLM backbone is an academically defensible proof-of-concept approach. The keyword fallback ensures system operation when the API is unavailable.

**Why DBSCAN over K-Means?**  
K-Means requires pre-specifying the number of clusters k. In crime analysis, the number of hotspots is unknown and variable. DBSCAN discovers clusters based on density, handles arbitrary shapes, and naturally identifies outliers (isolated incidents that don't form patterns).

**Why PostGIS?**  
Spatial operations — bounding box queries, distance calculations, polygon intersection — are far more efficient in a spatial database than in application code. GeoAlchemy2 provides a clean ORM layer over PostGIS geometry columns.

---

## Dissertation Objective Traceability

| Objective | Implementation | Measurement |
|---|---|---|
| NLP triage ≥75% accuracy | `services/nlp/triage.py` | `evaluate_triage.py` → accuracy score |
| GIS hotspot mapping | `services/gis/hotspot_analysis.py` + Leaflet | Map screenshot + hotspot count |
| Patrol optimization ≥15% fuel reduction | `services/routing/route_engine.py` | `run_benchmarks.py` → fuel delta CSV |
| Unified system integration | Flask app + React SPA | End-to-end demo video |

---

## Limitations

- **Data:** System uses synthetic and publicly available data only. Real ZRP data was unavailable due to operational security constraints.
- **Translation:** Shona/Ndebele reports are processed via prompt annotation to Gemini rather than full translation, which may reduce accuracy for fully non-English reports.
- **Connectivity:** Real-time features require internet for Gemini API access. Keyword fallback handles offline operation.
- **Scale:** Proof-of-concept calibrated for Harare urban area. Multi-city deployment would require infrastructure changes.

---

## Future Work

- Self-hosted LLM to eliminate external API dependency and address data sovereignty concerns
- Full Shona/Ndebele translation pipeline using a localized model
- Mobile app for community incident reporting (React Native)
- Real-time WebSocket updates for new incidents
- Integration with ZRP internal dispatch systems (subject to data sharing agreements)

---

## References

1. I. Mugari & T. Chakanyuka, "Intelligence-led policing in Zimbabwe," *JACPR*, 2024
2. M. Alikhademi et al., "A Review of Predictive Policing from Data Science and Ethics Perspectives," *IEEE Access*, 2022
3. Government of Zimbabwe, *Cyber and Data Protection Act [Chapter 12:07]*, 2021
4. Government of Zimbabwe, *Vision 2030*, 2018

---

## License

This project is submitted in partial fulfilment of the requirements for BSc Honours in Computer Science at Midlands State University. All code is original work by the listed authors. Dataset used is synthetic/publicly available and contains no personal identifying information.
