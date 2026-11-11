"""Z3 integer formulation for the COMP3070 exam-timetabling coursework.

The coursework asks for five main constraints and at least three additional
constraints. This implementation labels them C1-C8:

Main constraints:
    C1  exactly one (timeslot, room) assignment per exam;
    C2  at most one exam per (room, timeslot);
    C3  enrolment does not exceed room capacity;
    C4  student exams cannot occupy adjacent slots;
    C5  student exams cannot occupy the same slot.

Additional constraints:
    C6  each slot holds at most max_exams_per_slot exams;
    C7  each room meets the assigned exam's facility requirements;
    C8  each exam fits within its assigned slot's duration.

C1 is represented by exactly two bounded integer variables per exam:
    slot[e] in {0, ..., T-1}, room[e] in {0, ..., R-1}.

Every loop below instantiates a finite mathematical constraint for the
corresponding exams, rooms or slots. The resulting quantifier-free formulas
are submitted to Z3's integer solver. The input parser and optional C7/C8
metadata are shared with the Boolean and Hybrid formulations.
"""

import argparse
from itertools import combinations
from pathlib import Path
from time import perf_counter

import z3

from shared_input import Instance, read_file, validate_and_index as index_instance


def validate_and_index(instance):
    """Return distinct exam enrolments and shared-student exam pairs.

    The input validation is shared with the Boolean formulation, while this
    encoding keeps its own pair-based constraints for C4 and C5.
    """
    exam_students, student_exams = index_instance(instance)
    pairs = set()
    for registered in student_exams:
        pairs.update(combinations(sorted(registered), 2))
    return [len(students) for students in exam_students], sorted(pairs)


def add_c1_domains(solver, slot, room, n_slots, n_rooms):
    """Apply the finite domains for the two integer decisions per exam.

    Each exam has one integer ``slot[e]`` and one integer ``room[e]``. The
    bounds make each value a valid assignment, while the single value of each
    variable represents the required one-slot/one-room allocation.
    """
    for s, r in zip(slot, room):
        solver.add(s >= 0, s < n_slots, r >= 0, r < n_rooms)


def add_c2_room_clash(solver, slot, room):
    """Prevent two different exams sharing a room and slot.

    For every pair ``a < b`` this adds
    ``room[a] != room[b] OR slot[a] != slot[b]``, which is the Z3 form of
    ``room[a] = room[b] -> slot[a] != slot[b]``.
    """
    for a, b in combinations(range(len(slot)), 2):
        solver.add(z3.Or(room[a] != room[b], slot[a] != slot[b]))


def add_c3_capacity(solver, room, enrolment, capacities):
    """Reject rooms whose capacity is smaller than the exam enrolment."""
    for e, n in enumerate(enrolment):
        for r, cap in enumerate(capacities):
            if cap < n:
                solver.add(room[e] != r)


def add_c4_no_consecutive(solver, slot, pairs):
    """Prevent a student from sitting exams in adjacent slot indices.

    For each pair of exams sharing a student, both directed differences are
    excluded. Together they are equivalent to
    ``abs(slot[a] - slot[b]) != 1`` without introducing an absolute-value
    expression.
    """
    for a, b in pairs:
        solver.add(slot[a] - slot[b] != 1, slot[b] - slot[a] != 1)


def add_c5_no_same_slot(solver, slot, pairs):
    """A student must not sit multiple exams in the same slot."""
    for a, b in pairs:
        solver.add(slot[a] != slot[b])


def add_c6_slot_limit(solver, slot, n_slots, max_exams_per_slot):
    """C6: at most the configured number of exams run in each timeslot."""
    for t in range(n_slots):
        solver.add(z3.Sum([z3.If(s == t, 1, 0) for s in slot]) <= max_exams_per_slot)


def add_c7_facilities(solver, room, instance):
    """Additional constraint: the room must contain every required facility.

    If the requirement set for exam ``e`` is not a subset of room ``r``'s
    facilities, the assignment ``room[e] == r`` is forbidden.
    """
    for e in range(instance.number_of_exams):
        for r in range(instance.number_of_rooms):
            if not instance.exam_requirements[e].issubset(instance.room_facilities[r]):
                solver.add(room[e] != r)


def add_c8_duration(solver, slot, instance):
    """Additional constraint: an exam must fit in its selected slot.

    Equality between exam duration and slot duration is valid; only shorter
    slots are removed from an exam's domain.
    """
    for e in range(instance.number_of_exams):
        for t in range(instance.number_of_slots):
            if instance.exam_durations[e] > instance.slot_durations[t]:
                solver.add(slot[e] != t)


