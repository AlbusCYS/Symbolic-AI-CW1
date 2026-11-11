"""Baseline checks and measurements for the C1-C8 Boolean formulation."""

import csv
import itertools
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import unittest

import z3

from Formulation2 import Instance, read_file, solve_boolean
from timetable_check import validate_timetable


ROOT = Path(__file__).resolve().parent.parent


def make_instance(exams, slots, capacities, registrations=(), students=None):
    instance = Instance()
    instance.number_of_students = (
        students if students is not None
        else max((s for _, s in registrations), default=-1) + 1
    )
    instance.number_of_exams = exams
    instance.number_of_slots = slots
    instance.number_of_rooms = len(capacities)
    instance.room_capacities = list(capacities)
    instance.exams_to_students = list(registrations)
    return instance


def exhaustive_status(instance):
    """Independent oracle for tiny instances only."""
    choices = list(itertools.product(
        range(instance.number_of_slots), range(instance.number_of_rooms)
    ))
    for allocation in itertools.product(
        choices, repeat=instance.number_of_exams
    ):
        timetable = [
            (exam, slot, room)
            for exam, (slot, room) in enumerate(allocation)
        ]
        try:
            validate_timetable(instance, timetable)
        except AssertionError:
            continue
        return "sat"
    return "unsat"


class BooleanSolverTests(unittest.TestCase):
    def check_sat(self, instance):
        result = solve_boolean(instance)
        self.assertEqual(result["status"], "sat")
        validate_timetable(instance, result["timetable"])
        self.assertGreaterEqual(result["solve_time_ms"], 0)
        self.assertGreaterEqual(result["build_time_ms"], 0)
        self.assertEqual(
            result["variable_count"],
            instance.number_of_exams
            * instance.number_of_slots
            * instance.number_of_rooms,
        )
        self.assertGreaterEqual(result["constraint_count"], 0)
        return result

    def check_unsat(self, instance):
        result = solve_boolean(instance)
        self.assertEqual(result["status"], "unsat")
        self.assertIsNone(result["timetable"])

    def test_single_exam_is_scheduled(self):
        self.check_sat(make_instance(1, 1, [2], [(0, 0), (0, 1)]))

    def test_each_exam_has_exactly_one_slot_and_room(self):
        self.check_sat(make_instance(3, 4, [1, 2], [(0, 0), (1, 1), (2, 2)]))

    def test_room_cannot_host_two_exams_in_one_slot(self):
        self.check_unsat(make_instance(2, 1, [2], [(0, 0), (1, 1)]))

    def test_room_can_be_reused_in_different_slots(self):
        self.check_sat(make_instance(2, 2, [1], [(0, 0), (1, 1)]))

    def test_capacity_below_enrolment_is_unsat(self):
        self.check_unsat(make_instance(1, 2, [1], [(0, 0), (0, 1)]))

    def test_capacity_exactly_equal_to_enrolment_is_sat(self):
        self.check_sat(make_instance(1, 2, [2], [(0, 0), (0, 1)]))

    def test_student_clash_is_forbidden_across_different_rooms(self):
        self.check_unsat(make_instance(2, 1, [1, 1], [(0, 0), (1, 0)]))

    def test_consecutive_slots_are_forbidden(self):
        self.check_unsat(make_instance(2, 2, [1, 1], [(0, 0), (1, 0)]))

    def test_one_slot_gap_between_student_exams_is_allowed(self):
        result = self.check_sat(
            make_instance(2, 3, [1], [(0, 0), (1, 0)])
        )
        self.assertEqual(
            sorted(slot for _, slot, _ in result["timetable"]), [0, 2]
        )

    def test_duplicate_registration_counts_one_student(self):
        self.check_sat(make_instance(1, 1, [1], [(0, 0), (0, 0)]))

    def test_exam_with_no_students_still_gets_an_assignment(self):
        self.check_sat(make_instance(1, 1, [0], students=0))

    def test_no_exams_has_an_empty_sat_timetable(self):
        result = self.check_sat(make_instance(0, 0, [], students=0))
        self.assertEqual(result["timetable"], [])

    def test_exam_without_slots_or_rooms_is_unsat(self):
        for instance in (
            make_instance(1, 0, [1]),
            make_instance(1, 1, []),
        ):
            with self.subTest(slots=instance.number_of_slots,
                              rooms=instance.number_of_rooms):
                self.check_unsat(instance)

    def test_invalid_registration_ids_are_rejected(self):
        for registration in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            with self.subTest(registration=registration):
                instance = make_instance(1, 1, [1], [registration], students=1)
                with self.assertRaises(ValueError):
                    solve_boolean(instance)

    def test_invalid_counts_or_capacities_are_rejected(self):
        bad_count = make_instance(-1, 1, [1])
        bad_capacity = make_instance(1, 1, [-1])
        missing_capacity = make_instance(1, 1, [1])
        missing_capacity.number_of_rooms = 2
        for instance in (bad_count, bad_capacity, missing_capacity):
            with self.subTest(instance=vars(instance)):
                with self.assertRaises(ValueError):
                    solve_boolean(instance)

    def test_command_line_prints_sat_timetable_and_timing(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(z3.__file__).resolve().parent.parent)
        completed = subprocess.run(
            [sys.executable, str(ROOT / "Formulation2.py"),
             str(ROOT / "instances" / "sat1.txt")],
            capture_output=True, text=True, env=env, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.splitlines()[0], "sat")
        self.assertIn("0\t0\t0", completed.stdout)
        self.assertIn("Solving time (ms):", completed.stdout)

    def test_command_line_prints_unsat_without_a_timetable(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(z3.__file__).resolve().parent.parent)
        completed = subprocess.run(
            [sys.executable, str(ROOT / "Formulation2.py"),
             str(ROOT / "instances" / "unsat1.txt")],
            capture_output=True, text=True, env=env, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.splitlines()[0], "unsat")
        self.assertNotIn("Exam\tTimeslot\tRoom", completed.stdout)

    def test_tiny_instances_match_independent_exhaustive_search(self):
        rng = random.Random(3070)
        for case in range(48):
            students = rng.randrange(3)
            exams = rng.randrange(4)
            slots = rng.randrange(4)
            rooms = rng.randrange(3)
            instance = make_instance(
                exams, slots,
                [rng.randrange(students + 1) for _ in range(rooms)],
                [(e, s) for e in range(exams) for s in range(students)
                 if rng.randrange(2)],
                students=students,
            )
            with self.subTest(case=case, instance=vars(instance)):
                result = solve_boolean(instance)
                self.assertEqual(result["status"], exhaustive_status(instance))
                if result["status"] == "sat":
                    validate_timetable(instance, result["timetable"])

    def test_all_official_instances(self):
        paths = sorted((ROOT / "instances").glob("*.txt"))
        self.assertEqual(len(paths), 20)
        for path in paths:
            with self.subTest(instance=path.name):
                instance = read_file(path)
                expected = "unsat" if path.stem.startswith("unsat") else "sat"
                result = solve_boolean(instance)
                self.assertEqual(result["status"], expected)
                if result["status"] == "sat":
                    validate_timetable(instance, result["timetable"])


