"""Regression tests for the safe integration refactor."""

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path

from shared_input import Instance, validate_and_index

ROOT = Path(__file__).resolve().parent.parent


def load_integer_solver():
    spec = importlib.util.spec_from_file_location("integer_refactor_test", ROOT / "Formulation1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RefactorRegressions(unittest.TestCase):
    def test_shared_index_deduplicates_registrations(self):
        instance = Instance()
        instance.number_of_students = 2
        instance.number_of_exams = 2
        instance.number_of_slots = 3
        instance.number_of_rooms = 1
        instance.room_capacities = [2]
        instance.exams_to_students = [(0, 0), (0, 0), (1, 0), (1, 1)]
        exam_students, student_exams = validate_and_index(instance)
        self.assertEqual(exam_students, [{0}, {0, 1}])
        self.assertEqual(student_exams, [{0, 1}, {1}])

    def test_shared_index_rejects_invalid_registrations(self):
        instance = Instance()
        instance.number_of_students = 1
        instance.number_of_exams = 1
        instance.number_of_slots = 1
        instance.number_of_rooms = 1
        instance.room_capacities = [1]
        instance.exams_to_students = [(1, 0)]
        with self.assertRaises(ValueError):
            validate_and_index(instance)

    def test_integer_reporting_does_not_claim_unchecked_solution_is_unique(self):
        solver = load_integer_solver()
        result = {
            "status": "sat", "metadata_mode": "baseline",
            "timetable": [(0, 0, 0)], "alternative_exists": None,
            "solve_time_ms": 1, "build_time_ms": 1,
            "variable_count": 2, "constraint_count": 4,
        }
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            solver.print_result(result)
        self.assertIn("Alternative solutions not checked", output.getvalue())
        self.assertNotIn("Solution is unique", output.getvalue())


if __name__ == "__main__":
    unittest.main()
