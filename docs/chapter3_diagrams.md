# Chapter 3 Methodology Diagrams

## 3.3 Proposed System Architecture

**Figure 3.1: Crime-Watch Four-Tier System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM BOUNDARY (Dashed)                                     │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                    PRESENTATION TIER                                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │ React.js     │  │ Leaflet.js  │  │ Command      │  │ Triage Queue │        │ │
│  │  │ Client       │  │ Map Renderer │  │ Dashboard    │  │ UI           │        │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                        │ HTTPS/JSON                                  │
│                                        ↓                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │              APPLICATION/MIDDLEWARE TIER                                        │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │ │
│  │  │                  Flask REST Gateway                                    │    │ │
│  │  │  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │ │
│  │  │  │ JWT/     │  │ Input        │  │ Rate         │  │ Request      │  │    │ │
│  │  │  │ Flask-   │  │ Sanitization │  │ Limiting     │  │ Routing      │  │    │ │
│  │  │  │ Login    │  │              │  │              │  │              │  │    │ │
│  │  │  └──────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │    │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                        │ REST                                        │
│                                        ↓                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │              INTELLIGENCE & ANALYTICS TIER                                     │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐            │ │
│  │  │ LLM NLP Triage   │  │ Spatio-Temporal   │  │ Patrol            │            │ │
│  │  │ Parser           │  │ Hotspot Engine    │  │ Optimization      │            │ │
│  │  │                  │  │ (DBSCAN/KDE)      │  │ Engine            │            │ │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘            │ │
│  │         │                                           │                           │ │
│  │         └───────────────────────────────────────────┘                           │ │
│  │                                            │                                    │ │
│  │                                            ↓ HTTPS/JSON                         │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ↓ HTTPS/JSON
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL CLOUD SERVICE (Outside System Boundary)                 │
│  ┌──────────────────┐                                                               │
│  │  Gemini 1.5      │                                                               │
│  │  Flash API       │                                                               │
│  │  (Third-Party)   │                                                               │
│  └──────────────────┘                                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM BOUNDARY (Dashed)                                     │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │                         DATA TIER                                              │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │              PostgreSQL / PostGIS                                         │  │ │
│  │  │  ┌──────────────────────────────────────────────────────────────────┐   │  │ │
│  │  │  │ Relational Tables                                                 │   │  │ │
│  │  │  │  • users                                                          │   │  │ │
│  │  │  │  • dockets                                                        │   │  │ │
│  │  │  │  • triaged_reports                                                │   │  │ │
│  │  │  └──────────────────────────────────────────────────────────────────┘   │  │ │
│  │  │  ┌──────────────────────────────────────────────────────────────────┐   │  │ │
│  │  │  │ Spatial Vector Tables (PostGIS)                                   │   │  │ │
│  │  │  │  • road_network (LINESTRING)                                      │   │  │ │
│  │  │  │  • point_geometries (POINT)                                       │   │  │ │
│  │  │  │  • polygon_boundaries (POLYGON)                                   │   │  │ │
│  │  │  │  • [R-Tree / GIST Spatial Index]                                  │   │  │ │
│  │  │  └──────────────────────────────────────────────────────────────────┘   │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**QA checklist:**
- [ ] All 4 tiers present in correct top-to-bottom order
- [ ] Gemini API shown as external, outside system trust boundary
- [ ] Every arrow labelled with protocol

---

## 3.4.1 Process Analysis, Data Collection, and Preprocessing

**Figure 3.2: Crime-Watch Operational Activity Diagram (Swimlane)**

