# Test results: Formulation 1 (integer) vs Formulation 2 (Boolean)

Z3 5.3.3, 10 repeats per instance; times are the mean of `solver.check()` in ms.

## Correctness and timing

| Instance | Data mode | Expected | F1 | F1 ok | F1 ms | F2 | F2 ok | F2 ms | Agree | Timetables |
|---|---|---|---|---|---|---|---|---|---|---|
| instances/sat1.txt | baseline | sat | sat | yes | 0.80 | sat | yes | 0.20 | yes | valid |
| instances/sat2.txt | baseline | sat | sat | yes | 1.55 | sat | yes | 0.59 | yes | valid |
| instances/sat3.txt | baseline | sat | sat | yes | 2.80 | sat | yes | 0.52 | yes | valid |
| instances/sat4.txt | baseline | sat | sat | yes | 0.85 | sat | yes | 0.13 | yes | valid |
| instances/sat5.txt | baseline | sat | sat | yes | 2.73 | sat | yes | 0.51 | yes | valid |
| instances/sat6.txt | baseline | sat | sat | yes | 1.67 | sat | yes | 2.04 | yes | valid |
| instances/sat7.txt | baseline | sat | sat | yes | 2.02 | sat | yes | 2.56 | yes | valid |
| instances/sat8.txt | baseline | sat | sat | yes | 1.66 | sat | yes | 2.66 | yes | valid |
| instances/sat9.txt | baseline | sat | sat | yes | 2.65 | sat | yes | 5.09 | yes | valid |
| instances/sat10.txt | baseline | sat | sat | yes | 2.77 | sat | yes | 7.71 | yes | valid |
| instances/unsat1.txt | baseline | unsat | unsat | yes | 0.68 | unsat | yes | 0.12 | yes | n/a |
| instances/unsat2.txt | baseline | unsat | unsat | yes | 0.81 | unsat | yes | 0.11 | yes | n/a |
| instances/unsat3.txt | baseline | unsat | unsat | yes | 2.53 | unsat | yes | 1.10 | yes | n/a |
| instances/unsat4.txt | baseline | unsat | unsat | yes | 3.16 | unsat | yes | 0.82 | yes | n/a |
| instances/unsat5.txt | baseline | unsat | unsat | yes | 2.00 | unsat | yes | 2.56 | yes | n/a |
| instances/unsat6.txt | baseline | unsat | unsat | yes | 1.44 | unsat | yes | 1.17 | yes | n/a |
| instances/unsat7.txt | baseline | unsat | unsat | yes | 1.77 | unsat | yes | 0.50 | yes | n/a |
| instances/unsat8.txt | baseline | unsat | unsat | yes | 1.63 | unsat | yes | 1.62 | yes | n/a |
| instances/unsat9.txt | baseline | unsat | unsat | yes | 7.25 | unsat | yes | 47.49 | yes | n/a |
| instances/unsat10.txt | baseline | unsat | unsat | yes | 14.72 | unsat | yes | 485.54 | yes | n/a |
| examples/sat_combined_gap.txt | extended | sat | sat | yes | 1.18 | sat | yes | 0.54 | yes | valid |
| examples/sat_duration_exact.txt | extended | sat | sat | yes | 0.59 | sat | yes | 0.18 | yes | valid |
| examples/sat_duration_forced.txt | extended | sat | sat | yes | 0.67 | sat | yes | 0.11 | yes | valid |
| examples/sat_facilities_forced.txt | extended | sat | sat | yes | 0.68 | sat | yes | 0.12 | yes | valid |
| examples/unsat_combined_contention.txt | extended | unsat | unsat | yes | 0.74 | unsat | yes | 0.11 | yes | n/a |
| examples/unsat_duration_long.txt | extended | unsat | unsat | yes | 0.61 | unsat | yes | 0.08 | yes | n/a |
| examples/unsat_facilities_missing.txt | extended | unsat | unsat | yes | 0.60 | unsat | yes | 0.03 | yes | n/a |
| examples/unsat_facilities_partial.txt | extended | unsat | unsat | yes | 0.61 | unsat | yes | 0.08 | yes | n/a |


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
| 5 | 1 | unsat | 1.0 | 10 | unsat | 0.4 | 60 |
| 5 | 2 | unsat | 1.1 | 10 | unsat | 0.4 | 60 |
| 5 | 3 | unsat | 1.8 | 10 | unsat | 4.1 | 60 |
| 10 | 1 | unsat | 1.7 | 20 | unsat | 1.6 | 240 |
| 10 | 2 | unsat | 1.6 | 20 | unsat | 1.6 | 240 |
| 10 | 3 | sat | 6.3 | 20 | sat | 10.6 | 240 |
| 15 | 1 | unsat | 5.2 | 30 | unsat | 4.9 | 810 |
| 15 | 2 | unsat | 5.9 | 30 | unsat | 4.1 | 810 |
| 15 | 3 | sat | 7.0 | 30 | sat | 25.8 | 810 |
| 20 | 1 | sat | 10.5 | 40 | sat | 52.8 | 2400 |
| 20 | 2 | sat | 11.4 | 40 | sat | 52.8 | 2400 |
| 20 | 3 | sat | 10.4 | 40 | sat | 65.5 | 2400 |
| 25 | 1 | sat | 15.7 | 50 | sat | 99.6 | 4500 |
| 25 | 2 | unsat | 13.1 | 50 | unsat | 19.0 | 4500 |
| 25 | 3 | sat | 17.4 | 50 | sat | 109.1 | 4500 |
| 30 | 1 | sat | 21.4 | 60 | sat | 175.7 | 7560 |
| 30 | 2 | sat | 21.1 | 60 | sat | 161.4 | 7560 |
| 30 | 3 | sat | 21.2 | 60 | sat | 190.2 | 7560 |
| 40 | 1 | sat | 58.9 | 80 | sat | 459.2 | 19200 |
| 40 | 2 | sat | 40.8 | 80 | sat | 449.1 | 19200 |
| 40 | 3 | sat | 48.4 | 80 | sat | 492.4 | 19200 |
| 50 | 1 | sat | 76.4 | 100 | sat | 916.4 | 36000 |
| 50 | 2 | unsat | 53.2 | 100 | unsat | 162.0 | 36000 |
| 50 | 3 | sat | 77.0 | 100 | sat | 949.6 | 36000 |
