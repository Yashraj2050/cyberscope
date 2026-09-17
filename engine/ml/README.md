# ML Module for CyberScope (Phase 2A)

This module introduces a controlled machine learning ranker for reconstruction candidates.

## Why ML is used
The deterministic rule-based gap scorer is highly effective and transparent, but relies on rigid heuristics. The ML ranker is introduced to scale non-linear interactions across those heuristic dimensions (e.g., temporal vs graph distance tradeoffs) without breaking the strict validation logic of the application. 

## Dataset generation
Synthetic attack paths are programmatically constructed across MITRE techniques. Simulated missing telemetry generates deterministic "gaps", and candidates are produced to evaluate the gap. The data is partitioned by `scenario_id` ensuring no test leakage occurs.

## Feature schema
- temporal_score
- host_score
- user_score
- process_score
- technique_score
- graph_score
- deterministic_score

## Training
`HistGradientBoostingClassifier` natively handles numeric scaling and missing patterns. Train/Val/Test is isolated.

## Evaluation
Measured in Top-1, Top-3, and MRR. The Baseline uses the `deterministic_score`, whereas the ML model relies on predicting the hidden positive sample probability.

## Ground-truth isolation
The `FeatureExtractor` prevents access to `ground_truth_events` via an absolute exception block. Ground truth is purely retained in the synthetic generator script to evaluate the rank order post-inference.

## Model limitations
The ML Ranker operates strictly on synthetic assumptions. If production encounters completely novel topologies, it safely degrades behavior gracefully. 

## Final Decision
ML ranks candidates; it **does NOT** make the final `OBSERVED / INFERRED / UNKNOWN` decision. That remains strictly bounded by the `EvidenceVerifier` acting as the ultimate trust anchor.

---

# CyberScope Phase 2B Integration

The ML Ranker is fully integrated as an optional production feature in Phase 2B. 

## Ranking Modes
The `CandidateRanker` now exposes three modes via the `RankingContext`:
- **DETERMINISTIC**: (Default) Strict heuristic adherence.
- **ML**: Pure machine-learning probability sorting.
- **HYBRID**: Alpha-weighted combination of `deterministic_score` and `ml_ranking_score`.

## Safe Fallback & Logging
If the `.joblib` model artifact is corrupt or missing, the `CandidateRanker` automatically safely degrades to `DETERMINISTIC_FALLBACK`. Crucially, failure states are logged via the secure Python `logging` module to avoid polluting stdout or exposing raw telemetry payloads.

## Provenance Metadata
All ML predictions automatically trace the `model_version`, `dataset_version`, and `feature_schema_version`, appending it into the response's `AnalysisMetadata` payload, ensuring complete chain of custody for any inferred evidence decisions downstream.