```
┌──────────────────┬──────────────────────────────────┬────────────────────────────┐
│ Community/Duty   │           System                  │      Station Commander     │
│     Officer       │                                  │                            │
├──────────────────┼──────────────────────────────────┼────────────────────────────┤
│                  │                                  │                            │
│  Incident Data   │                                  │                            │
│  Ingestion       │                                  │                            │
│  (public submit  │                                  │                            │
│   OR digitized   │                                  │                            │
│   OB entry)      │                                  │                            │
│       │          │                                  │                            │
│       └─────────→│                                  │                            │
│                  │  Text Pre-Filtering &            │                            │
│                  │  LLM Parsing                     │                            │
│                  │       │                          │                            │
│                  │       ↓                          │                            │
│                  │  Spatial Geocoding &             │                            │
│                  │  DB Storage                      │                            │
│                  │       │                          │                            │
│                  │       ↓                          │                            │
│                  │  Density Hotspot                 │                            │
│                  │  Generation                      │                            │
│                  │       │                          │                            │
│                  │       ↓                          │                            │
│                  │  Patrol Route                    │                            │
│                  │  Generation                      │                            │
│                  │       │                          │                            │
│                  │       └─────────────────────────→│                            │
│                  │                                  │  Human-in-the-Loop         │
│                  │                                  │  Review                    │
│                  │                                  │       │                    │
│                  │                                  │       ↓                    │
│                  │                                  │  ◇ Decision                │
│                  │                                  │       │                    │
│                  │     Approve ←────────────────────┤  Approve / Modify / Reject │
│                  │       │                          │       │                    │
│                  │       ↓                          │   ┌───┴───┬───┐            │
│                  │  Plan Executed as-is             │   │       │   │            │
│                  │                                  │   ↓       ↓   ↓            │
│                  │                                  │ Modify  Reject             │
│                  │       ←──────────────────────────┤   │       │                │
│                  │                                  │   │       ↓                │
│                  │  Modified Plan                   │   │  Plan Discarded         │
│                  │  Executed                        │   │  Commander Logs         │
│                  │                                  │   │  Rationale              │
│                  │                                  │   └───────┘                │
│                  │                                  │                            │
└──────────────────┴──────────────────────────────────┴────────────────────────────┘
```

**QA checklist:**
- [ ] 3 distinct swimlanes present
- [ ] Decision diamond with 3 explicit branches (Approve/Modify/Reject)
- [ ] Modify branch loops back, does not dead-end

---

## 3.4.3 Data Preprocessing and Feature Engineering Pipelines

**Figure 3.3: Text Normalization and Fallback-Resilient Triage Pipeline**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         DATA PREPROCESSING PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘

                    Raw Text Input
                            │
                            ↓
              ┌───────────────────────────┐
              │  Normalize                │
              │  • lowercase              │
              │  • strip non-printable    │
              │  • collapse whitespace    │
              │  • strip JSON-breaking    │
              └───────────────────────────┘
                            │
                            ↓
              ┌───────────────────────────┐
              │  Regex Pre-Filter         │
              │  Scan for priority        │
              │  keywords:                │
              │  "firearm", "knife",      │
              │  "assault", "armed        │
              │  robbery", "break-in"     │
              └───────────────────────────┘
                            │
                            ↓
                    ◇ Gemini API
                    ◇ reachable?
                     │     │
                    YES   NO
                     │     │
                     │     ↓
                     │  ┌───────────────────────────┐
                     │  │  Fallback:                │
                     │  │  regex-derived            │
                     │  │  classification only       │
                     │  │  (degraded but resilient) │
                     │  └───────────────────────────┘
                     │     │
                     └─────┘
                           │
                           ↓
         ┌───────────────────────────────────┐
         │  Gemini 1.5 Flash structured      │
         │  JSON extraction:                 │
         │  • crime_category                │
         │  • priority_score                │
         │  • extracted_location            │
         │  • confidence_score              │
         └───────────────────────────────────┘
                           │
                           ↓
         ┌───────────────────────────────────┐
         │  Geocode extracted_location      │
         │  against PostGIS gazetteer       │
         └───────────────────────────────────┘
                           │
                           ↓
                    ◇ coordinates
                    ◇ resolved?
                     │     │
                    YES   NO
                     │     │
                     │     ↓
                     │  ┌───────────────────────────┐
                     │  │  Impute centroid of       │
                     │  │  matched administrative   │
                     │  │  suburb                   │
                     │  └───────────────────────────┘
                     │     │
                     └─────┘
                           │
                           ↓
         ┌───────────────────────────────────┐
         │  Persist to spatial crime table   │
         └───────────────────────────────────┘
