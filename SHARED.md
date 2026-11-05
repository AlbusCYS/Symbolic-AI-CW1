## Load an instance

```python
from shared_input import read_file, prepare_metadata
from timetable_check import validate_timetable

instance = read_file("examples/sat_combined_gap.txt")
```

Use the same input data for both solvers. read_file reads the original text file and a companion with the same stem and the .extra.json suffix. An explicit metadata path can be passed as the second argument. Enrolment records are (exam_id, student_id). All IDs are zero-based.

For E exams, R rooms and T slots, the four required JSON fields are:

| Field | Shape | Meaning |
|---|---|---|
| exam_requirements | E lists of strings | All facilities each exam requires |
| room_facilities | R lists of strings | Facilities each room supplies |
| exam_durations | E positive integers | Exam lengths in minutes |
| slot_durations | T positive integers | Slot lengths in minutes |

The shared loader converts the facility lists to Python sets. Names match exactly and are case-sensitive; use consistent names such as computers and projector. Empty requirement sets permit any room under C7. Extra room facilities are allowed. All four fields must be supplied together; dimensions, names and durations are validated. Input errors raise ValueError or an appropriate file error, rather than being reported as UNSAT.

## Constraint definitions

For every exam e, room r and ordered slot t:

- C7: assigning e to r implies exam_requirements[e] is a subset of room_facilities[r]. Every requirement must be present. Capacity C4 still applies separately.
- C8: assigning e to t implies exam_durations[e] <= slot_durations[t]. Equality is allowed. Exam and slot durations are fixed data, not solver decisions.
- C1/C2 still assign one slot and one room. Exams cannot span slots or split across rooms. A short exam still occupies that room-slot pair, so C3 still forbids another exam in that room and slot.
- C5 refers to adjacent slot indices, not elapsed minutes. C6 separately forbids simultaneous student exams. Varying slot lengths does not alter either rule.

The integer coder can use these clauses after declaring bounded room[e] and slot[e] variables:

```python
prepare_metadata(instance)
for e in range(instance.number_of_exams):
    for r in range(instance.number_of_rooms):
        if not instance.exam_requirements[e].issubset(instance.room_facilities[r]):
            solver.add(room[e] != r)
    for t in range(instance.number_of_slots):
        if instance.exam_durations[e] > instance.slot_durations[t]:
            solver.add(slot[e] != t)
```

The Boolean solver asserts Not(X[e,t,r]) for each forbidden assignment. Both encodings exclude the same choices.

## Original-file baseline

When metadata is absent, the loader supplies synthetic neutral values: no required facilities, no listed room facilities, 60-minute exams and 120-minute slots. metadata_mode is baseline. C7 and C8 are nonbinding, preserving the C1-C6 feasible set.

Present but incomplete or invalid metadata is rejected. A requested metadata file that does not exist is an error. Valid metadata with no eligible room or slot is a legitimate UNSAT instance. read_file(path, baseline=True) deliberately ignores companion metadata for comparison.

## Results and comparison

The Boolean solver returns a dictionary containing status, timetable, solve_time_ms, build_time_ms, variable_count, constraint_count, reason_unknown and metadata_mode. The timetable is a list of (exam_id, slot_id, room_id) triples for SAT, or None otherwise. No exams produces an empty SAT timetable. Keep unknown distinct from unsat.

Use the same result structure for the integer solver. Measure solver.check() alone for solve_time_ms. Construction time includes validation, preprocessing and model construction; it excludes solving and decoding. A Boolean variable count is E*T*R; integer assignment variables are normally 2*E, excluding any auxiliaries. constraint_count means top-level Z3 assertions and depends on grouping; it is not an internal clause count.

Check SAT timetables with validate_timetable(instance, result["timetable"]). The checker is independent of the Z3 model. Compare satisfiability and schedule validity; different valid schedules are acceptable. Use identical files, metadata, Z3 version and runtime for comparisons.

The eight synthetic cases in examples have SAT/UNSAT expectations indicated by their filenames. The original Moodle filename labels apply to the baseline model; additional restrictions may change an extended instance's result.