def verify(instance, timetable):
    """Independently check a returned timetable against all eight constraints.

    This checker deliberately uses ordinary Python rather than Z3. It provides
    an implementation-independent validation of SAT models, including the
    additional facility and duration restrictions. An empty error list means
    that the timetable is valid.
    """
    errors = []
    enrolment, pairs = validate_and_index(instance)
    where = {}
    for e, t, r in timetable:
        if e in where:
            errors.append(f"C1: exam {e} appears more than once")
        where[e] = (t, r)
    if sorted(where) != list(range(instance.number_of_exams)):
        errors.append("C1: not every exam is scheduled exactly once")
        return errors

    used = {}
    for e, (t, r) in where.items():
        if not 0 <= t < instance.number_of_slots:
            errors.append(f"C1: exam {e} slot {t} out of range")
            continue
        if not 0 <= r < instance.number_of_rooms:
            errors.append(f"C1: exam {e} room {r} out of range")
            continue
        if (t, r) in used:
            errors.append(f"C2: exams {used[(t, r)]} and {e} share room {r} in slot {t}")
        used[(t, r)] = e
        if instance.room_capacities[r] < enrolment[e]:
            errors.append(f"C3: exam {e} ({enrolment[e]} students) exceeds room {r}")
        if not instance.exam_requirements[e].issubset(instance.room_facilities[r]):
            errors.append(f"C7: room {r} lacks facilities for exam {e}")
        if instance.exam_durations[e] > instance.slot_durations[t]:
            errors.append(f"C8: exam {e} does not fit slot {t}")
    by_slot = {}
    for e, (t, _) in where.items():
        by_slot[t] = by_slot.get(t, 0) + 1
    for t, count in by_slot.items():
        if count > instance.max_exams_per_slot:
            errors.append(f"C6: slot {t} has {count} exams; max is {instance.max_exams_per_slot}")
    for a, b in pairs:
        d = abs(where[a][0] - where[b][0])
        if d == 1:
            errors.append(f"C4: exams {a} and {b} share a student and are in adjacent slots")
        elif d == 0:
            errors.append(f"C5: exams {a} and {b} share a student and the same slot")
    return errors


def solve_integer(instance, check_alternatives=False):
    """Build and solve the integer formulation, returning coursework results.

    ``status`` is ``sat``, ``unsat`` or ``unknown``. For ``sat``, ``timetable``
    contains one ``(exam, slot, room)`` tuple per exam; for ``unsat`` it is
    ``None``. The timing fields separate model construction from the
    ``solver.check()`` call, and the latter is reported in milliseconds as
    required by the coursework.

    If ``check_alternatives`` is enabled, the first model is temporarily
    blocked and Z3 is asked for a second model. ``alternative_exists`` is
    therefore a direct test for more than one timetable and is not included
    in the primary solving-time measurement.
    """
    build_start = perf_counter()
    enrolment, pairs = validate_and_index(instance)

    exams = instance.number_of_exams
    slot = [z3.Int(f"slot_{e}") for e in range(exams)]
    room = [z3.Int(f"room_{e}") for e in range(exams)]

    solver = z3.Solver()
    add_c1_domains(solver, slot, room, instance.number_of_slots, instance.number_of_rooms)
    add_c2_room_clash(solver, slot, room)
    add_c3_capacity(solver, room, enrolment, instance.room_capacities)
    add_c4_no_consecutive(solver, slot, pairs)
    add_c5_no_same_slot(solver, slot, pairs)
    add_c6_slot_limit(solver, slot, instance.number_of_slots, instance.max_exams_per_slot)
    add_c7_facilities(solver, room, instance)
    add_c8_duration(solver, slot, instance)
    build_time_ms = (perf_counter() - build_start) * 1000

    check_start = perf_counter()
    status = solver.check()
    solve_time_ms = (perf_counter() - check_start) * 1000

    timetable, alternative = None, None
    if status == z3.sat:
        model = solver.model()
        value = lambda v: model.eval(v, model_completion=True).as_long()
        timetable = [(e, value(slot[e]), value(room[e])) for e in range(exams)]
        if check_alternatives and exams > 0:
            # Block the complete first assignment, then search for another one.
            solver.push()
            solver.add(z3.Or([v != model.eval(v, model_completion=True) for v in slot + room]))
            alternative_status = solver.check()
            alternative = (
                True if alternative_status == z3.sat else
                False if alternative_status == z3.unsat else None
            )
            solver.pop()
        elif check_alternatives:
            alternative = False

    return {
        "status": str(status),
        "timetable": timetable,
        "solve_time_ms": solve_time_ms,
        "build_time_ms": build_time_ms,
        "variable_count": len(slot) + len(room),
        "constraint_count": len(solver.assertions()),
        "reason_unknown": solver.reason_unknown() if status == z3.unknown else None,
        "metadata_mode": instance.metadata_mode,
        "alternative_exists": alternative,
    }


def print_result(result):
    """Print the coursework output: sat/unsat, the timetable, then the solving time in ms."""
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
        else:
            print("Alternative solutions not checked")
    elif result["status"] == "unknown":
        print(f'Reason: {result["reason_unknown"]}')
    print(f'Solving time (ms): {result["solve_time_ms"]:.3f}')
    print(f'Model construction time (ms): {result["build_time_ms"]:.3f}')
    print(f'Decision variables: {result["variable_count"]}')
    print(f'Z3 assertions: {result["constraint_count"]}')


def solve(instance):
    """Entry point required by the coursework template: solve(instance).

    Solves the instance with the integer formulation, prints sat/unsat, the
    timetable and the solving time in milliseconds, and returns the result dictionary.
    """
    result = solve_integer(instance, check_alternatives=True)
    print_result(result)
    return result


def run_one(path, metadata, baseline):
    """Read one instance file and solve it, as the template's __main__ does."""
    return solve(read_file(path, metadata, baseline=baseline))


def default_instance_path():
    """Template behaviour: with no argument use sat1.txt (current folder, script folder, or instances/)."""
    here = Path(__file__).resolve().parent
    for candidate in (Path("sat1.txt"), here / "sat1.txt", here / "instances" / "sat1.txt"):
        if candidate.is_file():
            return str(candidate)
    return "sat1.txt"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("filename", nargs="?", default=default_instance_path(),
                        help="instance .txt file (default: sat1.txt)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--metadata", help="Explicit companion JSON path")
    group.add_argument("--baseline", action="store_true", help="Ignore metadata and use neutral defaults")
    args = parser.parse_args()
    try:
        run_one(args.filename, args.metadata, args.baseline)
    except (OSError, ValueError) as error:
        raise SystemExit(f"Input error: {error}") from error