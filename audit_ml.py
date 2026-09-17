import random
import copy
from collections import defaultdict
from engine.ml.dataset_generator import DatasetGenerator
from engine.ml.trainer import MLTrainer
from engine.ml.baseline import BaselineEvaluator, MetricsEvaluator
from sklearn.ensemble import HistGradientBoostingClassifier

import numpy as np

def audit():
    print("==================================================")
    print("1. DATASET ACCOUNTING & 2. SPLIT LEAKAGE AUDIT")
    print("==================================================")
    
    gen = DatasetGenerator(seed=42)
    dataset = gen.generate(num_scenarios=200) # Same as trainer
    
    scenarios = set()
    hidden_events = set()
    samples_per_missing = defaultdict(int)
    positives = 0
    negatives = 0
    cands_per_scenario = defaultdict(int)
    
    train_scen = set(s.scenario_id for s in dataset.train)
    val_scen = set(s.scenario_id for s in dataset.val)
    test_scen = set(s.scenario_id for s in dataset.test)
    
    all_samples = dataset.train + dataset.val + dataset.test
    for s in all_samples:
        scenarios.add(s.scenario_id)
        hidden_events.add(s.hidden_event_id)
        samples_per_missing[s.missing_rate] += 1
        if s.is_positive:
            positives += 1
        else:
            negatives += 1
        cands_per_scenario[s.scenario_id] += 1
        
    print(f"Number of scenarios generated: {len(scenarios)}")
    print(f"Number of hidden events: {len(hidden_events)}")
    print(f"Number of candidate rows: {len(all_samples)}")
    print(f"Positive candidates: {positives}")
    print(f"Negative candidates: {negatives}")
    
    mean_cands = np.mean(list(cands_per_scenario.values()))
    print(f"Mean candidates per scenario: {mean_cands:.2f}")
    
    for rate, count in sorted(samples_per_missing.items()):
        print(f"Samples for missing rate {rate}: {count}")
        
    print(f"\nTrain count: {len(dataset.train)} samples")
    print(f"Validation count: {len(dataset.val)} samples")
    print(f"Test count: {len(dataset.test)} samples")
    
    print("\nSplit Leakage:")
    print(f"intersection(train, validation): {train_scen & val_scen}")
    print(f"intersection(train, test): {train_scen & test_scen}")
    print(f"intersection(validation, test): {val_scen & test_scen}")

    print("\n==================================================")
    print("7. METRIC VERIFICATION & 9. ABLATION TEST")
    print("==================================================")
    
    def extract_X_y(samples, feature_mode="ALL"):
        X, y = [], []
        for s in samples:
            f = s.features
            if feature_mode == "ALL":
                vec = [f.temporal_score, f.host_score, f.user_score, f.process_score, f.technique_score, f.graph_score, f.deterministic_score]
            elif feature_mode == "NO_DETERMINISTIC":
                vec = [f.temporal_score, f.host_score, f.user_score, f.process_score, f.technique_score, f.graph_score]
            elif feature_mode == "ONLY_DETERMINISTIC":
                vec = [f.deterministic_score]
            X.append(vec)
            y.append(1 if s.is_positive else 0)
        return X, y
        
    def evaluate_model(model, samples, feature_mode):
        X, _ = extract_X_y(samples, feature_mode)
        # Deepcopy to avoid modifying test set attributes during iteration
        samples_copy = copy.deepcopy(samples)
        for s, x in zip(samples_copy, X):
            s.ml_score = float(model.predict_proba([x])[0][1])
        return MetricsEvaluator().evaluate(samples_copy, score_key="ml_score")
        
    print("\n--- Ablation Results ---")
    modes = ["ALL", "NO_DETERMINISTIC", "ONLY_DETERMINISTIC"]
    for mode in modes:
        X_train, y_train = extract_X_y(dataset.train, mode)
        clf = HistGradientBoostingClassifier(random_state=42)
        clf.fit(X_train, y_train)
        metrics = evaluate_model(clf, dataset.test, mode)
        print(f"Mode {mode}: {metrics}")
        
    print("\n--- Metric Breakdown by Missing Rate (Mode ALL) ---")
    X_train, y_train = extract_X_y(dataset.train, "ALL")
    clf = HistGradientBoostingClassifier(random_state=42)
    clf.fit(X_train, y_train)
    
    baseline_eval = BaselineEvaluator()
    for rate in [0.1, 0.2, 0.3, 0.4]:
        subset = [s for s in dataset.test if s.missing_rate == rate]
        if not subset:
            continue
        base = baseline_eval.evaluate_baseline(subset)
        ml = evaluate_model(clf, subset, "ALL")
        print(f"Missing Rate {rate}:")
        print(f"  Baseline: {base}")
        print(f"  ML:       {ml}")
        
    print("\n==================================================")
    print("10. RANDOM SEED ROBUSTNESS")
    print("==================================================")
    for seed in [42, 123, 999]:
        g = DatasetGenerator(seed=seed)
        d = g.generate(num_scenarios=200)
        X_t, y_t = extract_X_y(d.train, "ALL")
        c = HistGradientBoostingClassifier(random_state=seed)
        c.fit(X_t, y_t)
        res = evaluate_model(c, d.test, "ALL")
        print(f"Seed {seed}: {res}")

if __name__ == "__main__":
    audit()
