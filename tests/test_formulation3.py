"""Independent correctness and regression tests for hybrid Formulation 3."""
import itertools
import random
import unittest
from pathlib import Path

from Formulation3 import solve_hybrid
from shared_input import Instance, read_file
from timetable_check import validate_timetable

ROOT = Path(__file__).resolve().parent.parent


def make_instance(exams, slots, capacities, registrations=(), students=None):
    inst = Instance()
    inst.number_of_exams = exams
    inst.number_of_slots = slots
    inst.number_of_rooms = len(capacities)
    inst.number_of_students = students if students is not None else max((s for _, s in registrations), default=-1) + 1
    inst.room_capacities = list(capacities)
    inst.exams_to_students = list(registrations)
    return inst


def oracle(inst):
    """Brute-force timetable checker for tiny cases; no Z3 involved."""
    choices = list(itertools.product(range(inst.number_of_slots), range(inst.number_of_rooms)))
    for allocations in itertools.product(choices, repeat=inst.number_of_exams):
        timetable = [(e, slot, room) for e, (slot, room) in enumerate(allocations)]
        try:
            validate_timetable(inst, timetable)
        except AssertionError:
            continue
        return "sat"
    return "unsat"


class HybridTests(unittest.TestCase):
    def check_case(self, inst, expected):
        result = solve_hybrid(inst)
        self.assertEqual(result["status"], expected)
        self.assertEqual(result["variable_count"], inst.number_of_exams * (1 + inst.number_of_rooms))
        if expected == "sat":
            validate_timetable(inst, result["timetable"])
        else:
            self.assertIsNone(result["timetable"])
        return result

    def test_empty_instance(self):
        self.assertEqual(self.check_case(make_instance(0, 0, [], students=0), "sat")["timetable"], [])

    def test_single_exam_and_alternative(self):
        inst = make_instance(1, 1, [1], [(0, 0)])
        self.check_case(inst, "sat")
        self.assertFalse(solve_hybrid(inst, check_alternatives=True)["alternative_exists"])
        inst = make_instance(1, 2, [1], [(0, 0)])
        self.assertTrue(solve_hybrid(inst, check_alternatives=True)["alternative_exists"])

    def test_missing_rooms_or_slots(self):
        self.check_case(make_instance(1, 0, [1]), "unsat")
        self.check_case(make_instance(1, 1, []), "unsat")

    def test_room_capacity_and_room_collision(self):
        self.check_case(make_instance(1, 1, [1], [(0, 0), (0, 1)]), "unsat")
        self.check_case(make_instance(2, 1, [1], [(0, 0), (1, 1)]), "unsat")

    def test_student_clashes_and_consecutive(self):
        regs = [(0, 0), (1, 0)]
        self.check_case(make_instance(2, 1, [1, 1], regs), "unsat")
        self.check_case(make_instance(2, 2, [1, 1], regs), "unsat")
        self.check_case(make_instance(2, 3, [1], regs), "sat")

    def test_c6_independent_of_room_limit(self):
        inst = make_instance(2, 1, [1, 1], [(0, 0), (1, 1)])
        inst.max_exams_per_slot = 1
        self.check_case(inst, "unsat")
        inst.max_exams_per_slot = 2
        self.check_case(inst, "sat")

    def test_c7_facilities(self):
        inst = make_instance(1, 1, [1, 1], [(0, 0)])
        inst.exam_requirements = [["computer"]]
        inst.room_facilities = [[], ["computer"]]
        inst.exam_durations = [60]
        inst.slot_durations = [120]
        result = self.check_case(inst, "sat")
        self.assertEqual(result["timetable"][0][2], 1)
        inst.room_facilities = [[], []]
        self.check_case(inst, "unsat")

    def test_c8_durations(self):
        inst = make_instance(1, 2, [1], [(0, 0)])
        inst.exam_requirements = [[]]
        inst.room_facilities = [[]]
        inst.exam_durations = [90]
        inst.slot_durations = [60, 120]
        self.assertEqual(self.check_case(inst, "sat")["timetable"][0][1], 1)
        inst.slot_durations = [60, 60]
        self.check_case(inst, "unsat")

    def test_all_official_instances(self):
        paths = sorted((ROOT / "instances").glob("*.txt"))
        self.assertEqual(len(paths), 20, "Expected 20 official coursework instances")
        for path in paths:
            with self.subTest(path=path.name):
                inst = read_file(path, baseline=True)
                self.check_case(inst, "unsat" if path.stem.startswith("unsat") else "sat")

    def test_all_extended_examples(self):
        paths = sorted((ROOT / "examples").glob("*.txt"))
        self.assertEqual(len(paths), 10, "Expected 10 extended examples")
        for path in paths:
            with self.subTest(path=path.name):
                self.check_case(read_file(path), "unsat" if path.stem.startswith("unsat") else "sat")

    def test_small_random_against_brute_force(self):
        rng = random.Random(307003)
        for i in range(45):
            exams, students, slots, rooms = (rng.randrange(4), rng.randrange(3), rng.randrange(4), rng.randrange(3))
            inst = make_instance(exams, slots, [rng.randrange(students + 1) for _ in range(rooms)],
                                 [(e, s) for e in range(exams) for s in range(students) if rng.randrange(2)], students)
            inst.max_exams_per_slot = rng.randrange(rooms + 1)
            with self.subTest(case=i):
                self.check_case(inst, oracle(inst))


if __name__ == "__main__":
    unittest.main()
