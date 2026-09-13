"""Merge the reviewed v2 upload with reproducible v1, retaining provenance.

V2 reused family IDs for different meanings and split every family across all
partitions. The explicit mapping below aligns known paraphrases to v1 families
BEFORE training; v1's original partitions are preserved. Merely prefixing family
IDs by version would not prevent cross-version paraphrase leakage.

Mappings are conservative author judgements, not expert personality labels or
proof that all semantic similarity has been eliminated. Changed/new uploads
require another review rather than silently reusing this mapping.
"""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from dataset_utils import FIELDS, text_key, validate_row, validate_rows
from generate_dataset import SEED, build_rows

BASE = Path(__file__).resolve().parent
VERSION = "synthetic-cognitive-merged-v1-v2"
V2_VERSION = "synthetic-cognitive-v2"
V2_SHA256 = "d8c97b5ee8b8be6d7cd69cba4269b90c8f65516d5aec56283046fa327b9fb2e1"
V2_PATH = BASE / "data" / "sources" / "cognitive_reasons_v2.csv"
PROVENANCE_FIELDS = ("source_sample_id", "source_family_id", "source_split")

# List index = v2 family number, value = v1 family number. Related extra
# formulations (12-15) deliberately stay with the corresponding broader family.
V2_TO_V1 = {
    "Te": (0, 3, 2, 1, 4, 5, 7, 10, 8, 6, 9, 11, 5, 1, 8, 1),
    "Ti": (0, 1, 2, 3, 6, 4, 10, 7, 8, 11, 5, 9, 7, 7, 1, 10),
    "Fe": (0, 1, 7, 3, 2, 6, 4, 8, 11, 5, 10, 9, 3, 3, 3, 0),
    "Fi": (0, 4, 3, 5, 2, 1, 6, 7, 8, 10, 9, 11, 2, 3, 0, 4),
    "Ne": (5, 1, 8, 2, 6, 9, 4, 10, 7, 3, 11, 0, 0, 6, 2, 8),
    "Ni": (6, 3, 5, 2, 7, 11, 1, 9, 10, 5, 7, 2, 7, 8, 9, 3),
    "Se": (3, 0, 7, 2, 9, 8, 6, 4, 10, 5, 8, 6, 11, 5, 9, 8),
    "Si": (0, 2, 1, 6, 8, 5, 7, 10, 3, 4, 9, 11, 2, 4, 0, 10),
    "unknown": (3, 10, 6, 5, 7, 11, 8, 0, 9, 4),
}
FAMILY_MAP = {f"{f}-{i:02}": f"{f}-{target:02}"
              for f, targets in V2_TO_V1.items() for i, target in enumerate(targets)}


def load_v2(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != V2_SHA256:
        raise ValueError("V2 file differs from the reviewed upload; review family mapping before importing")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def merge_rows(v1_rows, v2_rows):
    validate_rows(v1_rows)
    split_by_family = {r["family_id"]: r["split"] for r in v1_rows}
    merged, seen, source_ids = [], {}, set()
    original_groups = defaultdict(set)
    corrections = Counter()
    for version_name, source_rows in (("v1", v1_rows), ("v2", v2_rows)):
        for original in source_rows:
            row = {field: original.get(field) for field in FIELDS}
            # Only the known equivalent unknown spelling is repaired.
            if row["label"] == "unknown:unknown" and row["function"] == row["stance"] == "unknown":
                row["label"] = "unknown"
                corrections["unknown_labels_normalized"] += 1
            validate_row(row)
            source_id = (version_name, row["sample_id"])
            if source_id in source_ids:
                raise ValueError("Duplicate source sample ID")
            source_ids.add(source_id)
            row.update(source_sample_id=row["sample_id"], source_family_id=row["family_id"],
                       source_split=row["split"])
            row["sample_id"] = f"{version_name}:{row['sample_id']}"
            if version_name == "v2":
                if row["generator_version"] != V2_VERSION or row["family_id"] not in FAMILY_MAP:
                    raise ValueError("Unreviewed v2 version or family")
                original_groups[row["family_id"]].add(row["split"])
                row["family_id"] = FAMILY_MAP[row["family_id"]]
                if row["family_id"].split("-")[0] != row["function"]:
                    raise ValueError("Family/function mismatch")
                row["split"] = split_by_family[row["family_id"]]
                corrections["v2_split_changes"] += row["split"] != row["source_split"]
            key = text_key(row["text"])
            if key in seen:
                previous = seen[key]
                if previous["label"] != row["label"]:
                    raise ValueError("Conflicting labels for duplicate text; manual review required")
                if (previous["family_id"], previous["split"]) != (row["family_id"], row["split"]):
                    raise ValueError("Duplicate text crosses semantic families; manual review required")
                corrections["duplicates_removed"] += 1
                continue
            seen[key] = row
            merged.append(row)
    random.Random(SEED).shuffle(merged)
    audit = validate_rows(merged)
    audit.update({"version": VERSION, "seed": SEED,
                  "input_rows": {"v1": len(v1_rows), "v2": len(v2_rows)},
                  "duplicates_removed": corrections["duplicates_removed"],
                  "unknown_labels_normalized": corrections["unknown_labels_normalized"],
                  "v2_split_changes": corrections["v2_split_changes"],
                  "v2_original_leaking_families": sum(len(s) > 1 for s in original_groups.values()),
                  "split_policy": "Preserve v1 partitions; manually align reviewed v2 paraphrases to v1 families",
                  "family_mapping": FAMILY_MAP,
                  "warning": "Synthetic sentences, not human validation. Family mapping is a conservative author judgement, not expert annotation or a guarantee against all semantic overlap."})
    return merged, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2", type=Path, default=V2_PATH)
    parser.add_argument("--output", type=Path, default=BASE / "data" / "cognitive_reasons.csv")
    args = parser.parse_args()
    if args.output.resolve() == args.v2.resolve():
        parser.error("Output must not overwrite the original v2 source")
    rows, metadata = merge_rows(build_rows(), load_v2(args.v2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS + PROVENANCE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    metadata["sha256"] = hashlib.sha256(args.output.read_bytes()).hexdigest()
    metadata["v2_source_sha256"] = V2_SHA256
    args.output.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({k: metadata[k] for k in ("rows", "split_counts", "duplicates_removed",
                     "unknown_labels_normalized", "v2_original_leaking_families", "semantic_family_overlap")}, indent=2))


if __name__ == "__main__":
    main()
