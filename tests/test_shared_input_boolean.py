"""Check the shared companion-file contract used by both formulations."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from formulation2 import solve_boolean
from shared_input import load_metadata, read_file
from tests.test_formulation2 import ROOT, make_instance


class SharedInputTests(unittest.TestCase):
    def valid_metadata(self):
        return {
            "exam_requirements": [["computers"]],
            "room_facilities": [["computers", "projector"]],
            "exam_durations": [90], "slot_durations": [120],
        }

    def load(self, metadata):
        instance = make_instance(1, 1, [1], [(0, 0)])
        with TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "case.extra.json"
            path.write_text(json.dumps(metadata), encoding="utf-8")
            load_metadata(instance, path)
        return instance

    def test_complete_metadata_is_normalized_and_marked_extended(self):
        instance = self.load(self.valid_metadata())
        self.assertEqual(instance.exam_requirements, [{"computers"}])
        self.assertEqual(instance.metadata_mode, "extended")

    def test_original_files_use_explicit_neutral_baseline_values(self):
        instance = read_file(ROOT / "instances" / "sat2.txt")
        self.assertEqual(instance.metadata_mode, "baseline")
        self.assertEqual(instance.exam_requirements, [set(), set()])
        self.assertEqual(instance.room_facilities, [set()])
        self.assertEqual(instance.exam_durations, [60, 60])
        self.assertEqual(instance.slot_durations, [120, 120, 120])
        self.assertEqual(solve_boolean(instance)["metadata_mode"], "baseline")

    def test_companion_is_discovered_and_baseline_can_be_requested(self):
        with TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "exam.txt"
            path.write_text((ROOT / "instances" / "sat1.txt").read_text(), encoding="utf-8")
            metadata = self.valid_metadata()
            metadata["exam_durations"] = [121]
            path.with_suffix(".extra.json").write_text(json.dumps(metadata), encoding="utf-8")
            extended = read_file(path)
            baseline = read_file(path, baseline=True)
            self.assertEqual(extended.metadata_mode, "extended")
            self.assertEqual(solve_boolean(extended)["status"], "unsat")
            self.assertEqual(solve_boolean(baseline)["status"], "sat")

    def test_explicit_missing_file_is_an_error(self):
        with TemporaryDirectory(dir=ROOT) as directory:
            with self.assertRaises(FileNotFoundError):
                read_file(ROOT / "instances" / "sat1.txt", Path(directory) / "missing.json")

    def test_partial_null_unknown_or_nondictionary_metadata_is_rejected(self):
        valid = self.valid_metadata()
        cases = [None, [], {**valid, "room_features": []},
                 {name: value for name, value in valid.items() if name != "slot_durations"}]
        cases += [{**valid, name: None} for name in valid]
        cases += [{name: None for name in valid}]
        for metadata in cases:
            with self.subTest(metadata=metadata):
                with self.assertRaises(ValueError):
                    self.load(metadata)

    def test_wrong_lengths_and_feature_types_are_rejected(self):
        for field in self.valid_metadata():
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    self.load({**self.valid_metadata(), field: []})
        for value in ["computers", ["computers"], [[1]], [[""]], [[" computers"]]]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.load({**self.valid_metadata(), "room_facilities": value})

    def test_durations_are_positive_integer_minutes(self):
        for field in ("exam_durations", "slot_durations"):
            for value in (0, -1, 90.5, "90", True):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        self.load({**self.valid_metadata(), field: [value]})

    def test_partial_programmatic_metadata_is_not_silently_defaulted(self):
        instance = make_instance(1, 1, [1], [(0, 0)])
        instance.exam_requirements = [["computers"]]
        with self.assertRaises(ValueError):
            solve_boolean(instance)

    def test_invalid_present_json_is_not_silently_ignored(self):
        with TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "exam.txt"
            path.write_text((ROOT / "instances" / "sat1.txt").read_text(), encoding="utf-8")
            path.with_suffix(".extra.json").write_text("{invalid", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_file(path)


if __name__ == "__main__":
    unittest.main()