```

**QA checklist:**
- [ ] Both decision diamonds present (API reachability, coordinate resolution)
- [ ] Fallback path is a genuine parallel branch, not a dead-end note
- [ ] Ends at persistence step, matching 3.4.1's "Spatial Geocoding and Database Storage" stage

---

## 3.5.1 Automated NLP Triage Engine

**Figure 3.4: Urgency Index Computation Pipeline**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        URGENCY INDEX U(t) COMPUTATION                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

                    Input Text
                        │
                        ↓
         ┌───────────────────────────┐
         │  Regex Check              │
         │  (see Fig 3.3)            │
         └───────────────────────────┘
                        │
                        ↓
         ┌───────────────────────────┐
         │  Gemini Severity Score S  │
         │  extracted from LLM       │
         └───────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │ Temporal         │    │ Normalized       │    │ Gemini Severity  │      │
│  │ Recency Decay    │    │ Spatial Density  │    │ Score S           │      │
│  │ Factor           │    │ Metric ρ        │    │                    │      │
│  │ (using Δt hours  │    │ (from hotspot    │    │                    │      │
│  │  and decay       │    │  engine)         │    │                    │      │
│  │  parameter)      │    │                  │    │                    │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│           │                      │                      │                   │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  ↓                                          │
│                    ┌──────────────────────────┐                               │
│                    │  Weighted Summation     │                               │
│                    │  U(t) = w₁·S + w₂·decay │                               │
│                    │        + w₃·ρ           │                               │
│                    └──────────────────────────┘                               │
│                                  │                                            │
│                                  ↓                                            │
│                    ┌──────────────────────────┐                               │
│                    │  Urgency Index U(t)      │                               │
│                    │  (output)                │                               │
│                    └──────────────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────┘

Weighting Coefficients:
  w₁ = severity weight
  w₂ = temporal decay weight
  w₃ = spatial density weight
```

**QA checklist:**
- [ ] All three inputs (severity, decay, spatial density) shown as separate incoming arrows
- [ ] Weighting coefficients labelled, not silently omitted
- [ ] Single output: Urgency Index

---

## 3.5.2 Geospatial Hotspot Clustering Engine

**Figure 3.5: DBSCAN Core/Border/Noise Point Classification within ε-Radius**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                  DBSCAN ε-NEIGHBORHOOD CLASSIFICATION                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

                              ε = 0.008
                              MinPts = 4

                       •  •       •        •
                     •   •     •   •      •
                   •     •   •     •    •
                 •       ◉────────•──•
               •         │ ●    ● │  •
             •           │ ●  ● ● │   •
           •             │   ●    │    •
         •               │        │      •
       •                 │   ○    │        •
     •                   └────────┘          •
   •                                          •
 •                                             •
•         Noise Point (isolated)               •

