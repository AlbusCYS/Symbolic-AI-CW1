"""Boolean exam timetabling for the group's C1-C8 constraints.

X[e, t, r] means exam e uses timeslot t and room r. IDs are zero-based.
C7 requires all exam facilities; C8 fits each exam within its single slot.
Derived from the supplied Moodle template; the Boolean model and JSON
extension are additions. See SHARED.md for the common input contract.
"""

import argparse
from pathlib import Path
from time import perf_counter

import z3

# Re-export these names to preserve the earlier solver's import interface.
from shared_input import Instance, prepare_metadata, read_file, validate_and_index


def solve_boolean(instance):
    """Return status, timetable and measurements without printing.

    timetable is a list of (exam_id, slot_id, room_id) tuples for SAT,
    including an empty list when there are no exams, or None otherwise.
    constraint_count counts top-level Z3 assertions, not internal SAT clauses.
    solve_time_ms measures only solver.check().
    """
    build_start = perf_counter()
    students = instance.number_of_students
    exams = instance.number_of_exams
    slots = instance.number_of_slots
    rooms = instance.number_of_rooms

    exam_students, student_exams = validate_and_index(instance)

    solver = z3.Solver()
    X = {
        (exam, slot, room): z3.Bool(f"X_{exam}_{slot}_{room}")
        for exam in range(exams)
        for slot in range(slots)
        for room in range(rooms)
    }

    # C1 and C2: exactly one (timeslot, room) pair for every exam.
    for exam in range(exams):
        choices = [X[exam, slot, room]
                   for slot in range(slots) for room in range(rooms)]
        if choices:
            solver.add(z3.PbEq([(choice, 1) for choice in choices], 1))
        else:
            solver.add(False)

    # C3: a room can host at most one exam in a timeslot.
    if exams > 1:
        for slot in range(slots):
            for room in range(rooms):
                solver.add(z3.AtMost(
                    *[X[exam, slot, room] for exam in range(exams)], 1
                ))

    # C4: rule out assignments to rooms that cannot hold the enrolment.
    for exam in range(exams):
        for room in range(rooms):
            if len(exam_students[exam]) > instance.room_capacities[room]:
                for slot in range(slots):
                    solver.add(z3.Not(X[exam, slot, room]))

    # C7: every required facility must be present. These sets are fixed data;
    # Z3 chooses the assignment, not what facilities the room happens to have.
    for exam in range(exams):
        for room in range(rooms):
            if not instance.exam_requirements[exam].issubset(instance.room_facilities[room]):
                for slot in range(slots):
                    solver.add(z3.Not(X[exam, slot, room]))

    # C8: an exam must fit within one slot. Equality is allowed. C1/C2 still
    # prevent splitting across slots; C3 still reserves the room for the slot.
    for exam in range(exams):
        for slot in range(slots):
            if instance.exam_durations[exam] > instance.slot_durations[slot]:
                for room in range(rooms):
                    solver.add(z3.Not(X[exam, slot, room]))

    # These are Boolean expressions over X, not additional decision variables.
    in_slot = {
        (exam, slot): z3.Or(
            [X[exam, slot, room] for room in range(rooms)]
        )
        for exam in range(exams) for slot in range(slots)
    }
    for registered_exams in student_exams:
        if len(registered_exams) < 2:
            continue
        registered_exams = sorted(registered_exams)

        # C6: the student's exams cannot share a slot, even in different rooms.
        for slot in range(slots):
            solver.add(z3.AtMost(
                *[in_slot[exam, slot] for exam in registered_exams], 1
            ))

        # C5: the student cannot be busy in two adjacent ordered slots.
        busy = [
            z3.Or([in_slot[exam, slot] for exam in registered_exams])
            for slot in range(slots)
        ]
        for first, second in zip(busy, busy[1:]):
            solver.add(z3.Not(z3.And(first, second)))

    build_time_ms = (perf_counter() - build_start) * 1000
    check_start = perf_counter()
    status = solver.check()
    solve_time_ms = (perf_counter() - check_start) * 1000

    timetable = None
    if status == z3.sat:
        model = solver.model()
        timetable = [
            key for key, variable in X.items()
            if z3.is_true(model.eval(variable, model_completion=True))
        ]

    return {
        "status": str(status),
        "timetable": timetable,
        "solve_time_ms": solve_time_ms,
        "build_time_ms": build_time_ms,
        "variable_count": len(X),
        "constraint_count": len(solver.assertions()),
        "reason_unknown": solver.reason_unknown() if status == z3.unknown else None,
        "metadata_mode": instance.metadata_mode,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filename", nargs="?", default=Path(__file__).parent / "instances" / "sat1.txt")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--metadata", help="Explicit companion JSON path")
    group.add_argument("--baseline", action="store_true", help="Ignore metadata and use neutral defaults")
    args = parser.parse_args()
    try:
        result = solve_boolean(read_file(args.filename, args.metadata, baseline=args.baseline))
    except (OSError, ValueError) as error:
        raise SystemExit(f"Input error: {error}") from error
    print(result["status"])
    if result["metadata_mode"] == "baseline":
        print("Data mode: baseline (synthetic neutral defaults; C7/C8 are nonbinding)")
    else:
        print("Data mode: extended (facilities C7 and duration C8)")
    if result["status"] == "sat":
        print("Exam\tTimeslot\tRoom")
        for exam, slot, room in result["timetable"]:
            print(f"{exam}\t{slot}\t{room}")
    elif result["status"] == "unknown":
        print(f'Reason: {result["reason_unknown"]}')
    print(f'Solving time (ms): {result["solve_time_ms"]:.3f}')
    print(f'Model construction time (ms): {result["build_time_ms"]:.3f}')
    print(f'Boolean variables: {result["variable_count"]}')
    print(f'Z3 assertions: {result["constraint_count"]}')

