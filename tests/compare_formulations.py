"""Head-to-head testing harness for the two exam-timetabling formulations.

Formulation 1: integer encoding  (slot[e], room[e] are bounded Int variables)
Formulation 2: Boolean encoding  (X[e,t,r] is a Bool per exam/slot/room triple)

What this script does
---------------------
1. CORRECTNESS: runs every official instance (instances/) and every extended
   example (examples/) through BOTH formulations. For each run it checks
     a) the status matches the expectation encoded in the file name
        (sat*.txt -> sat, unsat*.txt -> unsat),
     b) the two formulations agree with each other,
     c) every SAT timetable passes the independent validator
        (timetable_check.validate_timetable, ordinary Python, no Z3).
2. TIMING: repeats every solve N times and reports mean / median / std of the
   solver.check() time in milliseconds (model-building time is kept separate).
3. SCALABILITY: generates random instances of growing size (fixed seeds, so
   the results are reproducible) and times both formulations on them, with a
   per-solve timeout.
4. OUTPUT: writes CSV files, a Markdown summary and PNG charts to --out.

Usage
-----
    python compare_formulations.py --f1 path/to/formulation1_folder \
                                   --f2 path/to/formulation2_folder

Optional flags: --repeats 10  --scale-repeats 3  --timeout-ms 20000
                --skip-scalability  --out results
"""

import argparse
import csv
import importlib.util
import random
import statistics
import sys
from pathlib import Path

import z3


