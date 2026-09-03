# Agent Task: Generate ASCII Diagrams for Crime-Watch Chapter 3

## Context

You are producing **ASCII-art diagrams** for Chapter 3 (Methodology) of a BSc dissertation titled
*"Crime-Watch: An AI-Driven Spatiotemporal Analytics and Patrol Optimization Decision Support System"*
(Midlands State University, HCSE438/HCSCI438).

The university's Level 4 Hardware/ML Guide requires Chapter 3 to include: **system architecture,
activity diagrams, flow chart diagrams, algorithm design (pseudocode/flowcharts), and circuit/model
design diagrams.** For this software-only project, "circuit design" is reinterpreted as
**software component, sequence, and schema design** — this reinterpretation should be footnoted in
the dissertation, not hidden.

Each diagram must:
- Be placed in the **exact subsection** listed below (do not consolidate or reorder them)
- Be numbered `Figure 3.X` following the chapter-numbering convention (chapter number, then
  sequential count within the chapter)
- Include a **caption below the diagram** (MSU guide: figure captions go at the bottom, table
  captions go at the top — do not mix this up)
- Be drawn using **box-drawing / ASCII characters** (`┌─┐│└─┘├┤┬┴┼→←↑↓▶` or plain `+-|>` if the
  target renderer doesn't support box-drawing glyphs — ask which before starting, default to
  box-drawing)
- Be legible in a monospace font at ~100 columns wide; wrap or split into multiple linked panels
  rather than shrinking labels illegibly
- Use **only the terminology, variable names, and parameters already defined in Chapter 3's prose**
  (e.g. use `ε`, `MinPts`, `U(t)`, `w(u,v,t)`, `F(R)` exactly as named in the text) — do not invent
  new symbols
- Where a diagram would visually expose an unresolved inconsistency between documentation and
  implementation (see **Flag list** at the end), draw the diagram to match **what Chapter 3
  documents**, and separately output a one-line inline comment noting the mismatch — do not
  silently "fix" the diagram to match undocumented code behaviour, and do not silently hide the
  mismatch either.

Output each diagram as its own fenced code block, immediately preceded by its section heading and
figure number, and immediately followed by its caption line and a 2-4 line "what this diagram must
show" checklist so I can QA it against the text.

---

## Diagram 1 — System Architecture Diagram

**Section:** 3.3 Proposed System Architecture
**Figure:** 3.1
**Caption:** *Figure 3.1: Crime-Watch Four-Tier System Architecture*

Draw four horizontal tiers, top to bottom, with labelled arrows between them showing protocol/payload:

1. **Presentation Tier** — React.js client, Leaflet.js map rendering, command dashboard, triage queue UI
2. **Application/Middleware Tier** — Flask REST Gateway: JWT/Flask-Login auth, input sanitization, rate limiting, request routing
3. **Intelligence & Analytics Tier** — three parallel sub-boxes side by side:
   - LLM NLP Triage Parser (calls out to Gemini 1.5 Flash API — **draw this as an external box
     outside the system boundary**, connected by a dashed arrow to signal it's a third-party
     cloud dependency, not internal infrastructure)
   - Spatio-Temporal Hotspot Engine (DBSCAN/KDE)
   - Patrol Optimization Engine (Dynamic Dijkstra + MOGA)
4. **Data Tier** — PostgreSQL/PostGIS: relational tables (users, dockets, triaged reports) + spatial
   vector tables (road network, point geometries, polygon boundaries) with R-Tree indexing noted

Label every inter-tier arrow with its protocol: `HTTPS/JSON`, `SQL`, `REST`. Draw a **dashed box
enclosing tiers 1-4** representing the system's own infrastructure boundary, with the Gemini API
box explicitly sitting outside it.

**QA checklist:**
- [ ] All 4 tiers present in correct top-to-bottom order
- [ ] Gemini API shown as external, outside system trust boundary
- [ ] Every arrow labelled with protocol

---

## Diagram 2 — Main Operational Activity Diagram

**Section:** 3.4 Process Analysis, Data Collection, and Preprocessing (3.4.1)
**Figure:** 3.2
**Caption:** *Figure 3.2: Crime-Watch Operational Activity Diagram (Swimlane)*

Draw a **3-swimlane UML-style activity diagram** (lanes side by side, activity flows downward
across lanes as control passes):