Legend:
  ◉ = Core Point (≥ MinPts neighbors within ε)
  ● = Points within ε-radius of core point
  ○ = Border Point (inside core's ε-radius but < MinPts neighbors of its own)
  • = Other points

ε-radius shown as diamond bracket around core point
```

// NOTE: ε and MinPts values below are not yet empirically derived — flag for k-distance plot before defense.

**QA checklist:**
- [ ] Core, border, and noise points all present and visually distinguishable
- [ ] ε and MinPts labelled with actual configured values from the text
- [ ] Empirical-justification flag included if applicable

---

## 3.5.3 Dynamically Weighted Dijkstra Graph Routing Model

**Figure 3.6: Dynamic-Weight Dijkstra Pathfinding Algorithm**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    DYNAMIC-WEIGHT DIJKSTRA ALGORITHM                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────┐
│  1. Initialize                                                                      │
│     dist[source] = 0                                                               │
│     dist[all others] = ∞                                                            │
│     parent[all] = null                                                              │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  2. Insert all nodes into min-priority queue Q ordered by dist[]                   │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  3. [Loop] Extract node u with minimum dist[u] from Q                              │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  4. For each neighbor v of u via edge (u,v):                                       │
│        compute dynamic weight w(u,v,t)                                             │
│        candidate = dist[u] + w(u,v,t)                                               │
│        ◇ candidate < dist[v]?                                                      │
│           YES → dist[v] = candidate; parent[v] = u; update position in Q         │
│           NO  → no update                                                          │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  5. ◇ target reached OR Q empty?                                                   │
│        NO  → loop back to step 3 "Extract node u"                                  │
│        YES → Reconstruct path via parent[] pointers, source → target               │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**QA checklist:**
- [ ] All 4 algorithmic steps from prose represented as distinct flowchart blocks
- [ ] Relaxation decision diamond present
- [ ] Loop-back arrow to extraction step shown explicitly
- [ ] Path reconstruction shown as final step, not implied

---

## 3.5.4 Multi-Objective Genetic Algorithm (MOGA) Fleet Optimization

**Figure 3.7: Chromosome Encoding of a Candidate Patrol Route**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    CHROMOSOME ENCODING (Permutation Vector)                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌──────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌──────────┐
│  Origin  │ → │ Hotspot_3 │ → │ Hotspot_7 │ → │ Hotspot_1 │ → │ Hotspot_5 │ → │  Origin  │
└──────────┘   └───────────┘   └───────────┘   └───────────┘   └───────────┘   └──────────┘

Path segments between consecutive nodes computed via Dynamic-Weight Dijkstra (Figure 3.6)
```

**QA checklist:**
- [ ] Origin appears at both start and end (round-trip route)
- [ ] Cross-reference to Figure 3.6 included
- [ ] At least 3 intermediate hotspot nodes shown

---

**Figure 3.8: MOGA Generational Optimization Cycle**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                       MOGA GENERATIONAL CYCLE                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────┐
│  Initialize Population (random candidate routes)                                     │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  Evaluate Fitness F(R) — Pareto rank + crowding distance                          │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  Binary Tournament Selection (Pareto dominance)                                      │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  Order Crossover (OX), probability p_c                                              │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  Swap Mutation, probability p_m                                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  Elitism: top 5% Pareto-optimal carried forward unmodified                         │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  ◇ termination criterion met? (e.g. max generations)                              │
│        NO  → loop back to "Evaluate Fitness"                                       │
│        YES → Output Pareto-optimal route set                                        │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**QA checklist:**
- [ ] All 4 genetic operators named in prose appear as distinct blocks (Selection, Crossover, Mutation, Elitism)
- [ ] Elitism percentage matches prose value
- [ ] Loop-back arrow present, terminates only on explicit condition

---

## 3.6.1 Software Component Integration and API Code Implementation

**Figure 3.9: Sequence Diagram — NLP Triage API Call with Fallback**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                 NLP TRIAGE API CALL WITH FALLBACK SEQUENCE                          │
└─────────────────────────────────────────────────────────────────────────────────────┘

Client          Flask Middleware        Gemini API           fallback_regex_triage()
  │                  │                     │                        │
  │ raw_report_text  │                     │                        │
  │─────────────────>│                     │                        │
  │                  │                     │                        │
  │                  │ generate_content()  │                        │
  │                  │────────────────────>│                        │
  │                  │                     │                        │
  │                  │   [alt: success]    │                        │
  │                  │<────────────────────│                        │
  │                  │ parsed JSON         │                        │
  │<─────────────────│                     │                        │
  │                  │                     │                        │
  │                  │   [alt: exception]  │                        │
  │                  │────────────────────────────────────────────>│
  │                  │                     │     fallback result   │
  │                  │<────────────────────────────────────────────│
  │<─────────────────│                     │                        │
  │                  │                     │                        │
```

**QA checklist:**
- [ ] 4 lifelines present, correctly labelled
- [ ] alt/exception framing matches the actual code's try/except structure
- [ ] Both return paths (success JSON, fallback result) terminate back at Client

---

## 3.6.2 Spatial Graph Network Topology Design

**Figure 3.10: `network_nodes` / `network_edges` Relational-Spatial Schema**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│              SPATIAL GRAPH NETWORK SCHEMA (PostGIS)                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐         ┌──────────────────────────────┐
│      network_nodes      │         │        network_edges          │
├─────────────────────────┤         ├──────────────────────────────│
│ node_id (PK)            │◄───┐    │ segment_id (PK)                │
│ geometry (POINT)        │    │    │ source_node_id (FK)            │
│ elevation_marker        │    ├────┤ target_node_id (FK)            │
│ admin_zone_tag          │    │    │ geometry (LINESTRING)          │
│ [GIST/R-Tree index]     │    │    │ length_m                       │
└─────────────────────────┘    │    │ speed_limit_kmh                │
                                │    │ turn_penalty                   │
                                │    │ crime_density_score (ρ input) │
                                │    │ [GIST/R-Tree index]            │
                                │    └──────────────────────────────│
                                │
                                └─── 1-to-many (source & target FKs) ─┘

Note: crime_density_score (ρ) is input to Dijkstra weight formula w(u,v,t) — see Figure 3.6
```

**QA checklist:**
- [ ] Both FK relationships (source_node_id, target_node_id) shown pointing to network_nodes
- [ ] R-Tree/GIST index noted on both geometry columns
- [ ] crime_density_score field present (this is the ρ input to the Dijkstra weight formula — cross-reference Figure 3.6)

---

## 3.6.3 Human-in-the-Loop Decision Support Workflow

**Figure 3.11: HITL Approval and Immutable Audit Workflow**

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    HUMAN-IN-THE-LOOP APPROVAL WORKFLOW                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────┐
│  System (NLP triage + MOGA optimizer)                                              │
│       │                                                                            │
│       ↓ proposes deployment plan                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│  Station Commander                                                                  │
│       │                                                                            │
│       ↓ reviews                                                                    │
│       │                                                                            │
│       ├── Approve ───────────────────────────────────────────────────────────►     │
│       │      Plan executed as-is                                                  │
│       │                                                                            │
│       ├── Modify (adjust priority / insert waypoint / reassign vehicle) ─────►     │
│       │      Modified plan executed                                               │
│       │                                                                            │
│       └── Override/Reject ───────────────────────────────────────────────────►     │
│              Plan discarded, commander logs rationale                              │
│       │                                                                            │
└───────┴────────────────────────────────────────────────────────────────────────────┘
        │
        ↓ (all three branches converge here)
┌───────────────────────────────────────────────────────────────────────────────────┐
│  Immutable PostGIS Audit Table                                                    │
│  • logs: original recommendation                                                   │
│  •        human action taken                                                       │
│  •        commander ID                                                             │
│  •        timestamp                                                                │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**QA checklist:**
- [ ] All three commander actions (Approve/Modify/Override) shown as distinct branches
- [ ] All three branches converge on the audit table, not just Override
- [ ] Audit table fields listed (recommendation, action, commander ID, timestamp)

---

## Figure Numbering & Placement Summary

| Figure | Section | Diagram |
|---|---|---|
| 3.1 | 3.3 | System Architecture Diagram |
| 3.2 | 3.4.1 | Main Operational Activity Diagram (swimlane) |
| 3.3 | 3.4.3 | Data Preprocessing Pipeline Flowchart |
| 3.4 | 3.5.1 | NLP Priority Scoring Flowchart |
| 3.5 | 3.5.2 | DBSCAN ε-Neighborhood Conceptual Diagram |
| 3.6 | 3.5.3 | Dynamic-Weight Dijkstra Flowchart |
| 3.7 | 3.5.4 | MOGA Chromosome Encoding |
| 3.8 | 3.5.4 | MOGA Generational Cycle Flowchart |
| 3.9 | 3.6.1 | API Integration Sequence Diagram |
| 3.10 | 3.6.2 | Spatial Graph Network Schema Diagram |
| 3.11 | 3.6.3 | Human-in-the-Loop Workflow Diagram |
