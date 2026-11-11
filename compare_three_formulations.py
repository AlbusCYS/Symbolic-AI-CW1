"""Reproducible three-way benchmark for the COMP3070 exam timetabling solvers.

Run from the repository root:
    python compare_three_formulations.py --repeats 10
    python compare_three_formulations.py --repeats 10 --scalability

Results are written directly to results/ (or the --out directory). Requires F1, F2, F3, shared_input and checker in root.
"""
import argparse
import csv
import random
import statistics
from pathlib import Path

import z3
from Formulation1 import solve_integer
from Formulation2 import solve_boolean
from Formulation3 import solve_hybrid
from shared_input import Instance, read_file
from timetable_check import validate_timetable

SOLVERS = {"F1 Integer": solve_integer, "F2 Boolean": solve_boolean, "F3 Hybrid": solve_hybrid}


def run_trials(factory, repeats, timeout_ms):
    rows = []
    for label, fn in SOLVERS.items():
        times, builds, statuses, counts = [], [], set(), []
        for _ in range(repeats):
            inst = factory()
            # Each solver constructs a new Solver object. Apply timeout via global
            # Z3 setting; restore at the end of each invocation.
            z3.set_param("timeout", timeout_ms)
            try:
                out = fn(inst)
            finally:
                z3.set_param("timeout", 4294967295)
            times.append(out["solve_time_ms"])
            builds.append(out["build_time_ms"])
            statuses.add(out["status"])
            counts.append(out)
            if out["status"] == "sat":
                validate_timetable(inst, out["timetable"])
        last = counts[-1]
        rows.append({"formulation": label, "status": "/".join(sorted(statuses)),
                     "mean_check_ms": statistics.fmean(times),
                     "median_check_ms": statistics.median(times),
                     "std_check_ms": statistics.pstdev(times),
                     "mean_build_ms": statistics.fmean(builds),
                     "variables": last["variable_count"],
                     "assertions": last["constraint_count"]})
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def random_instance(exams, seed):
    rng = random.Random(seed)
    inst = Instance()
    inst.number_of_exams = exams
    inst.number_of_students = max(1, 2 * exams)
    inst.number_of_slots = max(3, int(exams * 1.2))
    inst.number_of_rooms = max(2, exams // 4)
    inst.room_capacities = [rng.randint(4, 12) for _ in range(inst.number_of_rooms)]
    pairs = set()
    for student in range(inst.number_of_students):
        pairs.update((exam, student) for exam in rng.sample(range(exams), min(exams, rng.randint(2, 3))))
    inst.exams_to_students = sorted(pairs)
    return inst


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--timeout-ms", type=int, default=20000)
    parser.add_argument("--scalability", action="store_true")
    parser.add_argument("--out", default="results")
    args = parser.parse_args()
    if args.repeats < 1 or args.timeout_ms < 1:
        parser.error("--repeats and --timeout-ms must be positive")
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(Path("instances").glob("*.txt")) + sorted(Path("examples").glob("*.txt"))
    official = list(Path("instances").glob("*.txt"))
    extended = list(Path("examples").glob("*.txt"))
    if len(official) != 20:
        parser.error(f"Expected 20 official instances in instances/, found {len(official)}")
    if len(extended) != 10:
        parser.error(f"Expected 10 extended examples in examples/, found {len(extended)}")
    result_rows, failures = [], []
    print("Comparing F1 Integer / F2 Boolean / F3 Hybrid")
    for path in files:
        baseline = path.parent.name == "instances"
        expected = "unsat" if path.stem.startswith("unsat") else "sat"
        trial = run_trials(lambda p=path, b=baseline: read_file(p, baseline=b), args.repeats, args.timeout_ms)
        all_ok = all(item["status"] == expected for item in trial)
        for item in trial:
            result_rows.append({"instance": path.as_posix(), "mode": "baseline" if baseline else "extended",
                                "expected": expected, "correct": item["status"] == expected, **item})
        if not all_ok:
            failures.append(str(path))
        print(f"{str(path):42} expected={expected:<5} " + "  ".join(
            f"{item['formulation'].split()[0]}:{item['status']} {item['mean_check_ms']:.3f}ms" for item in trial), flush=True)
    write_csv(output / "comparison_3way.csv", result_rows)
    scale_rows = []
    if args.scalability:
        for exams in [5, 10, 15, 20, 25, 30, 40, 50]:
            for seed in [1, 2, 3]:
                trial = run_trials(lambda n=exams, s=seed: random_instance(n, s),
                                   max(1, min(args.repeats, 3)), args.timeout_ms)
                statuses = {item["status"] for item in trial}
                if len(statuses) != 1:
                    # UNKNOWN is timeout, not a proof of disagreement.
                    if "unknown" not in statuses:
                        failures.append(f"scalability exams={exams}, seed={seed}")
                for item in trial:
                    scale_rows.append({"exams": exams, "seed": seed, **item})
                print(f"scalability exams={exams} seed={seed}: " +
                      ", ".join(f"{v['formulation']}={v['status']}" for v in trial), flush=True)
        write_csv(output / "scalability_3way.csv", scale_rows)
    summary = ["# Three-way comparison: COMP3070", "",
               "Solver.check() times exclude model construction and model enumeration.",
               "Official instances run in baseline mode. Extended examples use companion JSON.",
               "", f"Files checked: {len(files)}; discrepancies: {len(failures)}.",
               "", "## Mean check time (ms) by formulation", "",
               "| Formulation | Mean across per-instance means |",
               "|---|---:|"]
    for label in SOLVERS:
        matching = [r["mean_check_ms"] for r in result_rows if r["formulation"] == label]
        summary.append(f"| {label} | {statistics.fmean(matching):.3f} |")
    summary += ["", "## Discrepancies", "", *(failures if failures else ["None detected."]), "",
                "Review individual statuses, timing distributions and model sizes in comparison_3way.csv.",
                "Solver performance is machine/instance-dependent; do not infer speed from variable counts alone."]
    (output / "summary_3way.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"\nResults written to {output.resolve()}")
    if failures:
        raise SystemExit(f"Comparison failed on: {failures}")
    print("All three formulations agree with expected SAT/UNSAT labels.")
    print("Generate Matplotlib figures: python generate_reports.py")


if __name__ == "__main__":
    main()