- **Lane 1: Community/Duty Officer** — Incident Data Ingestion (public submission OR digitized OB entry)
- **Lane 2: System** — Text Pre-Filtering & LLM Parsing → Spatial Geocoding & DB Storage → Density
  Hotspot Generation → Patrol Route Generation
- **Lane 3: Station Commander** — Human-in-the-Loop Review → **decision diamond**: Approve / Modify
  / Reject → (loop back to System lane if Modify)

The decision diamond in Lane 3 is the most important element in this diagram — it is the visual
evidence for the dissertation's "not fully autonomous, HITL-enforced" claim (referenced in
Chapter 2's Social Feasibility section). Do not simplify it away.

**QA checklist:**
- [ ] 3 distinct swimlanes present
- [ ] Decision diamond with 3 explicit branches (Approve/Modify/Reject)
- [ ] Modify branch loops back, does not dead-end

---

## Diagram 3 — Data Preprocessing Pipeline Flowchart

**Section:** 3.4.3 Data Preprocessing and Feature Engineering Pipelines
**Figure:** 3.3
**Caption:** *Figure 3.3: Text Normalization and Fallback-Resilient Triage Pipeline*

Linear flowchart with one explicit branch:

```
Raw Text Input
  → Normalize (lowercase, strip non-printable ASCII, collapse whitespace, strip JSON-breaking symbols)
  → Regex Pre-Filter (scan for priority keywords: "firearm", "knife", "assault", "armed robbery", "break-in")
  → [Decision: Gemini API reachable?]
      → YES → Gemini 1.5 Flash structured JSON extraction (crime_category, priority_score,
               extracted_location, confidence_score)
      → NO  → Fallback: regex-derived classification only (degraded but resilient path)
  → Geocode extracted_location against PostGIS gazetteer
  → [Decision: coordinates resolved?]
      → YES → Store lat/lon
      → NO  → Impute centroid of matched administrative suburb
  → Persist to spatial crime table
```

