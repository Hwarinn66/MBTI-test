"""Regression checks for the imported corpus, without training dependencies."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from dataset_utils import LABELS, text_key, validate_rows
from generate_dataset import build_rows
from merge_datasets import BASE, FAMILY_MAP, V2_PATH, V2_SHA256, load_v2, merge_rows


class DatasetValidationTests(unittest.TestCase):
    def setUp(self):
        self.rows = build_rows()

    def test_valid_base_corpus(self):
        audit = validate_rows(self.rows)
        self.assertEqual(audit["rows"], 9000)
        self.assertEqual(set(audit["label_counts"]), LABELS)

    def test_missing_or_blank_fields_rejected(self):
        for field in ("text", "sample_id", "family_id", "generator_version"):
            with self.subTest(field=field):
                rows = [dict(r) for r in self.rows]
                rows[0][field] = "   "
                with self.assertRaisesRegex(ValueError, "Missing or empty"):
                    validate_rows(rows)

    def test_invalid_labels_splits_and_source_rejected(self):
        for field, value in (("label", "unknown:unknown"), ("label", "ENTJ"),
                             ("split", "testing"), ("source", "human"), ("function", "XX")):
            with self.subTest(field=field, value=value):
                rows = [dict(r) for r in self.rows]
                rows[0][field] = value
                with self.assertRaises(ValueError):
                    validate_rows(rows)

    def test_whitespace_case_unicode_duplicates_rejected(self):
        duplicate = {**self.rows[0], "sample_id": "NEW", "text": "  " + self.rows[0]["text"].upper().replace(" ", "\t")}
        with self.assertRaisesRegex(ValueError, "Duplicate text"):
            validate_rows(self.rows + [duplicate])
        self.assertEqual(text_key("ＡＫＵ  belajar"), text_key("aku belajar"))

    def test_duplicate_ids_rejected(self):
        self.rows[1]["sample_id"] = self.rows[0]["sample_id"]
        with self.assertRaisesRegex(ValueError, "Duplicate sample ID"):
            validate_rows(self.rows)

    def test_family_leakage_rejected(self):
        self.rows[0]["split"] = "test" if self.rows[0]["split"] == "train" else "train"
        with self.assertRaisesRegex(ValueError, "Semantic-family leakage"):
            validate_rows(self.rows)

    def test_missing_partition_or_label_rejected(self):
        for rows in ([r for r in self.rows if r["split"] != "test"],
                     [r for r in self.rows if not (r["split"] == "test" and r["label"] == "unknown")]):
            with self.assertRaisesRegex(ValueError, "all 25 labels"):
                validate_rows(rows)


class MergedDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_rows = build_rows()
        cls.upload = load_v2(V2_PATH)
        cls.merged, cls.audit = merge_rows(cls.base_rows, cls.upload)

    def test_source_bytes_unchanged(self):
        self.assertEqual(hashlib.sha256(V2_PATH.read_bytes()).hexdigest(), V2_SHA256)

    def test_changed_upload_requires_new_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "changed.csv"
            path.write_text("different upload", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "review family mapping"):
                load_v2(path)

    def test_merge_is_reproducible_and_balanced(self):
        again, audit = merge_rows(self.base_rows, self.upload)
        self.assertEqual(again, self.merged)
        self.assertEqual(audit, self.audit)
        self.assertEqual(audit["rows"], 25000)
        self.assertEqual(set(audit["label_counts"].values()), {1000})
        self.assertEqual(audit["duplicates_removed"], 0)
        self.assertEqual(audit["unknown_labels_normalized"], 640)
        self.assertEqual(audit["v2_original_leaking_families"], 138)
        self.assertEqual(audit["semantic_family_overlap"], 0)

    def test_base_text_labels_and_splits_preserved(self):
        base = {r["sample_id"]: r for r in self.base_rows}
        for row in self.merged:
            if row["sample_id"].startswith("v1:"):
                previous = base[row["source_sample_id"]]
                for field in ("text", "label", "family_id", "split"):
                    self.assertEqual(row[field], previous[field])

    def test_cross_version_paraphrases_share_family_and_split(self):
        self.assertEqual(FAMILY_MAP["Ne-07"], "Ne-10")
        self.assertEqual(FAMILY_MAP["Ti-06"], "Ti-10")
        v1_splits = {r["family_id"]: r["split"] for r in self.base_rows}
        for row in self.merged:
            self.assertEqual(row["split"], v1_splits[row["family_id"]])
            if row["sample_id"].startswith("v2:"):
                self.assertEqual(row["family_id"], FAMILY_MAP[row["source_family_id"]])

    def test_active_dataset_and_metadata_match_rebuild(self):
        path = BASE / "data" / "cognitive_reasons.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            saved = list(csv.DictReader(handle))
        self.assertEqual(saved, self.merged)
        metadata = json.loads(path.with_suffix(".metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(metadata["family_mapping"], FAMILY_MAP)

    def test_duplicate_with_conflicting_label_is_not_silently_dropped(self):
        duplicate = dict(self.base_rows[0])
        duplicate["sample_id"] = "other"
        duplicate["generator_version"] = "synthetic-cognitive-v2"
        duplicate["function"] = "unknown"
        duplicate["stance"] = "unknown"
        duplicate["label"] = "unknown"
        duplicate["family_id"] = "unknown-00"
        with self.assertRaisesRegex(ValueError, "Conflicting labels"):
            merge_rows(self.base_rows, [duplicate])

    def test_matching_duplicate_is_counted_once(self):
        source = next(r for r in self.base_rows if r["family_id"] == "Te-00" and r["stance"] == "support")
        duplicate = {**source, "sample_id": "duplicate", "generator_version": "synthetic-cognitive-v2"}
        merged, audit = merge_rows(self.base_rows, [duplicate])
        self.assertEqual(len(merged), 9000)
        self.assertEqual(audit["duplicates_removed"], 1)

    def test_duplicate_across_families_requires_review(self):
        source = next(r for r in self.base_rows if r["family_id"] == "Te-00" and r["stance"] == "support")
        duplicate = {**source, "sample_id": "duplicate", "family_id": "Te-03",
                     "generator_version": "synthetic-cognitive-v2"}
        with self.assertRaisesRegex(ValueError, "crosses semantic families"):
            merge_rows(self.base_rows, [duplicate])

    def test_unknown_family_cannot_be_imported(self):
        row = {**self.upload[0], "family_id": "Ne-99"}
        with self.assertRaisesRegex(ValueError, "Unreviewed"):
            merge_rows(self.base_rows, [row])


if __name__ == "__main__":
    unittest.main()
