# Test results: Formulation 1 (integer) vs Formulation 2 (Boolean)

Z3 5.3.3, 10 repeats per instance; times are the mean of `solver.check()` in ms.

## Correctness and timing

| Instance | Data mode | Expected | F1 | F1 ok | F1 ms | F2 | F2 ok | F2 ms | Agree | Timetables |
|---|---|---|---|---|---|---|---|---|---|---|
| instances/sat1.txt | baseline | sat | sat | yes | 0.85 | sat | yes | 0.24 | yes | valid |
| instances/sat2.txt | baseline | sat | sat | yes | 1.67 | sat | yes | 0.75 | yes | valid |
| instances/sat3.txt | baseline | sat | sat | yes | 3.72 | sat | yes | 0.67 | yes | valid |
| instances/sat4.txt | baseline | sat | sat | yes | 1.08 | sat | yes | 0.19 | yes | valid |
| instances/sat5.txt | baseline | sat | sat | yes | 2.67 | sat | yes | 0.68 | yes | valid |
| instances/sat6.txt | baseline | sat | sat | yes | 1.86 | sat | yes | 2.78 | yes | valid |
| instances/sat7.txt | baseline | sat | sat | yes | 3.33 | sat | yes | 2.64 | yes | valid |
| instances/sat8.txt | baseline | sat | sat | yes | 1.55 | sat | yes | 1.88 | yes | valid |
| instances/sat9.txt | baseline | sat | sat | yes | 2.14 | sat | yes | 4.46 | yes | valid |
| instances/sat10.txt | baseline | sat | sat | yes | 2.44 | sat | yes | 7.95 | yes | valid |
| instances/unsat1.txt | baseline | unsat | unsat | yes | 0.77 | unsat | yes | 0.11 | yes | n/a |
| instances/unsat2.txt | baseline | unsat | unsat | yes | 0.83 | unsat | yes | 0.13 | yes | n/a |
| instances/unsat3.txt | baseline | unsat | unsat | yes | 2.15 | unsat | yes | 0.82 | yes | n/a |
| instances/unsat4.txt | baseline | unsat | unsat | yes | 2.44 | unsat | yes | 0.67 | yes | n/a |
| instances/unsat5.txt | baseline | unsat | unsat | yes | 2.32 | unsat | yes | 3.65 | yes | n/a |
| instances/unsat6.txt | baseline | unsat | unsat | yes | 2.03 | unsat | yes | 2.33 | yes | n/a |
| instances/unsat7.txt | baseline | unsat | unsat | yes | 3.56 | unsat | yes | 0.88 | yes | n/a |
| instances/unsat8.txt | baseline | unsat | unsat | yes | 2.17 | unsat | yes | 2.06 | yes | n/a |
| instances/unsat9.txt | baseline | unsat | unsat | yes | 7.94 | unsat | yes | 62.98 | yes | n/a |
| instances/unsat10.txt | baseline | unsat | unsat | yes | 16.49 | unsat | yes | 880.94 | yes | n/a |
| examples/sat_combined_gap.txt | extended | sat | sat | yes | 1.73 | sat | yes | 0.89 | yes | valid |
| examples/sat_duration_exact.txt | extended | sat | sat | yes | 0.86 | sat | yes | 0.26 | yes | valid |
| examples/sat_duration_forced.txt | extended | sat | sat | yes | 0.98 | sat | yes | 0.18 | yes | valid |
| examples/sat_facilities_forced.txt | extended | sat | sat | yes | 1.01 | sat | yes | 0.17 | yes | valid |
| examples/unsat_combined_contention.txt | extended | unsat | unsat | yes | 1.10 | unsat | yes | 0.15 | yes | n/a |
| examples/unsat_duration_long.txt | extended | unsat | unsat | yes | 0.87 | unsat | yes | 0.14 | yes | n/a |
| examples/unsat_facilities_missing.txt | extended | unsat | unsat | yes | 0.87 | unsat | yes | 0.05 | yes | n/a |
| examples/unsat_facilities_partial.txt | extended | unsat | unsat | yes | 0.87 | unsat | yes | 0.13 | yes | n/a |


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


## Scalability on generated instances (timeout 20000 ms)

| Exams | Seed | F1 status | F1 median ms | F1 vars | F2 status | F2 median ms | F2 vars |
|---|---|---|---|---|---|---|---|
| 5 | 1 | unsat | 1.4 | 10 | unsat | 0.6 | 60 |
| 5 | 2 | unsat | 1.5 | 10 | unsat | 0.6 | 60 |
| 5 | 3 | unsat | 2.8 | 10 | unsat | 5.2 | 60 |
| 10 | 1 | unsat | 2.4 | 20 | unsat | 2.4 | 240 |
| 10 | 2 | unsat | 2.3 | 20 | unsat | 2.3 | 240 |
| 10 | 3 | sat | 5.5 | 20 | sat | 14.3 | 240 |
| 15 | 1 | unsat | 7.6 | 30 | unsat | 8.7 | 810 |
| 15 | 2 | unsat | 9.2 | 30 | unsat | 6.4 | 810 |
| 15 | 3 | sat | 8.8 | 30 | sat | 36.4 | 810 |
| 20 | 1 | sat | 16.3 | 40 | sat | 83.4 | 2400 |
| 20 | 2 | sat | 15.1 | 40 | sat | 79.8 | 2400 |
| 20 | 3 | sat | 16.1 | 40 | sat | 98.0 | 2400 |
| 25 | 1 | sat | 22.5 | 50 | sat | 164.2 | 4500 |
| 25 | 2 | unsat | 17.6 | 50 | unsat | 25.2 | 4500 |
| 25 | 3 | sat | 26.5 | 50 | sat | 176.8 | 4500 |
| 30 | 1 | sat | 49.5 | 60 | sat | 298.6 | 7560 |
| 30 | 2 | sat | 37.0 | 60 | sat | 257.9 | 7560 |
| 30 | 3 | sat | 25.5 | 60 | sat | 227.2 | 7560 |
| 40 | 1 | sat | 53.8 | 80 | sat | 730.9 | 19200 |
| 40 | 2 | sat | 72.7 | 80 | sat | 749.2 | 19200 |
| 40 | 3 | sat | 68.3 | 80 | sat | 884.6 | 19200 |
| 50 | 1 | sat | 95.1 | 100 | sat | 1507.3 | 36000 |
| 50 | 2 | unsat | 89.7 | 100 | unsat | 281.3 | 36000 |
| 50 | 3 | sat | 117.5 | 100 | sat | 1775.8 | 36000 |
