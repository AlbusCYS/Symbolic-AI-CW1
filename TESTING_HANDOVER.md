# Testing part: hand-over for the group

## Files to give the group
| File | Purpose |
|---|---|
| `compare_formulations.py` | Testing harness (include in the code submission) |
| `alt_solutions_check.py` | Multiple-solution test |
| `results/summary.md` | All result tables, ready to paste into the report's Evaluation section |
| `results/results_main.csv`, `results_scalability.csv`, `alt_solutions.txt` | Raw data |
| `results/chart_official_times.png`, `chart_variables.png`, `chart_scalability.png` | Figures for the report |

## Test environment (state this in the report)
All measurements were taken in a single session on one machine:
- Python 3.12.3, Z3 (z3-solver) 5.3.3
- Intel Xeon @ 2.10 GHz, 1 core, 4 GB RAM, Linux (cloud container)
- Warm-up solve before timing; each instance timed 10 times (scalability: 3 times)

The harness can be re-run with `python compare_formulations.py --f1 <F1 folder> --f2 <F2 folder>` and `python alt_solutions_check.py --f1 <F1 folder>` if anyone in the group wants to reproduce it (about 2 minutes). Instances are generated with fixed seeds.

## Method (for the report writer)
- 28 instances: the 20 official ones (baseline data) and 8 extended examples with C7 (facilities) and C8 (durations).
- Each instance is solved 10 times per formulation; the time reported is the mean of `solver.check()` in ms (model-building time is recorded separately).
- Expected answer comes from the file name (`sat*` / `unsat*`).
- Every SAT timetable is checked by the independent Python validator (`timetable_check.py`, no Z3).
- The two formulations are compared with each other on every instance.
- Scalability: random instances with 5 to 50 exams (3 seeds each, fixed so results are reproducible), 20 s timeout.
- All figures come from the single environment listed above.

## Findings
1. **Correctness:** both formulations were correct on 28/28 instances and agreed with each other on 28/28. Every SAT timetable passed the independent validator. No bugs found. The teammates' own unit tests (61 in total) also all pass.
2. **Official instances:** total solve time across the 20 official instances was about 62 ms for F1 and about 977 ms for F2. F2 was faster on most of the small instances (e.g. sat1 to sat5, unsat1 to unsat4, under 1 ms each), but F1 was much faster on the largest: unsat10 took 16 ms (F1) vs 881 ms (F2), and unsat9 took 8 ms vs 63 ms.
3. **Model size:** F1 declares 2 x E integer variables; F2 declares E x T x R Booleans. On unsat10 that is 16 vs 240, and on the generated 50-exam instances 100 vs 36,000.
4. **Scalability (median over 3 seeds):** the two are level at 10 to 15 exams (about 2 ms and 9 ms). From 20 exams F1 pulls ahead: 16 vs 83 ms at 20 exams, 68 vs 749 ms at 40, 95 vs 1507 ms at 50. F2's time grows roughly with its variable count; F1 grows gently. Neither hit the timeout.
5. **Multiple solutions (F1 blocking-clause test on the 10 sat instances):** sat1 and sat4 have a unique timetable; the other eight have more than one.
6. **Extended examples (C7/C8):** all 8 correct in both formulations, including exact-fit durations and partial facility matches. Both solve these in about 1 ms or less.

## Suggested discussion points
- Why F2 slows down: more variables and more clauses (each exam x slot x room is a Boolean), which grows quickly with instance size. F1's integer domains stay small.
- Why F2 is sometimes faster on tiny instances: Boolean SAT reasoning is very cheap when the problem is small, while F1 pays for arithmetic reasoning.
- Differences are in milliseconds on the supplied instances, so both are fast enough for the coursework; the gap only matters at larger scale.

## Limitations to state honestly
- Timings come from one machine (a shared cloud container) and vary run to run, so treat small differences (a few ms) as noise.
- Generated small instances are mostly unsat, so the scalability trend is clearest from 20 exams upward, where they are sat.
- Only F1 has a built-in multiple-solution check; F2 was not tested for this.
- The generated instances only exercise C1 to C6 (no C7/C8).
