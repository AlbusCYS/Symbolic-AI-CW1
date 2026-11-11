# Test results: Formulation 1 (integer) vs Formulation 2 (Boolean)

Z3 5.3.3, 10 repeats per instance; times are the mean of `solver.check()` in ms.

## Correctness and timing

| Instance | Data mode | Expected | F1 | F1 ok | F1 ms | F2 | F2 ok | F2 ms | Agree | Timetables |
|---|---|---|---|---|---|---|---|---|---|---|
| instances/sat1.txt | baseline | sat | sat | yes | 0.73 | sat | yes | 0.21 | yes | valid |
| instances/sat2.txt | baseline | sat | sat | yes | 3.03 | sat | yes | 0.91 | yes | valid |
| instances/sat3.txt | baseline | sat | sat | yes | 4.32 | sat | yes | 0.64 | yes | valid |
| instances/sat4.txt | baseline | sat | sat | yes | 0.85 | sat | yes | 0.15 | yes | valid |
| instances/sat5.txt | baseline | sat | sat | yes | 3.55 | sat | yes | 0.49 | yes | valid |
| instances/sat6.txt | baseline | sat | sat | yes | 1.80 | sat | yes | 2.31 | yes | valid |
| instances/sat7.txt | baseline | sat | sat | yes | 2.23 | sat | yes | 3.05 | yes | valid |
| instances/sat8.txt | baseline | sat | sat | yes | 1.95 | sat | yes | 2.09 | yes | valid |
| instances/sat9.txt | baseline | sat | sat | yes | 2.34 | sat | yes | 4.56 | yes | valid |
| instances/sat10.txt | baseline | sat | sat | yes | 2.42 | sat | yes | 7.40 | yes | valid |
| instances/unsat1.txt | baseline | unsat | unsat | yes | 0.67 | unsat | yes | 0.09 | yes | n/a |
| instances/unsat2.txt | baseline | unsat | unsat | yes | 0.67 | unsat | yes | 0.09 | yes | n/a |
| instances/unsat3.txt | baseline | unsat | unsat | yes | 2.10 | unsat | yes | 0.65 | yes | n/a |
| instances/unsat4.txt | baseline | unsat | unsat | yes | 1.74 | unsat | yes | 0.47 | yes | n/a |
| instances/unsat5.txt | baseline | unsat | unsat | yes | 1.62 | unsat | yes | 2.10 | yes | n/a |
| instances/unsat6.txt | baseline | unsat | unsat | yes | 1.49 | unsat | yes | 1.13 | yes | n/a |
| instances/unsat7.txt | baseline | unsat | unsat | yes | 1.79 | unsat | yes | 0.47 | yes | n/a |
| instances/unsat8.txt | baseline | unsat | unsat | yes | 1.66 | unsat | yes | 1.48 | yes | n/a |
| instances/unsat9.txt | baseline | unsat | unsat | yes | 6.88 | unsat | yes | 44.87 | yes | n/a |
| instances/unsat10.txt | baseline | unsat | unsat | yes | 14.86 | unsat | yes | 510.97 | yes | n/a |
| examples/sat_combined_gap.txt | extended | sat | sat | yes | 1.34 | sat | yes | 0.60 | yes | valid |
| examples/sat_duration_exact.txt | extended | sat | sat | yes | 0.66 | sat | yes | 0.20 | yes | valid |
| examples/sat_duration_forced.txt | extended | sat | sat | yes | 0.74 | sat | yes | 0.12 | yes | valid |
| examples/sat_facilities_forced.txt | extended | sat | sat | yes | 0.75 | sat | yes | 0.12 | yes | valid |
| examples/unsat_combined_contention.txt | extended | unsat | unsat | yes | 0.79 | unsat | yes | 0.11 | yes | n/a |
| examples/unsat_duration_long.txt | extended | unsat | unsat | yes | 0.66 | unsat | yes | 0.09 | yes | n/a |
| examples/unsat_facilities_missing.txt | extended | unsat | unsat | yes | 0.64 | unsat | yes | 0.03 | yes | n/a |
| examples/unsat_facilities_partial.txt | extended | unsat | unsat | yes | 0.66 | unsat | yes | 0.09 | yes | n/a |


**Summary:** F1 correct on 28/28, F2 correct on 28/28, formulations agree on 28/28.
 F1 was faster on 8/28 instances, F2 on 20/28.


## Model size (variables / top-level assertions)

| Instance | F1 vars | F1 assertions | F2 vars | F2 assertions |
|---|---|---|---|---|
| instances/sat1.txt | 2 | 4 | 1 | 1 |
| instances/sat2.txt | 4 | 12 | 6 | 10 |
| instances/sat3.txt | 4 | 9 | 4 | 4 |
| instances/sat4.txt | 4 | 10 | 4 | 5 |
| instances/sat5.txt | 4 | 9 | 4 | 4 |
| instances/sat6.txt | 6 | 22 | 90 | 127 |
| instances/sat7.txt | 10 | 47 | 100 | 89 |
| instances/sat8.txt | 6 | 27 | 60 | 128 |
| instances/sat9.txt | 10 | 69 | 200 | 591 |
| instances/sat10.txt | 12 | 87 | 300 | 719 |
| instances/unsat1.txt | 2 | 6 | 8 | 9 |
| instances/unsat2.txt | 4 | 13 | 4 | 9 |
| instances/unsat3.txt | 10 | 72 | 105 | 305 |
| instances/unsat4.txt | 8 | 51 | 100 | 243 |
| instances/unsat5.txt | 8 | 41 | 80 | 96 |
| instances/unsat6.txt | 6 | 27 | 27 | 61 |
| instances/unsat7.txt | 10 | 52 | 90 | 164 |
| instances/unsat8.txt | 8 | 44 | 36 | 85 |
| instances/unsat9.txt | 18 | 207 | 360 | 595 |
| instances/unsat10.txt | 16 | 147 | 240 | 497 |
| examples/sat_combined_gap.txt | 4 | 13 | 6 | 11 |
| examples/sat_duration_exact.txt | 2 | 4 | 1 | 1 |
| examples/sat_duration_forced.txt | 2 | 5 | 2 | 2 |
| examples/sat_facilities_forced.txt | 2 | 5 | 2 | 2 |
| examples/unsat_combined_contention.txt | 4 | 13 | 8 | 14 |
| examples/unsat_duration_long.txt | 2 | 6 | 2 | 3 |
| examples/unsat_facilities_missing.txt | 2 | 5 | 1 | 2 |
| examples/unsat_facilities_partial.txt | 2 | 6 | 2 | 3 |
