# COMP3070 CW1 — corrected C1–C8 (revision)

## Constraint contract

**Main:** C1 exactly one room and slot for each exam; C2 no room double-booking; C3 room capacity; C4 no consecutive exams for a student; C5 no simultaneous exams for a student.

**Additional:** C6 at most `max_exams_per_slot` exams in any slot; C7 facilities; C8 duration. Slots are ordered by their zero-based indices; consecutive means index difference 1.

### Choosing the C6 limit

The official Moodle `.txt` format does **not** contain a max-exams-per-slot parameter, facilities or duration data. Without extra data, `max_exams_per_slot` defaults to the number of rooms, so C6 is deliberately nonbinding for the official baseline: C2 already prevents more exams in a slot than rooms. C7/C8 likewise use explicitly synthetic neutral defaults in baseline mode.

For extended examples, put an adjacent `<stem>.extra.json` file with all four original metadata fields, and the **optional** `max_exams_per_slot` nonnegative integer. For example:

```json
{
  "exam_requirements": [[], []],
  "room_facilities": [[], [], []],
  "exam_durations": [60, 60],
  "slot_durations": [120],
  "max_exams_per_slot": 1
}
```

This sets a single global maximum for **each** slot. There is no implicit requirement to make all slots equally full. If the limit is greater than or equal to the number of rooms, C6 imposes no further restrictions beyond C2.

## Formulations

- `Formulation1.py`: `2E` integer variables, `slot[e]` and `room[e]`; C6 uses `Sum(If(slot[e] == t, 1, 0)) <= M` for each slot.
- `Formulation2.py`: `E×T×R` Boolean variables, `X[e,t,r]`; C6 uses `Sum(If(X[e,t,r], 1, 0)) <= M` for each slot.

These are genuinely different encodings of **the same constraints**, so they can be compared in variables, assertion counts, model-build time, solve time, and scalability. A second timetable found by blocking a model is an *alternative solution*, not a third mathematical *formulation*.

## Running

Install `z3-solver` using your own Python environment (`pip install z3-solver`). From the project root:

```bash
python Formulation1.py examples/unsat_c6_limit_one.txt
python Formulation2.py examples/sat_c6_limit_allows_two.txt
python -m unittest discover -s tests -p 'test_c6_slot_limit.py' -v
python -m unittest discover -s tests -v
```

For official `.txt` files, place the supplied Moodle files in `instances/`. For your earlier 8 facility/duration examples, keep them in `examples/` beside their JSON companions. These original external instances were not in the uploaded code bundle, and are **not** included here.

The existing `compare_formulations.py` compares the solvers and runs the independent validator. It automatically discovers examples from the `examples` folder. Re-run its evaluation after copying in the official instances and original examples. The earlier eight facility/duration examples are **not included** in the uploaded files. The existing `test_c7_c8.py` now discovers all available extended examples, but retain the original eight examples for complete C7/C8 coverage.

## Important before submission

- Update all report equations and diagrams to match the new C1–C8 **numbering**.
- Use both a one-slot SAT and a one-slot UNSAT example to isolate C6.
- Distinguish baseline (nonbinding C6, C7 and C8) from extended tests.
- Clearly document any assumption about simultaneous exams, ordered slots, and capacities.
- If copied or AI-assisted code is used, follow the coursework's disclosure and attribution requirements.
