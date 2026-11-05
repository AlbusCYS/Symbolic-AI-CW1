"""Focused extension tests; all facilities and durations here are synthetic."""

import itertools
import random
import unittest

from formulation2 import read_file, solve_boolean
from tests.test_formulation2 import ROOT, make_instance
from timetable_check import validate_timetable


def with_metadata(instance, requirements, facilities, durations, slot_lengths):
    instance.exam_requirements = requirements
    instance.room_facilities = facilities
    instance.exam_durations = durations
    instance.slot_durations = slot_lengths
    return instance


def exhaustive_status(instance):
    """Try every allocation for tiny cases, checking the actual timetable."""
    choices = list(itertools.product(
        range(instance.number_of_slots), range(instance.number_of_rooms)
    ))
    for allocation in itertools.product(choices, repeat=instance.number_of_exams):
        timetable = [(e, t, r) for e, (t, r) in enumerate(allocation)]
        try:
            validate_timetable(instance, timetable)
        except AssertionError:
            continue
        return "sat"
    return "unsat"


class ExtensionTests(unittest.TestCase):
    def check_result(self, instance, expected):
        result = solve_boolean(instance)
        self.assertEqual(result["status"], expected)
        if expected == "sat":
            validate_timetable(instance, result["timetable"])
        else:
            self.assertIsNone(result["timetable"])
        return result

    def test_saved_extended_examples(self):
        paths = sorted((ROOT / "examples").glob("*.txt"))
        self.assertEqual(len(paths), 8)
        for path in paths:
            with self.subTest(example=path.name):
                self.assertTrue(path.with_suffix(".extra.json").is_file())
                instance = read_file(path)
                self.assertEqual(instance.metadata_mode, "extended")
                expected = "unsat" if path.stem.startswith("unsat") else "sat"
                self.check_result(instance, expected)

    def test_c7_requires_every_feature_and_allows_extra_features(self):
        instance = with_metadata(
            make_instance(1, 1, [1, 1], [(0, 0)]),
            [["computers", "projector"]],
            [["computers"], ["computers", "projector", "whiteboard"]],
            [60], [120],
        )
        result = self.check_result(instance, "sat")
        self.assertEqual(result["timetable"], [(0, 0, 1)])

    def test_c7_missing_facility_is_unsat(self):
        instance = with_metadata(
            make_instance(1, 1, [1], [(0, 0)]),
            [["computers"]], [["projector"]], [60], [120],
        )
        self.check_result(instance, "unsat")

    def test_c7_partial_requirements_are_insufficient(self):
        instance = with_metadata(
            make_instance(1, 1, [1, 1], [(0, 0)]),
            [["computers", "projector"]],
            [["computers"], ["projector"]], [60], [120],
        )
        self.check_result(instance, "unsat")

    def test_c7_empty_requirements_allow_a_room_without_facilities(self):
        instance = with_metadata(
            make_instance(1, 1, [1], [(0, 0)]), [[]], [[]], [60], [120],
        )
        self.check_result(instance, "sat")

    def test_c7_feature_matching_is_case_sensitive(self):
        instance = with_metadata(
            make_instance(1, 1, [1], [(0, 0)]),
            [["computers"]], [["Computers"]], [60], [120],
        )
        self.check_result(instance, "unsat")

    def test_c8_forces_a_long_enough_slot(self):
        instance = with_metadata(
            make_instance(1, 2, [1], [(0, 0)]), [[]], [[]], [90], [60, 120],
        )
        result = self.check_result(instance, "sat")
        self.assertEqual(result["timetable"], [(0, 1, 0)])

    def test_c8_exact_fit_is_allowed(self):
        instance = with_metadata(
            make_instance(1, 1, [1], [(0, 0)]), [[]], [[]], [90], [90],
        )
        self.check_result(instance, "sat")

    def test_c8_exam_cannot_span_two_short_slots(self):
        instance = with_metadata(
            make_instance(1, 2, [1], [(0, 0)]), [[]], [[]], [121], [60, 120],
        )
        self.check_result(instance, "unsat")

    def test_c7_does_not_override_capacity(self):
        instance = with_metadata(
            make_instance(1, 1, [1, 2], [(0, 0), (0, 1)]),
            [["computers"]], [["computers"], []], [60], [120],
        )
        self.check_result(instance, "unsat")

    def test_c8_does_not_override_student_gap(self):
        instance = with_metadata(
            make_instance(2, 3, [1], [(0, 0), (1, 0)]),
            [[], []], [[]], [90, 60], [60, 90, 120],
        )
        result = self.check_result(instance, "sat")
        self.assertEqual(result["timetable"], [(0, 2, 0), (1, 0, 0)])

    def test_c7_c8_combination_can_exclude_all_timetables(self):
        def case(requirements, slot_lengths):
            return with_metadata(
                make_instance(2, 2, [1, 1], [(0, 0), (1, 1)]),
                requirements, [["computers"], []], [90, 90], slot_lengths,
            )
        self.check_result(case([["computers"], ["computers"]], [120, 120]), "sat")
        self.check_result(case([[], []], [60, 120]), "sat")
        self.check_result(case([["computers"], ["computers"]], [60, 120]), "unsat")

    def test_independent_checker_rejects_c7_and_c8_violations(self):
        instance = with_metadata(
            make_instance(1, 2, [1, 1], [(0, 0)]),
            [["computers"]], [[], ["computers"]], [90], [60, 120],
        )
        for timetable in ([(0, 1, 0)], [(0, 0, 1)]):
            with self.subTest(timetable=timetable):
                with self.assertRaises(AssertionError):
                    validate_timetable(instance, timetable)

    def test_tiny_extended_cases_match_exhaustive_search(self):
        rng = random.Random(307008)
        for case in range(48):
            students, exams = rng.randrange(3), rng.randrange(4)
            slots, rooms = rng.randrange(4), rng.randrange(3)
            features = ["computers", "projector"]
            instance = with_metadata(
                make_instance(
                    exams, slots, [rng.randrange(students + 1) for _ in range(rooms)],
                    [(e, s) for e in range(exams) for s in range(students)
                     if rng.randrange(2)], students=students,
                ),
                [[f for f in features if rng.randrange(2)] for _ in range(exams)],
                [[f for f in features if rng.randrange(2)] for _ in range(rooms)],
                [rng.choice([60, 90, 120]) for _ in range(exams)],
                [rng.choice([60, 90, 120]) for _ in range(slots)],
            )
            with self.subTest(case=case):
                self.check_result(instance, exhaustive_status(instance))


if __name__ == "__main__":
    unittest.main()
