# COMP3070 Coursework 1 — Z3 Exam Timetabling

Three complete, comparable Z3 formulations of the assessment timetabling problem described in the 2026/27 COMP3070 Coursework 1 brief. This repository contains the three solvers, independent Python timetable validation, unit tests, fixed-instance comparisons, and seeded scalability experiments. All mathematical formulations use the **same eight constraints**.

## 1. Getting started

From the **repository root** in a Windows PowerShell terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

If you do not have an environment yet: `python -m venv .venv` before activation. The dependencies are `z3-solver` and `matplotlib`; pandas is **not** required. Do not commit or submit `.venv/`.

Run a solver on a supplied instance:

```powershell
python Formulation1.py instances/sat1.txt
python Formulation2.py instances/sat1.txt
python Formulation3.py instances/sat1.txt
python Formulation3.py instances/unsat1.txt
```

All three print `sat`/`unsat`, a timetable if satisfiable, and the time spent in `solver.check()` in milliseconds. Additional construction time is reported separately. An `unknown` result is **not** the same as UNSAT.

## 2. Constraint specification (final numbering)

| ID | Type | Requirement |
|---|---|---|
| C1 | Main | Assign every exam to exactly one valid timeslot and exactly one room. |
| C2 | Main | A room hosts at most one exam in a given timeslot. |
| C3 | Main | Room capacity is at least the number of distinct students taking the exam. |
| C4 | Main | A student's exams may not be scheduled in adjacent ordered timeslots. |
| C5 | Main | A student's exams may not be scheduled in the same timeslot. |
| C6 | Additional | Each timeslot hosts at most `max_exams_per_slot` exams in total (across all rooms). |
| C7 | Additional | The assigned room has **all** facilities required by the exam. |
| C8 | Additional | The assigned timeslot duration is at least the exam duration. |

Timeslots are indexed `0, ..., T-1`; adjacent means indices differ by 1, not necessarily one hour. Examinations occupy their whole assigned room/slot even if shorter than the slot. Duplicate enrolment records count only once. C4 and C5 are both necessary: a time difference of zero is not a consecutive-slot difference of one.

### Supplied data versus proposed extensions

The official `.txt` format supplies student count, exam count, timeslot count, room count, room capacities and exam/student enrolment pairs. It **does not supply** a maximum concurrent-exam limit, room facility sets, or exam and slot durations. These are our **synthetic extensions**, specified in companion `.extra.json` files for the examples.

On official baseline instances, neutral defaults are used: `max_exams_per_slot = number_of_rooms`, no facility requirements, 60-minute exams and 120-minute slots. C6–C8 are therefore nonbinding, preserving the core Moodle instance semantics. These defaults **must not** be described as data provided by the lecturer. C6 can become restrictive when its explicit limit is smaller than the number of rooms.

Example companion `example.extra.json` for two exams, three rooms, one timeslot:

```json
{
  "exam_requirements": [[], []],
  "room_facilities": [[], [], []],
  "exam_durations": [60, 60],
  "slot_durations": [120],
  "max_exams_per_slot": 1
}
```

All four facility/duration fields must be provided together; `max_exams_per_slot` is optional. Use nonnegative integer concurrency limits and positive integer durations. Facility matching is case-sensitive.

## 3. Mathematical notation and formulations

Let `E` denote the exam set, `T` the ordered timeslot set, `R` the room set, `n_e` the number of distinct students registered for exam `e`, `c_r` room capacity, and `P` the set of distinct exam pairs sharing at least one student. Let `M` be the C6 limit, `Q_e` required facilities and `F_r` room facilities; `d_e` and `l_t` are exam and timeslot durations.

### F1 — Integer formulation (`Formulation1.py`)

Two bounded integer variables per exam: `slot[e] in [0,T-1]` and `room[e] in [0,R-1]`. Decision-variable count: **2E**.

- C1: both variables constrained to their respective domains.
- C2: for all distinct exams `a,b`, `room[a] != room[b] OR slot[a] != slot[b]`.
- C3/C7: exclude rooms `r` with `n_e > c_r` or `Q_e` not a subset of `F_r`.
- C4: for every `(a,b)` in `P`, exclude both differences `slot[a]-slot[b] = 1` and `slot[b]-slot[a] = 1`.
- C5: for every `(a,b)` in `P`, require `slot[a] != slot[b]`.
- C6: for each timeslot `t`, `Sum(If(slot[e] == t, 1, 0) for e in E) <= M`.
- C8: exclude slot `t` whenever `d_e > l_t`.

### F2 — Boolean formulation (`Formulation2.py`)

Boolean `X[e,t,r]` is true exactly when exam `e` occupies timeslot `t` in room `r`. Decision-variable count: **E × T × R**.

- C1: `PbEq([(X[e,t,r], 1) for t,r], 1)` for each exam.
- C2: `AtMost(X[e,t,r] for e in E, 1)` for each room and slot.
- C3/C7/C8: forbid ineligible triples by `Not(X[e,t,r])`.
- Define `in_slot[e,t] = Or(X[e,t,r] for r in R)`; this is a derived expression, **not** an additional decision variable.
- C5: `AtMost(in_slot[e,t] for e registered to student s, 1)`.
- C4: let `busy[s,t] = Or(in_slot[e,t] for exams e taken by student s)`; prohibit `And(busy[s,t], busy[s,t+1])`.
- C6: `Sum(If(X[e,t,r], 1, 0) for e,r) <= M` for each timeslot.

