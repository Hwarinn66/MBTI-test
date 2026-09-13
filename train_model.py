"""Train locally. Held-out metrics assess synthetic language, not personality.

Only text is a feature. IDs, functions, family and split are never features.
Export safe, version-independent JSON coefficients; no pickle required at run time.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from generate_dataset import validate_rows
from ml_local import LocalClassifier, features

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=BASE / "data" / "cognitive_reasons.csv")
    parser.add_argument("--output-dir", type=Path, default=BASE / "models")
    args = parser.parse_args()
    with args.dataset.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    audit = validate_rows(rows)
    partitions = {s: [r for r in rows if r["split"] == s] for s in ("train", "validation", "test")}
    vectorizer = TfidfVectorizer(analyzer=features, sublinear_tf=True, max_features=12000)
    X_train = vectorizer.fit_transform([r["text"] for r in partitions["train"]])
    y_train = [r["label"] for r in partitions["train"]]
    X_valid = vectorizer.transform([r["text"] for r in partitions["validation"]])
    y_valid = np.array([r["label"] for r in partitions["validation"]])
    trials = []
    candidates = []
    for c in (0.3, 1, 4, 12):
        candidate = LogisticRegression(C=c, max_iter=1000, solver="lbfgs", random_state=20260912)
        candidate.fit(X_train, y_train)
        metric = float(f1_score(y_valid, candidate.predict(X_valid), average="macro"))
        trials.append({"C": c, "validation_macro_f1": metric})
        candidates.append(candidate)
    best = max(range(len(trials)), key=lambda i: trials[i]["validation_macro_f1"])
    classifier = candidates[best]
    vp = classifier.predict_proba(X_valid)
    vlabels = classifier.classes_[vp.argmax(axis=1)]
    # Choose abstention cutoff on VALIDATION only. Test remains untouched.
    choices = []
    for threshold in (0.40, 0.50, 0.60, 0.70, 0.80):
        mask = (vp.max(axis=1) >= threshold) & (vlabels != "unknown")
        accuracy = float((vlabels[mask] == y_valid[mask]).mean()) if mask.any() else 0
        choices.append({"threshold": threshold, "coverage": float(mask.mean()), "accepted_accuracy": accuracy})
    # Do not select a cutoff based on one lucky accepted example. This is only
    # a development operating point, NOT calibration on human respondents.
    eligible = [c for c in choices if c["accepted_accuracy"] >= 0.75 and c["coverage"] >= 0.10]
    chosen = max(eligible, key=lambda c: c["coverage"]) if eligible else choices[-1]
    model = {"format": "innerself-linear-v1", "data_source": "synthetic", "real_respondents": 0,
             "threshold": chosen["threshold"], "vocabulary": {k: int(v) for k, v in vectorizer.vocabulary_.items()},
             "idf": vectorizer.idf_.round(8).tolist(), "classes": classifier.classes_.tolist(),
             "coef": classifier.coef_.round(8).tolist(), "intercept": classifier.intercept_.round(8).tolist(),
             "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest()}
    portable = LocalClassifier(model)
    for sample in partitions["validation"][:20]:
        expected = classifier.predict_proba(vectorizer.transform([sample["text"]]))[0]
        actual = np.array(list(portable.probabilities(sample["text"]).values()))
        if not np.allclose(actual, expected, atol=1e-7):
            raise ValueError("Export/inference mismatch")
    X_test = vectorizer.transform([r["text"] for r in partitions["test"]])
    y_test = np.array([r["label"] for r in partitions["test"]])
    probabilities = classifier.predict_proba(X_test)
    predicted = classifier.classes_[probabilities.argmax(axis=1)]
    accepted = (probabilities.max(axis=1) >= chosen["threshold"]) & (predicted != "unknown")
    runtime_predictions = [portable.predict(r["text"]) for r in partitions["test"]]
    runtime_mask = np.array([p["accepted"] for p in runtime_predictions])
    runtime_labels = np.array([f"{p['function']}:{p['stance']}" if p["accepted"] else "abstain" for p in runtime_predictions])
    report = {"scope": "SYNTHETIC held-out semantic families only. NOT measured accuracy on people.",
              "real_world_validation": "not_performed", "dataset_audit": audit,
              "features": "TF-IDF word unigrams+bigrams + character 3/4-grams; text only", "classifier": "multinomial LogisticRegression",
              "hyperparameter_search": trials,
              "hyperparameters": {"C": trials[best]["C"], "max_iter": 1000, "sublinear_tf": True},
              "validation_threshold_search": choices, "selected_threshold": chosen["threshold"],
              "test_accuracy": float(accuracy_score(y_test, predicted)),
              "test_macro_f1": float(f1_score(y_test, predicted, average="macro")),
              "test_accepted_coverage": float(accepted.mean()),
              "test_accepted_accuracy": float((predicted[accepted] == y_test[accepted]).mean()) if accepted.any() else None,
              "runtime_accepted_coverage": float(runtime_mask.mean()),
              "runtime_accepted_accuracy": float((runtime_labels[runtime_mask] == y_test[runtime_mask]).mean()) if runtime_mask.any() else None,
              "labels": classifier.classes_.tolist(),
              "confusion_matrix": confusion_matrix(y_test, predicted, labels=classifier.classes_).tolist(),
              "classification_report": classification_report(y_test, predicted, zero_division=0, output_dict=True),
              "portable_inference_parity": "passed, atol=1e-7"}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(model, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    (args.output_dir / "cognitive_text.json.gz").write_bytes(gzip.compress(encoded, mtime=0))
    (args.output_dir / "evaluation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("scope", "test_accuracy", "test_macro_f1", "test_accepted_coverage", "selected_threshold")}, indent=2))


if __name__ == "__main__":
    main()
