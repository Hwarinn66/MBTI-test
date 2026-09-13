"""Train the portable cognitive-reason classifier.

By default this script combines cognitive_reasons.csv and cognitive_reasons_v2.csv.
Only text is used as a feature. IDs, functions, family IDs and split names are
metadata and are never fed to the classifier.

The datasets are synthetic language simulations. Metrics therefore describe
held-out synthetic text, not personality accuracy on real people.
"""
import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from generate_dataset import validate_rows
from ml_local import LocalClassifier, features

BASE = Path(__file__).resolve().parent
DEFAULT_DATASETS = [
    BASE / "data" / "cognitive_reasons.csv",
    BASE / "data" / "cognitive_reasons_v2.csv",
]
SPLITS = ("train", "validation", "test")


def read_dataset(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_and_merge(paths):
    """Combine datasets, normalize unknown labels, and remove exact text duplicates.

    Later datasets win when the same normalized text occurs with the same label,
    so V2 can replace an older wording without creating duplicate training rows.
    Conflicting labels for identical text are rejected.
    """
    merged = {}
    input_counts = {}
    normalized_unknown = 0
    duplicate_rows = 0

    for path in paths:
        rows = read_dataset(path)
        input_counts[path.name] = len(rows)
        for raw in rows:
            row = dict(raw)
            function = row.get("function", "").strip()
            stance = row.get("stance", "").strip()
            text = row.get("text", "").strip()
            family_id = row.get("family_id", "").strip()
            if not text or not family_id:
                raise ValueError(f"Missing text/family_id in {path.name}")

            if function.casefold() == "unknown" or stance.casefold() == "unknown":
                if row.get("label") != "unknown":
                    normalized_unknown += 1
                row["function"] = "unknown"
                row["stance"] = "unknown"
                row["label"] = "unknown"
            else:
                row["function"] = function
                row["stance"] = stance
                row["label"] = f"{function}:{stance}"

            key = " ".join(text.casefold().split())
            previous = merged.get(key)
            if previous:
                if previous["label"] != row["label"]:
                    raise ValueError(
                        f"Conflicting labels for duplicate text: {previous['label']} vs {row['label']}"
                    )
                duplicate_rows += 1
            merged[key] = row

    rows = list(merged.values())
    return rows, {
        "input_counts": input_counts,
        "rows_before_dedup": sum(input_counts.values()),
        "rows_after_dedup": len(rows),
        "duplicates_removed": duplicate_rows,
        "unknown_labels_normalized": normalized_unknown,
    }


def assign_family_splits(rows):
    """Rebuild splits so a semantic family can never appear in two partitions.

    V1 and V2 intentionally share family IDs such as Ti-04. Treating the same
    family ID as one group across both datasets prevents cross-version leakage.
    Families are split per function, keeping every function represented in each
    partition when enough families exist.
    """
    families_by_function = defaultdict(set)
    for row in rows:
        families_by_function[row["function"]].add(row["family_id"])

    family_split = {}
    family_counts = {}
    for function, families in sorted(families_by_function.items()):
        ordered = sorted(families)
        count = len(ordered)
        if count < 3:
            raise ValueError(f"Need at least 3 semantic families for {function}; got {count}")

        validation_count = max(1, round(count * 0.15))
        test_count = max(1, round(count * 0.15))
        train_count = count - validation_count - test_count
        if train_count < 1:
            raise ValueError(f"Not enough training families for {function}")

        for index, family_id in enumerate(ordered):
            if index < train_count:
                split = "train"
            elif index < train_count + validation_count:
                split = "validation"
            else:
                split = "test"
            family_split[family_id] = split

        family_counts[function] = {
            "train": train_count,
            "validation": validation_count,
            "test": test_count,
            "total": count,
        }

    for row in rows:
        row["split"] = family_split[row["family_id"]]

    return family_counts


def combined_sha256(paths):
    digest = hashlib.sha256()
    per_file = {}
    for path in paths:
        data = path.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        per_file[path.name] = file_hash
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest(), per_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        dest="datasets",
        action="append",
        type=Path,
        help="Dataset CSV. Repeat --dataset to combine several files. Defaults to V1 + V2.",
    )
    parser.add_argument("--output-dir", type=Path, default=BASE / "models")
    args = parser.parse_args()

    datasets = args.datasets or DEFAULT_DATASETS
    missing = [str(path) for path in datasets if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset(s): " + ", ".join(missing))

    rows, merge_audit = normalize_and_merge(datasets)
    family_counts = assign_family_splits(rows)
    audit = validate_rows(rows)
    audit.update(merge_audit)
    audit["family_split_counts"] = family_counts
    audit["generator_versions"] = dict(sorted(Counter(r.get("generator_version", "unknown") for r in rows).items()))

    partitions = {split: [r for r in rows if r["split"] == split] for split in SPLITS}
    if any(not partitions[split] for split in SPLITS):
        raise ValueError("All train/validation/test partitions must be non-empty")

    vectorizer = TfidfVectorizer(analyzer=features, sublinear_tf=True, max_features=16000)
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

    choices = []
    for threshold in (0.40, 0.50, 0.60, 0.70, 0.80):
        mask = (vp.max(axis=1) >= threshold) & (vlabels != "unknown")
        accuracy = float((vlabels[mask] == y_valid[mask]).mean()) if mask.any() else 0
        choices.append({"threshold": threshold, "coverage": float(mask.mean()), "accepted_accuracy": accuracy})

    eligible = [choice for choice in choices if choice["accepted_accuracy"] >= 0.75 and choice["coverage"] >= 0.10]
    chosen = max(eligible, key=lambda choice: choice["coverage"]) if eligible else choices[-1]

    combined_hash, dataset_hashes = combined_sha256(datasets)
    model = {
        "format": "innerself-linear-v1",
        "data_source": "synthetic",
        "real_respondents": 0,
        "threshold": chosen["threshold"],
        "vocabulary": {k: int(v) for k, v in vectorizer.vocabulary_.items()},
        "idf": vectorizer.idf_.round(8).tolist(),
        "classes": classifier.classes_.tolist(),
        "coef": classifier.coef_.round(8).tolist(),
        "intercept": classifier.intercept_.round(8).tolist(),
        "dataset_files": [path.name for path in datasets],
        "dataset_sha256": combined_hash,
        "dataset_sha256_by_file": dataset_hashes,
    }

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
    runtime_labels = np.array([
        f"{p['function']}:{p['stance']}" if p["accepted"] else "abstain"
        for p in runtime_predictions
    ])

    report = {
        "scope": "SYNTHETIC held-out semantic families after V1+V2 regrouping. NOT measured accuracy on people.",
        "real_world_validation": "not_performed",
        "datasets": [str(path.relative_to(BASE)) if path.is_relative_to(BASE) else str(path) for path in datasets],
        "dataset_sha256": combined_hash,
        "dataset_sha256_by_file": dataset_hashes,
        "dataset_audit": audit,
        "features": "TF-IDF word unigrams+bigrams + character 3/4-grams; text only",
        "classifier": "multinomial LogisticRegression",
        "hyperparameter_search": trials,
        "hyperparameters": {"C": trials[best]["C"], "max_iter": 1000, "sublinear_tf": True},
        "validation_threshold_search": choices,
        "selected_threshold": chosen["threshold"],
        "test_accuracy": float(accuracy_score(y_test, predicted)),
        "test_macro_f1": float(f1_score(y_test, predicted, average="macro")),
        "test_accepted_coverage": float(accepted.mean()),
        "test_accepted_accuracy": float((predicted[accepted] == y_test[accepted]).mean()) if accepted.any() else None,
        "runtime_accepted_coverage": float(runtime_mask.mean()),
        "runtime_accepted_accuracy": float((runtime_labels[runtime_mask] == y_test[runtime_mask]).mean()) if runtime_mask.any() else None,
        "labels": classifier.classes_.tolist(),
        "confusion_matrix": confusion_matrix(y_test, predicted, labels=classifier.classes_).tolist(),
        "classification_report": classification_report(y_test, predicted, zero_division=0, output_dict=True),
        "portable_inference_parity": "passed, atol=1e-7",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(model, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    (args.output_dir / "cognitive_text.json.gz").write_bytes(gzip.compress(encoded, mtime=0))
    (args.output_dir / "evaluation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "datasets": report["datasets"],
        "rows": audit["rows"],
        "split_counts": audit["split_counts"],
        "test_accuracy": report["test_accuracy"],
        "test_macro_f1": report["test_macro_f1"],
        "test_accepted_coverage": report["test_accepted_coverage"],
        "selected_threshold": report["selected_threshold"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