# --------------------------------------------------------------------------
# Loading the two formulations
# --------------------------------------------------------------------------
def load_module(path, name):
    """Import a .py file by path (supports loading solver modules by explicit file path)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_formulations(f1_dir, f2_dir):
    """Return (solve_integer, solve_boolean, read_file, validate_timetable, Instance, prepare_metadata)."""
    f1_dir, f2_dir = Path(f1_dir).resolve(), Path(f2_dir).resolve()
    # Both formulations use the same shared input and timetable checker.
    sys.path.insert(0, str(f1_dir))
    from shared_input import Instance, prepare_metadata, read_file
    from timetable_check import validate_timetable
    f1 = load_module(f1_dir / "Formulation1.py", "Formulation1")
    sys.path.insert(0, str(f2_dir))
    f2 = load_module(f2_dir / "Formulation2.py", "Formulation2")
    return f1.solve_integer, f2.solve_boolean, read_file, validate_timetable, Instance, prepare_metadata


# --------------------------------------------------------------------------
# Running and validating one solve
# --------------------------------------------------------------------------
def expected_status(path):
    """sat/unsat expectation from the file name prefix (the Moodle convention)."""
    return "unsat" if Path(path).name.startswith("unsat") else "sat"


def run_once(solver_fn, instance, validate):
    """Solve once; return (result_dict, validity_message).

    validity_message is 'valid' for a SAT timetable that passes the independent
    checker, the assertion text if it fails, and 'n/a' for non-SAT results.
    """
    result = solver_fn(instance)
    verdict = "n/a"
    if result["status"] == "sat":
        try:
            validate(instance, result["timetable"])
            verdict = "valid"
        except AssertionError as error:
            verdict = f"INVALID: {error}"
    return result, verdict


def summarise(values):
    """mean / median / population std-dev of a list of timings."""
    return (statistics.fmean(values), statistics.median(values),
            statistics.pstdev(values) if len(values) > 1 else 0.0)


def benchmark_file(path, name, fns, repeats, baseline):
    """Run one instance through both formulations `repeats` times."""
    solve_int, solve_bool, read_file, validate, _, _ = fns
    row = {"instance": name, "mode": "baseline" if baseline else "extended",
           "expected": expected_status(path)}
    for tag, solver_fn in (("f1", solve_int), ("f2", solve_bool)):
        solve_ms, build_ms, statuses, verdicts = [], [], set(), set()
        last = None
        for _ in range(repeats):
            instance = read_file(str(path), baseline=baseline)  # fresh copy each run
            last, verdict = run_once(solver_fn, instance, validate)
            solve_ms.append(last["solve_time_ms"])
            build_ms.append(last["build_time_ms"])
            statuses.add(last["status"])
            verdicts.add(verdict)
        mean, median, std = summarise(solve_ms)
        row.update({
            f"{tag}_status": "/".join(sorted(statuses)),
            f"{tag}_valid": "/".join(sorted(verdicts)),
            f"{tag}_mean_ms": mean, f"{tag}_median_ms": median, f"{tag}_std_ms": std,
            f"{tag}_build_ms": statistics.fmean(build_ms),
            f"{tag}_vars": last["variable_count"],
            f"{tag}_assertions": last["constraint_count"],
        })
    row["agree"] = row["f1_status"] == row["f2_status"]
    row["f1_correct"] = row["f1_status"] == row["expected"]
    row["f2_correct"] = row["f2_status"] == row["expected"]
    return row


# --------------------------------------------------------------------------
# Random instance generator for the scalability study
# --------------------------------------------------------------------------
def generate_instance(Instance, prepare_metadata, exams, seed):
    """Random instance whose size scales with `exams`.

    students = 2 * exams, each takes 2-3 random exams; slots ~ exams (enough room
    for C5's gap rule to be feasible most of the time); rooms ~ exams / 4.
    Different seeds give a natural mix of sat and unsat cases.
    """
    rng = random.Random(seed)
    inst = Instance()
    inst.number_of_exams = exams
    inst.number_of_students = exams * 2
    inst.number_of_slots = max(3, int(exams * 1.2))
    inst.number_of_rooms = max(2, exams // 4)
    inst.room_capacities = [rng.randint(4, 12) for _ in range(inst.number_of_rooms)]
    pairs = set()
    for student in range(inst.number_of_students):
        for exam in rng.sample(range(exams), min(exams, rng.randint(2, 3))):
            pairs.add((exam, student))
    inst.exams_to_students = sorted(pairs)
    return prepare_metadata(inst)


def timed_solve(solver_fn, instance, timeout_ms):
    """Solve with a Z3 timeout; returns the result dict (status may be 'unknown')."""
    z3.set_param("timeout", timeout_ms)
    try:
        return solver_fn(instance)
    finally:
        z3.set_param("timeout", 4294967295)  # restore "no timeout"


def scalability(fns, sizes, seeds, repeats, timeout_ms):
    """Time both formulations on generated instances of increasing size."""
    solve_int, solve_bool, _, validate, Instance, prepare_metadata = fns
    rows = []
    for exams in sizes:
        for seed in seeds:
            row = {"exams": exams, "seed": seed}
            for tag, solver_fn in (("f1", solve_int), ("f2", solve_bool)):
                times, status, valid, variables = [], None, "n/a", None
                for _ in range(repeats):
                    inst = generate_instance(Instance, prepare_metadata, exams, seed)
                    result = timed_solve(solver_fn, inst, timeout_ms)
                    times.append(result["solve_time_ms"])
                    status, variables = result["status"], result["variable_count"]
                    if status == "sat":
                        try:
                            validate(inst, result["timetable"])
                            valid = "valid"
                        except AssertionError as error:
                            valid = f"INVALID: {error}"
                row[f"{tag}_status"] = status
                row[f"{tag}_valid"] = valid
                row[f"{tag}_median_ms"] = statistics.median(times)
                row[f"{tag}_vars"] = variables
            rows.append(row)
            print(f"  exams={exams:<3} seed={seed}: "
                  f"F1 {row['f1_status']:<7} {row['f1_median_ms']:9.1f} ms | "
                  f"F2 {row['f2_status']:<7} {row['f2_median_ms']:9.1f} ms", flush=True)
    return rows


# --------------------------------------------------------------------------
# Output: CSV, Markdown, charts
# --------------------------------------------------------------------------
def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers, body):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return "\n".join(lines)


def write_markdown(path, main_rows, scale_rows, repeats, timeout_ms):
    out = ["# Test results: Formulation 1 (integer) vs Formulation 2 (Boolean)\n",
           f"Z3 {z3.get_version_string()}, {repeats} repeats per instance; times are the "
           "mean of `solver.check()` in ms.\n"]
    ok = lambda r, t: "yes" if r[f"{t}_correct"] else "NO"
    body = [[r["instance"], r["mode"], r["expected"], r["f1_status"], ok(r, "f1"),
             f"{r['f1_mean_ms']:.2f}", r["f2_status"], ok(r, "f2"), f"{r['f2_mean_ms']:.2f}",
             "yes" if r["agree"] else "NO",
             "valid" if r["f1_valid"] == r["f2_valid"] == "valid"
              else ("n/a" if r["expected"] == "unsat" else "CHECK")]
            for r in main_rows]
    out.append("## Correctness and timing\n")
    out.append(markdown_table(
        ["Instance", "Data mode", "Expected", "F1", "F1 ok", "F1 ms", "F2", "F2 ok", "F2 ms",
         "Agree", "Timetables"], body))
    n = len(main_rows)
    out.append(f"\n\n**Summary:** F1 correct on {sum(r['f1_correct'] for r in main_rows)}/{n}, "
               f"F2 correct on {sum(r['f2_correct'] for r in main_rows)}/{n}, "
               f"formulations agree on {sum(r['agree'] for r in main_rows)}/{n}.")
    faster1 = sum(r["f1_mean_ms"] < r["f2_mean_ms"] for r in main_rows)
    out.append(f" F1 was faster on {faster1}/{n} instances, F2 on {n - faster1}/{n}.\n")
    out.append("\n## Model size (variables / top-level assertions)\n")
    out.append(markdown_table(
        ["Instance", "F1 vars", "F1 assertions", "F2 vars", "F2 assertions"],
        [[r["instance"], r["f1_vars"], r["f1_assertions"], r["f2_vars"], r["f2_assertions"]]
         for r in main_rows]))
    if scale_rows:
        out.append(f"\n\n## Scalability on generated instances (timeout {timeout_ms} ms)\n")
        out.append(markdown_table(
            ["Exams", "Seed", "F1 status", "F1 median ms", "F1 vars", "F2 status",
             "F2 median ms", "F2 vars"],
            [[r["exams"], r["seed"], r["f1_status"], f"{r['f1_median_ms']:.1f}", r["f1_vars"],
              r["f2_status"], f"{r['f2_median_ms']:.1f}", r["f2_vars"]] for r in scale_rows]))
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")


def make_charts(out_dir, main_rows, scale_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Chart 1: per-instance mean solve time, log scale.
    rows = [r for r in main_rows if r["mode"] == "baseline"]
    labels = [Path(r["instance"]).stem for r in rows]
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar([i - 0.2 for i in x], [r["f1_mean_ms"] for r in rows], 0.4,
           label="Formulation 1 (integer)")
    ax.bar([i + 0.2 for i in x], [r["f2_mean_ms"] for r in rows], 0.4,
           label="Formulation 2 (Boolean)")
    ax.set_yscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=60, ha="right")
    ax.set_ylabel("Mean solve time (ms, log scale)")
    ax.set_title("Solve time on the 20 official instances")
    ax.legend()
    fig.tight_layout()
    fig.savefig(Path(out_dir) / "chart_official_times.png", dpi=160)
    plt.close(fig)

    # Chart 2: model size.
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar([i - 0.2 for i in x], [r["f1_vars"] for r in rows], 0.4, label="F1 variables")
    ax.bar([i + 0.2 for i in x], [r["f2_vars"] for r in rows], 0.4, label="F2 variables")
    ax.set_yscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=60, ha="right")
    ax.set_ylabel("Declared variables (log scale)")
    ax.set_title("Model size: 2E integers vs E*T*R Booleans")
    ax.legend()
    fig.tight_layout()
    fig.savefig(Path(out_dir) / "chart_variables.png", dpi=160)
    plt.close(fig)

    # Chart 3: scalability (median over seeds per size).
    if scale_rows:
        sizes = sorted({r["exams"] for r in scale_rows})
        med = lambda tag, s: statistics.median(
            r[f"{tag}_median_ms"] for r in scale_rows if r["exams"] == s)
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(sizes, [med("f1", s) for s in sizes], "o-", label="Formulation 1 (integer)")
        ax.plot(sizes, [med("f2", s) for s in sizes], "s-", label="Formulation 2 (Boolean)")
        ax.set_yscale("log")
        ax.set_xlabel("Number of exams")
        ax.set_ylabel("Median solve time (ms, log scale)")
        ax.set_title("Scalability on generated instances")
        ax.legend()
        ax.grid(True, which="both", alpha=0.3)
        fig.tight_layout()
        fig.savefig(Path(out_dir) / "chart_scalability.png", dpi=160)
        plt.close(fig)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--f1", required=True, help="folder containing Formulation1.py")
    parser.add_argument("--f2", required=True, help="folder containing Formulation2.py")
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--scale-repeats", type=int, default=3)
    parser.add_argument("--timeout-ms", type=int, default=20000)
    parser.add_argument("--skip-scalability", action="store_true")
    parser.add_argument("--out", default="results")
    args = parser.parse_args()

    fns = load_formulations(args.f1, args.f2)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    f1_dir = Path(args.f1)

    # Warm-up solve so import/JIT costs do not distort the first measurement.
    first = sorted((f1_dir / "instances").glob("sat1.txt"))
    if first:
        inst = fns[2](str(first[0]))
        fns[0](inst)
        fns[1](fns[2](str(first[0])))

    main_rows = []
    print("Official instances (baseline data):")
    for path in sorted((f1_dir / "instances").glob("*.txt"),
                       key=lambda p: (p.name.startswith("unsat"), int("".join(c for c in p.stem if c.isdigit())))):
        row = benchmark_file(path, f"instances/{path.name}", fns, args.repeats, True)
        main_rows.append(row)
        print(f"  {path.name:<14} exp={row['expected']:<5} F1={row['f1_status']:<5} "
              f"F2={row['f2_status']:<5} agree={row['agree']} "
              f"F1 {row['f1_mean_ms']:.2f} ms  F2 {row['f2_mean_ms']:.2f} ms", flush=True)

    print("Extended examples (C7 facilities + C8 durations):")
    for path in sorted((f1_dir / "examples").glob("*.txt")):
        row = benchmark_file(path, f"examples/{path.name}", fns, args.repeats, False)
        main_rows.append(row)
        print(f"  {path.name:<34} exp={row['expected']:<5} F1={row['f1_status']:<5} "
              f"F2={row['f2_status']:<5} agree={row['agree']}", flush=True)

    scale_rows = []
    if not args.skip_scalability:
        print("Scalability (generated instances):")
        scale_rows = scalability(fns, sizes=[5, 10, 15, 20, 25, 30, 40, 50],
                                 seeds=[1, 2, 3], repeats=args.scale_repeats,
                                 timeout_ms=args.timeout_ms)

    bad = [r["instance"] for r in main_rows
           if not (r["agree"] and r["f1_correct"] and r["f2_correct"])
           or "INVALID" in r["f1_valid"] + r["f2_valid"]
           or (r["expected"] == "sat" and
               (r["f1_valid"] != "valid" or r["f2_valid"] != "valid"))]
    if bad:
        raise SystemExit(f"Correctness checks failed; saved results unchanged: {bad}")

    write_csv(out_dir / "results_main.csv", main_rows)
    if scale_rows:
        write_csv(out_dir / "results_scalability.csv", scale_rows)
    write_markdown(out_dir / "summary.md", main_rows, scale_rows, args.repeats, args.timeout_ms)
    make_charts(out_dir, main_rows, scale_rows)

    print("\nAll checks passed.")
    print(f"Results written to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