This is the diagram that gives visual backing to the resilience claim in the prose ("providing
immediate fallback classification in high-latency conditions") — the fallback branch must be drawn
as a real, reachable path, not a decorative afterthought.

**QA checklist:**
- [ ] Both decision diamonds present (API reachability, coordinate resolution)
- [ ] Fallback path is a genuine parallel branch, not a dead-end note
- [ ] Ends at persistence step, matching 3.4.1's "Spatial Geocoding and Database Storage" stage

---

## Diagram 4 — NLP Priority Scoring Flowchart

**Section:** 3.5.1 Automated NLP Triage Engine
**Figure:** 3.4
**Caption:** *Figure 3.4: Urgency Index Computation Pipeline*

Flowchart: Input text → regex check (branch as in Diagram 3, can reference "see Fig 3.3" instead of
repeating) → Gemini severity score `S` extracted → combine with:
- temporal recency decay factor (using elapsed hours `Δt` and decay parameter)
- normalized spatial density metric `ρ` (from the hotspot engine)

into weighted sum → **Urgency Index U(t)** output. Show the three weighting coefficients as labelled
inputs feeding into a final summation box. Use the exact weight values from Chapter 3's prose if
present in the source doc; if the weights were left as placeholder variables in the source text,
render them as `w₁, w₂, w₃` and do not invent numeric values.

**QA checklist:**
- [ ] All three inputs (severity, decay, spatial density) shown as separate incoming arrows
- [ ] Weighting coefficients labelled, not silently omitted
- [ ] Single output: Urgency Index

---

## Diagram 5 — DBSCAN ε-Neighborhood Conceptual Diagram

**Section:** 3.5.2 Geospatial Hotspot Clustering Engine
**Figure:** 3.5
**Caption:** *Figure 3.5: DBSCAN Core/Border/Noise Point Classification within ε-Radius*

Draw a **scatter of points** (ASCII dots `•` or `o`) with:
- One point marked as a **core point**, with a circle (approximated in ASCII as a diamond or
  bracketed radius annotation) of radius `ε` drawn around it, and at least `MinPts` neighbor dots
  inside that radius
- One **border point** (inside another core point's ε-radius but with fewer than MinPts neighbors
  of its own)
- One **noise point** (isolated, no core point's radius reaches it)
- Label `ε` and `MinPts` directly on the diagram, using whatever configured values appear in the
  Chapter 3 source text

**Inline flag required:** if the ε/MinPts values in the source text are not accompanied by an
empirical justification (e.g. a k-distance plot) elsewhere in the document, add a one-line comment
after this diagram: `// NOTE: ε and MinPts values below are not yet empirically derived — flag for k-distance plot before defense.`

**QA checklist:**
- [ ] Core, border, and noise points all present and visually distinguishable
- [ ] ε and MinPts labelled with actual configured values from the text
- [ ] Empirical-justification flag included if applicable

---

## Diagram 6 — Dynamic-Weight Dijkstra Flowchart

**Section:** 3.5.3 Dynamically Weighted Dijkstra Graph Routing Model
**Figure:** 3.6
**Caption:** *Figure 3.6: Dynamic-Weight Dijkstra Pathfinding Algorithm*

Flowchart matching the four numbered steps in the prose exactly:

```
Initialize: dist[source] = 0, dist[all others] = ∞, parent[all] = null
Insert all nodes into min-priority queue Q ordered by dist[]
  ↓
[Loop] Extract node u with minimum dist[u] from Q
  ↓
For each neighbor v of u via edge (u,v):
    compute dynamic weight w(u,v,t)
    candidate = dist[u] + w(u,v,t)
    [Decision: candidate < dist[v]?]
        YES → dist[v] = candidate; parent[v] = u; update position in Q
        NO  → no update
  ↓
[Decision: target reached OR Q empty?]
    NO  → loop back to "Extract node u"
    YES → Reconstruct path via parent[] pointers, source → target
```

**QA checklist:**
- [ ] All 4 algorithmic steps from prose represented as distinct flowchart blocks
- [ ] Relaxation decision diamond present
- [ ] Loop-back arrow to extraction step shown explicitly
- [ ] Path reconstruction shown as final step, not implied

---

## Diagram 7a — MOGA Chromosome Encoding

**Section:** 3.5.4 Multi-Objective Genetic Algorithm (MOGA) Fleet Optimization
**Figure:** 3.7
**Caption:** *Figure 3.7: Chromosome Encoding of a Candidate Patrol Route*

Draw a simple sequence of labelled boxes representing a permutation vector, e.g.:

```
┌────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌────────┐
│ Origin │ → │ Hotspot_3 │ → │ Hotspot_7 │ → │ Hotspot_1 │ → │ Origin │
└────────┘   └───────────┘   └───────────┘   └───────────┘   └────────┘
```

Annotate below: "Path segments between consecutive nodes computed via Dynamic-Weight Dijkstra
(Figure 3.6)". Keep this diagram deliberately small and simple — it exists to make the abstract
"variable-length permutation vector" concept concrete for a non-technical committee member.

**QA checklist:**
- [ ] Origin appears at both start and end (round-trip route)
- [ ] Cross-reference to Figure 3.6 included
- [ ] At least 3 intermediate hotspot nodes shown

---

## Diagram 7b — MOGA Generational Cycle Flowchart

**Section:** 3.5.4 Multi-Objective Genetic Algorithm (MOGA) Fleet Optimization
**Figure:** 3.8
**Caption:** *Figure 3.8: MOGA Generational Optimization Cycle*

Circular/looping flowchart:

```
Initialize Population (random candidate routes)
  ↓
Evaluate Fitness F(R) — Pareto rank + crowding distance
  ↓
Binary Tournament Selection (Pareto dominance)
  ↓
Order Crossover (OX), probability p_c
  ↓
Swap Mutation, probability p_m
  ↓
Elitism: top 5% Pareto-optimal carried forward unmodified
  ↓
[Decision: termination criterion met? e.g. max generations]
    NO  → loop back to Evaluate Fitness
    YES → Output Pareto-optimal route set
```

**QA checklist:**
- [ ] All 4 genetic operators named in prose appear as distinct blocks (Selection, Crossover, Mutation, Elitism)
- [ ] Elitism percentage matches prose value
- [ ] Loop-back arrow present, terminates only on explicit condition

---

## Diagram 8 — API Integration Sequence Diagram

**Section:** 3.6.1 Software Component Integration and API Code Implementation
**Figure:** 3.9
**Caption:** *Figure 3.9: Sequence Diagram — NLP Triage API Call with Fallback*

Standard UML sequence diagram with vertical lifelines for: `Client`, `Flask Middleware`,
`Gemini 1.5 Flash API`, `fallback_regex_triage()`. Sequence must mirror the actual `try/except`
control flow in the `triage_incident_report()` code block from 3.6.1:

```
Client          Flask Middleware        Gemini API           fallback_regex_triage()
  |  raw_report_text  |                     |                        |
  |------------------->|                     |                        |
  |                    |  generate_content() |                        |
  |                    |-------------------->|                        |
  |                    |                     |                        |
  |                    |   [alt: success]    |                        |
  |                    |<--------------------|                        |
  |                    | parsed JSON         |                        |
  |<-------------------|                     |                        |
  |                    |                     |                        |
  |                    |   [alt: exception]  |                        |
  |                    |-------------------------------------------->|
  |                    |                     |     fallback result    |
  |                    |<--------------------------------------------|
  |<-------------------|                     |                        |
```

Use `[alt]` fragment framing (success vs exception) as shown — this must correspond exactly to the
`try:`/`except Exception as err:` block already in the Chapter 3 code sample.

**QA checklist:**
- [ ] 4 lifelines present, correctly labelled
- [ ] alt/exception framing matches the actual code's try/except structure
- [ ] Both return paths (success JSON, fallback result) terminate back at Client

---

## Diagram 9 — Spatial Graph Network Schema Diagram

**Section:** 3.6.2 Spatial Graph Network Topology Design
**Figure:** 3.10
**Caption:** *Figure 3.10: `network_nodes` / `network_edges` Relational-Spatial Schema*

Draw as an ER-style diagram, two boxes connected by a relationship line:

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│      network_nodes      │         │        network_edges          │
├─────────────────────────┤         ├────────────────────────────── │
│ node_id (PK)            │◄───┐    │ segment_id (PK)                │
│ geometry (POINT)        │    │    │ source_node_id (FK)            │
│ elevation_marker        │    ├────┤ target_node_id (FK)            │
│ admin_zone_tag          │    │    │ geometry (LINESTRING)          │
│ [GIST/R-Tree index]     │    │    │ length_m                       │
└─────────────────────────┘    │    │ speed_limit_kmh                │
                                │    │ turn_penalty                   │
                                │    │ crime_density_score (w input)  │
                                │    │ [GIST/R-Tree index]            │
                                │    └──────────────────────────────  │
                                └─── 1-to-many (source & target FKs) ─┘
```

**QA checklist:**
- [ ] Both FK relationships (source_node_id, target_node_id) shown pointing to network_nodes
- [ ] R-Tree/GIST index noted on both geometry columns
- [ ] crime_density_score field present (this is the ρ input to the Dijkstra weight formula — cross-reference Figure 3.6)

---

## Diagram 10 — Human-in-the-Loop Workflow Diagram

**Section:** 3.6.3 Human-in-the-Loop Decision Support Workflow
**Figure:** 3.11
**Caption:** *Figure 3.11: HITL Approval and Immutable Audit Workflow*

Sequence or state diagram:

```
System (NLP triage + MOGA optimizer)
   ↓ proposes deployment plan
Station Commander
   ↓ reviews
   ├── Approve ─────────────► Plan executed as-is
   ├── Modify (adjust priority / insert waypoint / reassign vehicle) ─► Modified plan executed
   └── Override/Reject ─────► Plan discarded, commander logs rationale
   ↓ (all three branches converge here)
Immutable PostGIS Audit Table
   — logs: original recommendation, human action taken, commander ID, timestamp
```

This diagram is direct visual evidence for the bias-mitigation and accountability argument made in
Chapter 2's gap analysis (Socio-Technical and Algorithmic Bias Vulnerability) — all three decision
branches must converge on the audit log, not just the override branch.

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

Do **not** place any diagram in 3.2 (Hardware/Software Requirements) or 3.7 (Simulation Results) —
per the guide, 3.2 is satisfied by existing tables and 3.7 is methodology-stage only; result-shaped
charts belong in Chapter 4, not here.

---

## Flag List (things the agent must NOT silently paper over)

While drawing these, if the underlying documentation text and any referenced implementation details
conflict, draw to the **documented** version and append a short flag comment rather than guessing
or harmonizing silently:

1. Haversine vs. Euclidean distance in DBSCAN — Chapter 3 documents Haversine; if this doesn't match
   what's actually implemented, flag it under Diagram 5.
2. ε / MinPts constants lack empirical (k-distance plot) justification — flag under Diagram 5.
3. Any PostGIS-vs-SQLite implementation gap — flag under Diagram 9/10 if relevant.

## Deliverable Format

Output a single markdown document, one section per diagram in the order listed in the summary
table, each containing: section heading, figure number + caption, fenced ASCII code block, and the
QA checklist. End the document with the Figure Numbering Summary table repeated for quick reference.
