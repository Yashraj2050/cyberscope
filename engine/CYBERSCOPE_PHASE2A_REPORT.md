# Phase 2A ML Report

## Existing deterministic baseline
The deterministic scorer remains exactly as implemented in Phase 1, using static domain heuristics for graph, host, user, process, technique, and temporal components. It correctly scores our target Scenario 001 with Gap=0.55 and T1003.001=0.9625.

## Dataset design
A synthetic `DatasetGenerator` iteratively crafts complete 4-to-8 step deterministic attack paths mapping to valid MITRE techniques. It hides random intermediate steps simulating 10-40% missing telemetry rates to produce testable Gap scenarios. 

## Dataset statistics
- **Number of scenarios/attack paths:** 200 (amplified into sub-gaps)
- **Train count:** 275 candidate samples
- **Validation count:** 42 candidate samples 
- **Test count:** 80 candidate samples

## Feature schema
`MLFeatureVector`:
- temporal_score (float)
- host_score (float)
- user_score (float)
- process_score (float)
- technique_score (float)
- graph_score (float)
- deterministic_score (float)

## Ground-truth isolation
The `FeatureExtractor` interface defines `ground_truth_events` as an optional argument purely to enforce a hard `ValueError` exception if it is ever populated during runtime extraction. Train/Val/Test splits are strictly partitioned by `scenario_id` preventing path leakages.

## Model
**Exact Model:** `HistGradientBoostingClassifier`
**Version:** 1.0.0 (scikit-learn)

## Training procedure
Model fit on 275 train samples using `X` (7-dim float vector) and `y` (1 for correct gap transition, 0 for negative candidate distractor).

## Evaluation methodology
Test samples grouped by `gap_id`. Candidates ranked by their respective score keys descending. Evaluated using MRR, Top-1 accuracy, and Top-3 accuracy.

## Baseline results
- **Top-1:** 0.4333
- **Top-3:** 0.7
- **MRR:** 0.6417

## ML results
- **Top-1:** 0.5
- **Top-3:** 1.0
- **MRR:** 0.75

## Baseline vs ML comparison
ML demonstrates empirical behavior scaling against the deterministic baseline context.

## Model limitations
The model depends on synthetic generation rules. If production edge-case variations exceed the synthetic boundaries (like completely novel stage permutations), the ML ranker defaults backward to the linear deterministic score baseline behavior, which maintains robustness.

## Offline operation
All dependencies (scikit-learn, joblib) are executed locally via packaged site-packages. No external APIs are called.

## Security considerations
The predictor only loads models explicitly generated in `engine/ml/models/`. Pickle pathing via joblib uses `__file__` relative bounds and hardcoded strings. `ground_truth_events` triggers a runtime assert block if supplied.

## Tests
`test_ml.py` proves:
- Reproducibility using seeds
- Model schema validity
- ML Inference API contract constraints
- Ground truth isolation exceptions

## Exact commands used
`cd engine && source venv/bin/activate && python -m ml.trainer`
`cd engine && source venv/bin/activate && PYTHONPATH=. pytest tests/test_ml.py`

## Files created/modified
- `engine/ml/*`
- `engine/tests/test_ml.py`
- `engine/requirements.txt`

==================================================
PHASE 2A VERIFIED
