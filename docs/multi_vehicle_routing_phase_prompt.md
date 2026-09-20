# Phase Prompt: Multi-Vehicle Patrol Routing (Geographic Partition Heuristic)

## Context for the agent

This is an extension to the Crime-Watch patrol optimization engine, part of a
university dissertation project. The engine currently generates **one**
optimized patrol route per invocation, using a hand-implemented Genetic
Algorithm (GA) that calls a hand-implemented dynamic-weight Dijkstra as a
sub-routine to score candidate hotspot orderings (see `patrol/ga.py` and
`patrol/dijkstra.py`, or equivalent paths in this repo — locate and confirm
before editing).

**Do not modify the existing single-vehicle GA or Dijkstra logic.** The goal
of this phase is to *reuse* that logic unchanged, N times, once per vehicle,
after a geographic pre-partitioning step. This is a deliberate architectural
choice: it is **not** a full Vehicle Routing Problem (VRP) solver. Do not
attempt to jointly optimize partition assignment and route order — that is
explicitly out of scope for this phase (see "Explicitly out of scope" below).

If at any point implementing this requires modifying the existing GA
chromosome encoding, crossover, mutation, or fitness function — **stop and
surface this to the developer** rather than proceeding. That would mean the
task has drifted into full VRP territory (a different, larger piece of work,
described at the bottom of this document as future work).

---

## Objective

Given a set of active hotspot centroids and a number of available patrol
vehicles `N`, produce `N` independent, non-overlapping patrol routes by:

1. Geographically partitioning hotspot centroids into `N` groups.
2. Running the existing single-vehicle GA + Dijkstra pipeline independently
   on each group, unmodified.
3. Returning `N` labeled route results instead of one.

When `N = 1`, this must behave **identically** to the current single-vehicle
system — no partitioning step should run, and output should be unchanged
from current behavior. Verify this explicitly (see Validation section).

---

## Step-by-step implementation

### Step 1 — Partition function

Create a new, isolated module (e.g. `patrol/partitioning.py`). Do not put
this logic inside the existing GA or Dijkstra files.

- Input: list of hotspot centroids (lat/lng or projected coordinates —
  confirm which coordinate representation the existing hotspot engine
  outputs and match it, do not silently convert or assume), integer `N`.
- Method: `sklearn.cluster.KMeans(n_clusters=N)` on the centroid
  coordinates. If `sklearn` is already a project dependency (it is, for the
  TF-IDF/SVM NLP baseline), reuse that dependency rather than introducing a
  new clustering library.
- Output: a list of `N` groups, each a list of hotspot centroids assigned to
  that group.
- Edge cases to handle explicitly, not silently:
  - `N=1` → return all hotspots as a single group, skip KMeans entirely.
  - `N >= number of hotspots` → some vehicles will receive zero or one
    hotspots. Do not error. Log this condition. A vehicle assigned zero
    hotspots should return an empty route, not a crash.
  - `N <= 0` or non-integer `N` → raise a clear validation error at the API
    boundary (see Step 3), do not let it reach the partitioning function.
  - Fewer than `N` distinct hotspot locations available (e.g., duplicate
    coordinates) — KMeans can behave unexpectedly here. Add a guard: if
    KMeans raises or produces degenerate output, fall back to a simple
    round-robin assignment across vehicles and log a warning that the
    fallback path was used. This must be visible in logs/response metadata,
    not hidden.

### Step 2 — Per-partition routing

