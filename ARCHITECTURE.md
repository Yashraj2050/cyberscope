# CyberScope Architecture

## SAT-SA Context
CyberScope contributes an evidence-aware, offline-first capability to the Supervisory Analytics Tool for SOC Assessment (SAT-SA / SIH26157). The architecture below describes the core reconstruction pipeline that supports supervisory assessment by analysing incomplete operational security evidence.

## Ground-Truth Isolation
A foundational constraint of the CyberScope architecture is **perfect isolation of ground-truth data from the reconstruction engine**.
Ground-truth events (`ground_truth_events`) provided in synthetic scenarios are rigorously discarded at parse time (in `engine/main.py`). The core reconstruction algorithms—gap detection, candidate generation, scoring, and verification—operate strictly on `observed_events`. The ground-truth is purely utilized for evaluation metrics and is never leaked into the operational UI, LLM context, or export mechanisms.

## Core Pipeline

The reconstruction pipeline executes synchronously in a 6-stage process:

1. **Telemetry Parsing:**
   The `observed_events` are deserialized into `CyberEvent` models, capturing timestamps, hosts, users, processes, and MITRE ATT&CK techniques.

2. **Validation:**
   Basic temporal and structural validation is performed. Out-of-order events or wildly malformed schema entries are rejected before processing.

3. **Attack Graph Construction:**
   The `GraphEngine` stitches disparate telemetry events into a directed acyclic graph based on timestamps and host/user/process continuities.

4. **Evidence Gap Detection:**
   The `GapDetector` analyzes consecutive nodes in the attack graph. If the logical "distance" between two events exceeds a dynamically computed threshold (based on temporal delays and continuity breaks), an **Operational Evidence Gap** is identified — a discontinuity in available evidence requiring further human review.
   
   *Gap Signals:*
   - **technique transition:** Flagged if the transition between two MITRE techniques lacks a known logical bridge.
   - **behavioral prerequisite:** Flagged if an event occurs without a necessary precursor (e.g., Execution without Delivery).
   - **host continuity:** Flagged if activity jumps between hosts without a visible lateral movement mechanism.
   - **user continuity:** Flagged if activity switches user contexts without a visible privilege escalation or credential access event.
   - **process relationship:** Flagged if two events are causally disjoint in the process tree.
   - **temporal:** Flagged if the time delta between events exceeds standard interactive or automated thresholds.

5. **Candidate Generation & Scoring:**
   When a gap is detected, the `CandidateGenerator` consults a localized knowledge base (`TECHNIQUE_STAGE_MAP`) to propose plausible missing MITRE techniques.
   The `CandidateScorer` then evaluates each candidate against the surrounding observed evidence. It computes a `candidate_score` for each hypothesis.
   
   **IMPORTANT:** The `candidate_score` represents the degree of *evidence support* for a candidate, not a mathematical probability. It is an aggregate of continuity matches (e.g., does this candidate conceptually bridge the host/user gap?).

6. **Evidence Verification:**
   The `EvidenceVerifier` performs a final sanity check on the highest-scoring candidate. It asserts seven dimensions (`temporal`, `host`, `user`, `process`, `technique`, `contradiction`, `ambiguity`) to ensure the hypothesis doesn't violently contradict known facts.
   
   Based on the verification, the final status is assigned:
   - **OBSERVED:** The event was directly supported by telemetry (no gap existed).
   - **INFERRED:** A gap existed, and a candidate was successfully supported by available evidence and passed verification.
   - **UNKNOWN:** A gap existed, but the available evidence was insufficient or ambiguous (e.g., multiple candidates had tied evidence scores). CyberScope aggressively withholds classification rather than hallucinating an answer. UNKNOWN results are flagged for human supervisory review.

## Safety Properties
- The optional local LLM (AI Analyst) cannot create evidence, modify telemetry, modify ground truth, or override verification results.
- UNKNOWN cannot be converted to INFERRED by the LLM or any non-deterministic component.
- Deterministic verification remains the final trust boundary.

## UI / Packaging
The result of this pipeline is returned as a `FullPipelineResult` JSON object. 
The React frontend (bundled via Vite) renders this payload statically. The entire ecosystem is packaged as a local desktop executable using Tauri (Rust), with the Python engine bundled as a PyInstaller sidecar.