### F3 — Hybrid formulation (`Formulation3.py`)

Integer `t[e]` chooses each exam's timeslot; Boolean `y[e,r]` chooses its room. Decision-variable count: **E + E × R**.

- C1: `0 <= t[e] < T` and `PbEq([(y[e,r], 1) for r], 1)`.
- C2: `And(y[a,r], y[b,r]) -> t[a] != t[b]` for each distinct pair and room.
- C3/C7: prohibit ineligible room choices by `Not(y[e,r])`.
- C4/C5: same shared-student pair constraints as F1, applied to `t[e]`.
- C6: `Sum(If(t[e] == q, 1, 0) for e) <= M` for each timeslot `q`.
- C8: prohibit `t[e] == q` if `d_e > l_q`.

All three models encode the same problem, but the number and complexity of expressions differ. **Fewer declared variables need not mean faster performance**; assertions are top-level Z3 assertions, not internal SAT clauses.

## 4. Input/output and data validation

```python
from shared_input import read_file
from Formulation3 import solve_hybrid
from timetable_check import validate_timetable

instance = read_file("instances/sat1.txt", baseline=True)
result = solve_hybrid(instance)
if result["status"] == "sat":
    validate_timetable(instance, result["timetable"])
```

`read_file(path)` automatically loads `<stem>.extra.json` when present. `read_file(path, baseline=True)` ignores that companion file; alternatively `read_file(path, metadata_filename)` loads explicit metadata. Input errors raise exceptions rather than being converted to UNSAT. Timetables are lists of `(exam_id, slot_id, room_id)` tuples. A SAT result with zero exams has an empty timetable. Independent validation in `timetable_check.py` checks all eight constraints without using Z3 expressions.

## 5. Tests and correctness evidence

```powershell
python -m unittest discover -s tests -v
python -m unittest discover -s tests -p "test_formulation3.py" -v
python tests/alt_solutions_check.py --f1 .
```

Tests cover SAT/UNSAT inputs, the 20 official labelled instances, 10 extended examples, boundary cases, input validation, each optional constraint, solution validity and brute-force checking of small random instances. The alternative-solution checker blocks one full timetable and requests a second; a different timetable is an **alternative solution**, not a different mathematical formulation. If no instance files are found, the tests should fail rather than silently pass.

## 6. Benchmarks, charts and report tables

Run on the same machine and Python environment:

```powershell
python compare_three_formulations.py --repeats 10 --scalability --timeout-ms 20000
python generate_reports.py
```

The comparison writes to `results/`:

- `comparison_3way.csv`: expected and actual status, mean/median/std `solver.check()` time, average model build time, declared variable count and assertion count for each instance and formulation.
- `scalability_3way.csv`: fixed-seed generated instances, varied exam counts, three formulations, SAT/UNSAT outcomes and timings.
- `summary_3way.md`: summary and discrepancies.
- `chart_official_times_3way.png`: solving time over the 20 official instances.
- `chart_variables_3way.png`: variable-count comparison.
- `chart_sat_vs_unsat_3way.png`: separate SAT and UNSAT average solving times.
- `chart_build_vs_solve_3way.png`: model construction versus solve time.
- `chart_scalability_3way.png`: timing by problem size (if scalability data exists).
- `report_tables.md`: compact correctness/timing table for the report.

These PNGs use **Matplotlib**, not screenshot editing or synthetic benchmark values. They only appear after the benchmark CSVs have been generated. An `unknown` timeout is not proof of satisfiability or unsatisfiability. Mixing SAT and UNSAT in scalability experiments is an evaluation limitation and must be acknowledged. Short millisecond measurements are noisy; report the environment, number of repetitions and spread.

## 7. Project layout

```text
Formulation1.py                    F1 integer solver
Formulation2.py                    F2 Boolean solver
Formulation3.py                    F3 hybrid solver
shared_input.py                    shared data parser and metadata validation
timetable_check.py                 independent solution validation
compare_three_formulations.py     3-way benchmark and generated dataset experiments
generate_reports.py               Matplotlib figures and report table
instances/                        20 original Moodle .txt examples (retain your files)
examples/                         10 synthetic .txt + .extra.json cases (retain your files)
tests/                            unit tests and alternative-solution checker
results/       generated CSVs, Markdown, PNGs
requirements.txt                  dependencies
```

The supplied official instances and synthetic examples are **not distributed with this replacement package**: retain your current files. The original coursework PDF and Moodle template may be retained under `official/` for development, but need not be submitted as solver code.

## 8. Report and submission guidance

The brief asks for a report PDF and executable Python code, with five main and at least three additional constraints. Suggested report sections in order: report contents/introduction, **all three full mathematical formulations**, implementation, evaluation, discussion, conclusion, references. Clearly distinguish baseline from proposed synthetic extension cases; show tables for all official instances and results for extended cases, time measurements and meaningful performance discussion. Explain trade-offs rather than asserting one solver is universally best.

Per the coursework brief, acknowledge adapted/external/AI-assisted code appropriately and clearly identify the group's own contributions. Check the university's academic integrity rules and do not imply generated code is wholly independently authored. Keep the submitted ZIP free of `.venv`, `__pycache__`, temporary Word lock files and unrelated legacy benchmark outputs.

**Deadline in brief:** Friday, 13 November 2026 at 18:00 (Malaysia time).