- For each of the `N` groups produced in Step 1, call the **existing**
  single-vehicle GA function with that group's hotspots as input, exactly as
  it is currently called for the single-vehicle case. Do not alter its
  signature unless strictly necessary (e.g., adding an optional
  `vehicle_id` passthrough for labeling purposes only — this must not affect
  the algorithm's internal logic).
- Run these N calls sequentially first and confirm correctness before
  considering parallelization. Parallelizing N independent GA runs is a
  legitimate future optimization but is out of scope for this phase — do
  not add multiprocessing/threading in this pass unless explicitly asked.
- Collect results as a list of `{vehicle_id, route, cost_metrics}` objects.

### Step 3 — API layer changes

- Add an optional `vehicle_count` (or equivalent — match existing naming
  conventions in the codebase) parameter to the routing request endpoint.
  Default to `1` if omitted, preserving current behavior for any existing
  callers/tests.
- Validate `vehicle_count` is a positive integer before it reaches the
  partitioning function (see Step 1 edge cases).
- Response schema: change from a single route object to a list of route
  objects, each tagged with a `vehicle_id`. **This is a breaking API change**
  — check for and update any existing frontend code, tests, or other
  consumers that assume a single-route response shape. Do not leave the old
  response shape silently broken.

### Step 4 — Database schema changes

- Add a `vehicle_id` (or `unit_id` — match existing naming conventions)
  field to whatever table/model currently stores generated routes.
- If routes are currently stored as a single record per generation event,
  confirm whether the schema needs to move to one-record-per-vehicle-route,
  or a parent/child relationship (one generation event → N route records).
  Choose based on what's least disruptive to the existing audit log
  structure — **do not break the existing immutable audit trail
  functionality while doing this.** If PostGIS persistence (volume mount)
  has not yet been fixed, do not proceed with schema changes until it has —
  confirm this with the developer before starting.

### Step 5 — Frontend/dashboard changes

- Update the Leaflet map component to render N route layers instead of one,
  when `vehicle_count > 1`.
- Color-code or otherwise visually distinguish routes per vehicle (distinct
  line colors, a legend, or a toggle to show/hide individual vehicle
  routes).
- Add a UI control (dropdown, input, or similar — match existing UI
  patterns) for the commander to specify how many vehicles are available for
  the current shift before generating routes.
- Confirm the Next.js API route layer remains a **thin proxy only** — per
  the existing architectural constraint, no algorithmic or partitioning
  logic should be written on the JavaScript/TypeScript side. All
  partitioning and routing logic stays in the Flask backend.

---

## Validation requirements (do not skip)

This is the part most likely to be under-done by default — do not treat it
as optional polish.

1. **Regression test: N=1 behaves identically to current system.**
   Run the same hotspot input through both the old code path (if still
   accessible) and the new N=1 path. Route, cost metrics, and ordering
   should match exactly. If they don't, something in the partitioning
   wrapper is altering behavior it shouldn't — stop and report this rather
   than adjusting the test to pass.

2. **Partition sanity checks**, on at least one realistic dataset (real or
   synthetic Harare-scoped hotspot centroids):
   - Every hotspot is assigned to exactly one vehicle (no duplicates, no
     omissions).
   - No partition is wildly imbalanced without cause — report the count of
     hotspots per vehicle for a few test values of N (e.g., N=2, N=3, N=5)
     so the developer can visually sanity-check that geographic partitioning
     is producing sensible-looking zones, not something degenerate.
   - Produce this as a simple table or printed summary, not just "tests
     pass" — the developer needs to eyeball this for the dissertation
     writeup regardless of whether automated assertions pass.

3. **Known limitation to explicitly surface, not silently accept:**
   Confirm and report whether load imbalance occurs in test runs (e.g., one
   vehicle assigned 10 hotspots, another assigned 2). This is expected
   behavior for a geographic-partition heuristic, not a bug — but it must be
   visible and reported, because it is a documented limitation that needs to
   go into the dissertation (see Documentation section below), not
   discovered for the first time during defense.

4. **No changes to single-vehicle GA/Dijkstra output correctness.** If the
   project has existing unit tests validating the custom Dijkstra against
   NetworkX's reference `shortest_path()`, or GA correctness checks, run
   them after this change and confirm they still pass unmodified.

---

## Documentation requirements

After implementation, produce a short summary (for the developer to adapt
into Chapter 3 of the dissertation) covering:

- A one-paragraph description of the geographic pre-partitioning approach,
  written at the same technical register as the existing §3.5.3/§3.5.4
  content (i.e., precise, not marketing language).
- An explicit statement that this is a **heuristic decoupling of
  partitioning and routing**, not a joint optimization, and that it does not
  guarantee load-balanced routes across vehicles.
- The actual partition-size results observed during validation testing (see
  Validation Step 2), to be used as a small illustrative table if the
  developer wants one.
- A one-sentence note that full joint multi-vehicle optimization (VRP) is
  identified as future work — see below.

**Do not write dissertation prose in an inflated or promotional tone.** Match
the existing chapter's plain, precise, limitation-aware style.

---

## Explicitly out of scope for this phase

Do not implement any of the following unless separately instructed:

- Joint optimization of partition assignment and route order (this is full
  VRP — see Future Work below).
- Load-balancing logic that reassigns hotspots between vehicles based on
  route cost.
- Real-time reassignment of routes mid-shift.
- Parallel/concurrent execution of the N GA runs.
- Changes to the GA's chromosome encoding, crossover, mutation, or fitness
  function.
- Any new external dependencies beyond `sklearn` (already present in the
  project).

If completing this task seems to require any of the above, stop and report
back rather than expanding scope silently.

---

## Future work note (for the dissertation, not for this implementation phase)

For context only — do not build this now, but be aware it may inform how
you name/structure things (e.g., keep partitioning and routing as separable
functions, not tangled together, so a future VRP implementation could
plausibly replace just the partitioning step):

A full VRP formulation would jointly encode vehicle assignment **and**
visiting order in a single chromosome (e.g., a permutation of all hotspots
with N−1 divider markers splitting it into per-vehicle sub-routes), require
redesigned crossover/mutation operators that preserve validity across
dividers (no duplicate hotspots across vehicles, no accidental empty
routes), and a fitness function that makes an explicit design choice between
minimizing total fleet cost vs. minimizing the maximum single vehicle's
cost (load balancing). It would also require a new correctness-validation
strategy, since there is no simple reference implementation to diff against
the way NetworkX serves as a reference for single-source Dijkstra — small
hand-verified or brute-force synthetic test cases would be needed instead.
This is a substantially larger effort than the partition-heuristic approach
implemented in this phase and is recommended as a named item in Chapter 5
(Recommendations and Future Work), not attempted before final defense.

---

## Final checklist before marking this phase complete

- [ ] N=1 case verified identical to prior single-vehicle behavior
- [ ] Partition edge cases (N=1, N≥hotspot count, degenerate KMeans) handled
      and logged, not silently swallowed
- [ ] API breaking change identified and all consumers updated
- [ ] Existing immutable audit log functionality unaffected
- [ ] PostGIS persistence confirmed working before schema changes made
- [ ] Existing GA/Dijkstra correctness tests still pass unmodified
- [ ] Partition balance results captured and reported for developer review
- [ ] No algorithmic logic introduced into the Next.js API proxy layer
- [ ] Summary written for Chapter 3 documentation, in matching tone,
      explicitly naming the heuristic-not-joint-optimization limitation
- [ ] Any scope creep toward full VRP surfaced to developer, not built
