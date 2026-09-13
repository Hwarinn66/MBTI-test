"""Validate the synthetic sentence corpus before fitting any model."""
import unicodedata
from collections import Counter, defaultdict

FUNCTIONS = ("Te", "Ti", "Fe", "Fi", "Ne", "Ni", "Se", "Si")
STANCES = ("support", "oppose", "mixed")
SPLITS = ("train", "validation", "test")
FIELDS = ("sample_id", "text", "function", "stance", "label", "family_id",
          "split", "source", "generator_version")
LABELS = {f"{f}:{s}" for f in FUNCTIONS for s in STANCES} | {"unknown"}


def text_key(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def validate_row(row):
    if any(not isinstance(row.get(k), str) or not row[k].strip() for k in FIELDS):
        raise ValueError("Missing or empty dataset field")
    function, stance = row["function"], row["stance"]
    expected = "unknown" if function == stance == "unknown" else f"{function}:{stance}"
    if expected not in LABELS or row["label"] != expected:
        raise ValueError(f"Invalid function/stance/label: {row['sample_id']}")
    if row["split"] not in SPLITS:
        raise ValueError(f"Invalid split: {row['sample_id']}")
    # This pipeline reports zero real respondents. Do not silently accept human
    # data under that claim; it requires a separately reviewed protocol.
    if row["source"] != "synthetic":
        raise ValueError("Only declared synthetic sources are supported")


def validate_rows(rows):
    if not rows:
        raise ValueError("Empty dataset")
    texts, ids = set(), set()
    groups, group_functions = defaultdict(set), defaultdict(set)
    split_labels = defaultdict(set)
    for row in rows:
        validate_row(row)
        key = text_key(row["text"])
        if key in texts:
            raise ValueError("Duplicate text found")
        if row["sample_id"] in ids:
            raise ValueError("Duplicate sample ID found")
        texts.add(key)
        ids.add(row["sample_id"])
        groups[row["family_id"]].add(row["split"])
        group_functions[row["family_id"]].add(row["function"])
        split_labels[row["split"]].add(row["label"])
    if any(len(s) > 1 for s in groups.values()):
        raise ValueError("Semantic-family leakage")
    if any(len(s) > 1 for s in group_functions.values()):
        raise ValueError("A semantic family contains inconsistent functions")
    if any(split_labels[s] != LABELS for s in SPLITS):
        raise ValueError("Every split must contain all 25 labels")
    return {"rows": len(rows), "unique_texts": len(texts), "unique_sample_ids": len(ids),
            "split_counts": dict(Counter(r["split"] for r in rows)),
            "label_counts": dict(sorted(Counter(r["label"] for r in rows).items())),
            "generator_counts": dict(sorted(Counter(r["generator_version"] for r in rows).items())),
            "semantic_family_count": len(groups), "semantic_family_overlap": 0,
            "real_respondents": 0}
