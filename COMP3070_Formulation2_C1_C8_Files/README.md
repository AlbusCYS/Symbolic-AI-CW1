# COMP3070 Formulation 2 with C1 to C8

Boolean X[e,t,r] assignments select a slot and room for each exam. Companion JSON files supply facility and duration data for C7 and C8. The original Moodle text format is retained.

## Run in Google Colab

Open the [Colab notebook](https://colab.research.google.com/drive/1vmKJAvJkhGyhGh493TbsYi3RITLSBR-j) and choose Runtime > Run all with a CPU runtime. It installs Z3, restores the input data and tests, writes the code from editable source cells, runs the checks and prints example timetables.

Save code changes in the notebook's editable source cells. The Files-panel copies are temporary and are overwritten when the corresponding source cells run.

The package cell creates a ZIP containing the current code, tests, inputs, examples, shared contract and results. Download it from the Files panel. For formulation 1 integration, use SHARED_CONTRACT.md, shared_input.py, timetable_check.py and the same example pairs.

## Commands inside the restored project folder

```python
%run formulation2.py instances/sat2.txt
%run formulation2.py examples/sat_combined_gap.txt
%run formulation2.py examples/unsat_combined_contention.txt
%run formulation2.py examples/unsat_combined_contention.txt --baseline
```

The second and third commands automatically load their companion metadata. The final command deliberately ignores metadata and solves the original C1-C6-equivalent model. The CLI labels baseline and extended modes. To test all cases, run python -m unittest -v. To create measurements, run python test_formulation2.py --benchmark.

## Solver and shared input

Use solve_boolean(instance). The result includes status, timetable, model construction time, solver.check() time, Boolean variable count, top-level assertion count, reason_unknown, and metadata_mode. SAT timetables contain (exam_id, slot_id, room_id) triples, using zero-based IDs. Enrolment pairs in the text files are (exam_id, student_id).

C1/C2 choose exactly one room-slot pair per exam. C3 forbids room double booking. C4 checks distinct student enrolment against room capacity. C5 forbids adjacent occupied slots for a student. C6 forbids simultaneous exams for a student. C7 requires every requested facility to exist in the chosen room. C8 requires the exam duration to fit its one selected slot, including exact fits. Shorter exams do not allow room sharing.

shared_input.py defines the common Instance, read_file and metadata preparation functions without a Z3 dependency. SHARED_CONTRACT.md contains the schema, assumptions and integer integration snippets.

## Tests and measurements

The checks retain all 20 Moodle cases and 48 tiny baseline comparisons against exhaustive search. Added checks cover the facility and duration rules, their interaction with capacity and student gaps, malformed metadata, the eight saved synthetic examples, and 48 tiny extended exhaustive-search comparisons. The checker examines actual timetable triples in ordinary Python.

Original-format files use explicitly labelled synthetic neutral defaults, so C7/C8 are nonbinding. Extended examples contain complete metadata and deliberately exercise those restrictions. The eight example outcomes are encoded by their sat/unsat prefixes and checked by the tests.

results_c1_c8.csv records one solve per input, with Python/Z3 versions and data mode. Use repeated measurements when comparing formulation performance.

## Attribution

The parser and Instance structure are based on the Moodle template, preserved in official/. The 20 supplied instances are preserved in instances/. The Boolean encoding, supplemental JSON format, checks and notebook are additions.

Sources: the supplied COMP3070 brief, the leader's Symbolic AI.docx, the Moodle template and instances, and the official [Z3 Python API](https://z3prover.github.io/api/html/namespacez3py.html).

## Verified execution on 31 October 2026

Colab runtime: Python 3.13.18 and Z3 5.3.2. All 42 test methods passed, covering 20 original cases, eight extended examples and 96 exhaustive-search comparisons. All 28 measured input outcomes matched their expectations. The saved notebook includes the execution outputs; results_c1_c8.csv contains the Colab measurements.
