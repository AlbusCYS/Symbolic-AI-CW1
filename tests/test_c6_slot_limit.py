"""Targeted C6 tests for both genuinely different Z3 formulations."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from Formulation1 import solve_integer
from Formulation2 import solve_boolean
from shared_input import Instance, read_file, prepare_metadata
from timetable_check import validate_timetable


def example(slots=1, limit=2, exams=2, rooms=3, shared_student=False):
    instance = Instance()
    instance.number_of_exams = exams
    instance.number_of_students = exams if not shared_student else 1
    instance.number_of_slots = slots
    instance.number_of_rooms = rooms
    instance.room_capacities = [10] * rooms
    instance.exams_to_students = [(e, 0 if shared_student else e) for e in range(exams)]
    instance.max_exams_per_slot = limit
    return prepare_metadata(instance)


class C6SlotLimitTests(unittest.TestCase):
    def assert_status(self, instance, expected):
        for solve in (solve_integer, solve_boolean):
            with self.subTest(formulation=solve.__name__):
                result = solve(instance)
                self.assertEqual(result['status'], expected)
                if expected == 'sat':
                    validate_timetable(instance, result['timetable'])

    def test_c6_changes_satisfiability_even_with_free_rooms(self):
        self.assert_status(example(slots=1, limit=1), 'unsat')
        self.assert_status(example(slots=1, limit=2), 'sat')

    def test_c6_can_spread_exams_over_multiple_slots(self):
        self.assert_status(example(slots=2, limit=1), 'sat')

    def test_zero_limit_is_unsat_for_nonempty_problem(self):
        self.assert_status(example(slots=2, limit=0, exams=1), 'unsat')

    def test_default_is_room_count_and_does_not_break_baseline(self):
        instance = example(slots=1, limit=None, exams=3, rooms=3)
        self.assertEqual(instance.max_exams_per_slot, 3)
        self.assert_status(instance, 'sat')

    def test_invalid_limit_rejected(self):
        for value in (-1, 1.5, True, '2'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    example(limit=value)

    def test_student_clash_still_works_independently(self):
        self.assert_status(example(slots=1, limit=3, shared_student=True), 'unsat')

    def test_checker_rejects_overloaded_slot(self):
        instance = example(slots=1, limit=1)
        with self.assertRaisesRegex(AssertionError, 'C6'):
            validate_timetable(instance, [(0, 0, 0), (1, 0, 1)])

    def test_json_limit_round_trip(self):
        data = ("Number of students: 2\nNumber of exams: 2\n"
                "Number of slots: 1\nNumber of rooms: 3\n"
                "Room 0 capacity: 10\nRoom 1 capacity: 10\nRoom 2 capacity: 10\n"
                "0 0\n1 1\n")
        meta = dict(exam_requirements=[[], []], room_facilities=[[], [], []],
                    exam_durations=[60, 60], slot_durations=[120], max_exams_per_slot=1)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'example.txt'
            path.write_text(data, encoding='utf-8')
            path.with_suffix('.extra.json').write_text(json.dumps(meta), encoding='utf-8')
            self.assert_status(read_file(path), 'unsat')
            self.assert_status(read_file(path, baseline=True), 'sat')


if __name__ == '__main__':
    unittest.main()