def benchmark():
    """Legacy per-formulation benchmark (use compare_three_formulations.py for final results)."""
    rows = []
    paths = sorted((ROOT / "instances").glob("*.txt"))
    paths += sorted((ROOT / "examples").glob("*.txt"))
    for path in paths:
        instance = read_file(path)
        result = solve_boolean(instance)
        expected = "unsat" if path.stem.startswith("unsat") else "sat"
        if result["status"] == "sat":
            validate_timetable(instance, result["timetable"])
        rows.append({
            "instance": path.relative_to(ROOT).as_posix(),
            "metadata_mode": result["metadata_mode"],
            "expected": expected,
            "status": result["status"],
            "matches_expected": result["status"] == expected,
            "solve_time_ms": result["solve_time_ms"],
            "build_time_ms": result["build_time_ms"],
            "variable_count": result["variable_count"],
            "constraint_count": result["constraint_count"],
            "python_version": platform.python_version(),
            "z3_version": z3.get_version_string(),
        })
        print(f'{path.name:12} {result["status"]:7} '
              f'{result["solve_time_ms"]:9.3f} ms  '
              f'{result["variable_count"]:4} Boolean variables')
    output = ROOT / "results" / "results_c1_c8_F2.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {output.name}; one check per instance.")
    if not all(row["matches_expected"] for row in rows):
        raise SystemExit("Some results differ from the supplied filename labels.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--benchmark"]:
        benchmark()
    else:
        unittest.main()
