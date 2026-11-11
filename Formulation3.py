"""COMP3070 formulation 3: hybrid integer-timeslot / Boolean-room encoding.

C1: exactly one slot and one room per exam.
C2: at most one exam per (room, slot).
C3: sufficient room capacity.
C4: no consecutive exams for a student.
C5: no simultaneous exams for a student.
C6: total exams in each timeslot <= max_exams_per_slot.
C7: every required exam facility is available in the chosen room.
C8: each exam's duration fits the chosen timeslot.

Requires the UPDATED shared_input.py from the C1-C8 package. Time-slot
indices are zero-based and consecutive indices represent consecutive slots.
"""

import argparse
from itertools import combinations
from pathlib import Path
from time import perf_counter

import z3
from shared_input import Instance, read_file, validate_and_index


def solve_hybrid(instance, check_alternatives=False):
    """Return a result dictionary compatible with Formulation1/2.

    Decision variables: E integer timeslots t[e] and E*R Boolean room
    selectors y[e,r]. The slot-domain constraints and exactly-one-room
    constraints jointly enforce C1 without an extra room integer.
    """
    start_build = perf_counter()
    exam_students, student_exams = validate_and_index(instance)
    E = instance.number_of_exams
    T = instance.number_of_slots
    R = instance.number_of_rooms

    solver = z3.Solver()
    t = [z3.Int(f"hybrid_slot_{e}") for e in range(E)]
    y = {(e, r): z3.Bool(f"hybrid_room_{e}_{r}")
         for e in range(E) for r in range(R)}

    # C1: a valid timeslot and exactly one selected room for each exam.
    for e in range(E):
        solver.add(t[e] >= 0, t[e] < T)
        selectors = [y[e, r] for r in range(R)]
        if selectors:
            solver.add(z3.PbEq([(v, 1) for v in selectors], 1))
        else:
            solver.add(z3.BoolVal(False))

    # C2: if two exams select the same room, their slots must differ.
    for a, b in combinations(range(E), 2):
        for r in range(R):
            solver.add(z3.Implies(z3.And(y[a, r], y[b, r]), t[a] != t[b]))

    # C3 and C7: remove ineligible room selectors using fixed input data.
    for e in range(E):
        for r in range(R):
            if len(exam_students[e]) > instance.room_capacities[r]:
                solver.add(z3.Not(y[e, r]))
            if not instance.exam_requirements[e].issubset(instance.room_facilities[r]):
                solver.add(z3.Not(y[e, r]))

    # C4, C5: pairwise conflicts are sufficient for all student enrolments.
    conflicts = set()
    for registered in student_exams:
        conflicts.update(combinations(sorted(registered), 2))
    for a, b in sorted(conflicts):
        solver.add(t[a] - t[b] != 1, t[b] - t[a] != 1)  # C4
        solver.add(t[a] != t[b])  # C5

    # C6: one counted exam per timeslot, independent of room selection.
    for slot in range(T):
        solver.add(z3.Sum([z3.If(t[e] == slot, 1, 0) for e in range(E)])
                   <= instance.max_exams_per_slot)

    # C8: each selected slot must have sufficient duration.
    for e in range(E):
        for slot in range(T):
            if instance.exam_durations[e] > instance.slot_durations[slot]:
                solver.add(t[e] != slot)

    build_time_ms = (perf_counter() - start_build) * 1000
    start_check = perf_counter()
    status = solver.check()
    solve_time_ms = (perf_counter() - start_check) * 1000
    timetable = None
    alternative_exists = None
    if status == z3.sat:
        model = solver.model()
        timetable = []
        for e in range(E):
            selected_room = next(r for r in range(R)
                                 if z3.is_true(model.eval(y[e, r], model_completion=True)))
            timetable.append((e, model.eval(t[e], model_completion=True).as_long(), selected_room))
        if check_alternatives:
            # Block all assignments as a complete model, not just the slots.
            # Empty timetable has exactly one valid assignment.
            if E == 0:
                alternative_exists = False
            else:
                block = []
                for e, slot, room in timetable:
                    block.append(t[e] != slot)
                    block.append(z3.Not(y[e, room]))
                solver.push()
                solver.add(z3.Or(block))
                second = solver.check()
                alternative_exists = (True if second == z3.sat else
                                      False if second == z3.unsat else None)
                solver.pop()

    return {
        "status": str(status),
        "timetable": timetable,
        "solve_time_ms": solve_time_ms,
        "build_time_ms": build_time_ms,
        "variable_count": len(t) + len(y),
        "constraint_count": len(solver.assertions()),
        "reason_unknown": solver.reason_unknown() if status == z3.unknown else None,
        "metadata_mode": instance.metadata_mode,
        "alternative_exists": alternative_exists,
    }


def print_result(result):
    """Display status, timetable and reproducible runtime measurements."""
    print(result["status"])
    if result["metadata_mode"] == "baseline":
        print("Data mode: baseline (neutral C6/C7/C8 defaults)")
    else:
        print("Data mode: extended (C6/C7/C8 metadata)")
    if result["status"] == "sat":
        print("Exam\tTimeslot\tRoom")
        for exam, slot, room in result["timetable"]:
            print(f"{exam}\t{slot}\t{room}")
        if result["alternative_exists"] is True:
            print("Multiple solutions exist")
        elif result["alternative_exists"] is False:
            print("Solution is unique")
    elif result["status"] == "unknown":
        print(f'Reason: {result["reason_unknown"]}')
    print(f'Solving time (ms): {result["solve_time_ms"]:.3f}')
    print(f'Model construction time (ms): {result["build_time_ms"]:.3f}')
    print(f'Decision variables: {result["variable_count"]}')
    print(f'Z3 assertions: {result["constraint_count"]}')


def solve(instance):
    """Coursework entry point: solve the instance and print its timetable."""
    result = solve_hybrid(instance, check_alternatives=True)
    print_result(result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filename", nargs="?", default=Path(__file__).parent / "instances" / "sat1.txt")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--metadata", help="Companion JSON file with C6-C8 metadata")
    group.add_argument("--baseline", action="store_true", help="Ignore companion metadata")
    parser.add_argument("--check-alternatives", action="store_true", help="Check if another timetable exists")
    args = parser.parse_args()
    try:
        result = solve_hybrid(read_file(args.filename, args.metadata, baseline=args.baseline),
                              check_alternatives=args.check_alternatives)
    except (OSError, ValueError) as error:
        raise SystemExit(f"Input error: {error}") from error
    print_result(result)
