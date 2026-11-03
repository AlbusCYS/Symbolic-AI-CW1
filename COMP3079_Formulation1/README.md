# COMP3070 Coursework 1 — Formulation 1

This folder contains the integer formulation of the COMP3070 exam
timetabling problem. The solver is implemented in Python using Z3's integer
solver.

## Requirements

- Python 3
- `z3-solver`

Install the dependency with:

```powershell
python -m pip install -r requirements.txt
```

## Running the solver

Run one instance:

```powershell
python "Formulation 1.py" instances\sat1.txt
```

Run an extended instance with facilities and duration metadata:

```powershell
python "Formulation 1.py" examples\sat_combined_gap.txt
```

Run every official instance in the `instances` folder:

```powershell
python "Formulation 1.py" instances
```

The command-line solver prints:

- `sat`, `unsat` or `unknown`;
- the timetable for a satisfiable instance;
- whether another solution exists;
- solving time in milliseconds;
- model-construction time;
- the number of integer variables; and
- the number of top-level Z3 assertions.

Use `--baseline` to ignore a companion metadata file:

```powershell
python "Formulation 1.py" examples\sat_combined_gap.txt --baseline
```

An explicit metadata file can be supplied with `--metadata`:

```powershell
python "Formulation 1.py" examples\sat_combined_gap.txt `
    --metadata examples\sat_combined_gap.extra.json
```

## Integer formulation

For each exam `e`, the solver creates two bounded integer variables:

```text
slot[e] ∈ {0, ..., number_of_slots - 1}
room[e] ∈ {0, ..., number_of_rooms - 1}
```

The constraints are:

### Main constraints

- **C1:** every exam is assigned exactly one timeslot;
- **C2:** every exam is assigned exactly one room;
- **C3:** a room cannot contain two exams in the same timeslot;
- **C4:** the room capacity must be at least the exam enrolment; and
- **C5:** a student cannot take exams in consecutive timeslots.

### Additional constraints

- **C6:** exams sharing a student cannot occur in the same timeslot;
- **C7:** the selected room must provide every facility required by the exam;
- **C8:** the exam duration must not exceed the selected slot duration.

C1 and C2 are represented by the single bounded value of each integer
variable. Invalid values are excluded with domain constraints.

## Input files

The original `.txt` format contains:

- number of students;
- number of exams;
- number of slots;
- number of rooms;
- capacity for each room; and
- exam/student registration pairs.

The original instances use neutral baseline metadata, so C7 and C8 do not
restrict those cases.

Extended examples use a companion file with the same stem and the
`.extra.json` suffix. For example:

```text
examples\sat_combined_gap.txt
examples\sat_combined_gap.extra.json
```

The JSON file must contain exactly these fields:

```json
{
  "exam_requirements": [["computers"]],
  "room_facilities": [["computers", "projector"]],
  "exam_durations": [90],
  "slot_durations": [120]
}
```

Facility names are case-sensitive. Durations must be positive integers, and
the list lengths must match the number of exams, rooms and slots.

## Project files

- `Formulation 1.py` — integer Z3 formulation and command-line interface.
- `shared_input.py` — instance parser and metadata validation.
- `timetable_check.py` — independent Python timetable validator.
- `test_formulation1.py` — integer solver tests and benchmark generation.
- `test_shared_input.py` — parser and metadata validation tests.
- `instances\` — the 20 official baseline instances.
- `examples\` — extended C7/C8 instances and companion JSON files.
- `requirements.txt` — Python dependency specification.
- `SHARED.md` — input and C7/C8 contract shared by the formulations.
- `results_c1_c8.csv` — recorded benchmark results for the supplied instances.

## Testing

Run the integer solver tests:

```powershell
python -m unittest -v test_formulation1.py
```

Run the shared-input tests:

```powershell
python -m unittest -v test_shared_input.py
```

Run both test groups:

```powershell
python -m unittest -v test_formulation1.py test_shared_input.py
```

Generate benchmark results for the official and extended examples:

```powershell
python test_formulation1.py --benchmark
```

The test suite checks SAT timetables with an independent Python validator and
compares randomly generated small cases against exhaustive search. It also
checks malformed counts, registrations, capacities, metadata and duration
values.

## Alternative solutions

When alternative checking is enabled, the solver first obtains a model, then
adds a constraint excluding the complete assignment of all `slot` and `room`
variables. A second satisfiable result proves that another timetable exists.
If the second check is unsatisfiable, the first timetable is unique with
respect to these decision variables.

This integer encoding can be compared with the Boolean formulation, where
each possible `(exam, slot, room)` assignment is represented by a Boolean
variable. The integer formulation uses two variables per exam and generally
has fewer declared variables, while the Boolean formulation makes each
possible assignment explicit.
