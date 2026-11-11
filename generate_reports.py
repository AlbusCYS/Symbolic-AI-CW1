"""Generate report-ready Matplotlib PNGs and summary tables from measured CSVs.

Run AFTER compare_three_formulations.py. No fabricated benchmark results are used.
Only Python standard-library modules and Matplotlib are needed.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path


def read_rows(path: Path) -> list[dict]:
    """Read benchmark CSV and fail clearly if the file is missing or empty."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Run compare_three_formulations.py first.")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"No data in {path}")
    return rows


def number(row: dict, field: str) -> float:
    return float(row[field])


def sort_instance(row: dict) -> tuple:
    name = Path(row["instance"]).stem
    is_unsat = name.startswith("unsat")
    number_part = name[5:] if is_unsat else name[3:]
    return (int(is_unsat), int(number_part) if number_part.isdigit() else 999, name)


def save(fig, path: Path):
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Created {path}")


def draw(comparison: list[dict], scalability: list[dict], output: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    output.mkdir(parents=True, exist_ok=True)
    labels = ["F1 Integer", "F2 Boolean", "F3 Hybrid"]
    # Colours are used consistently to distinguish the three formulations.
    colors = ["#326ca8", "#e07b39", "#2b927b"]
    official = [r for r in comparison if r["mode"] == "baseline"]
    instances = sorted({r["instance"] for r in official}, key=lambda name: sort_instance({"instance": name}))
    lookup = {(r["instance"], r["formulation"]): r for r in official}
    missing = [(i, f) for i in instances for f in labels if (i, f) not in lookup]
    if missing:
        raise ValueError(f"Incomplete 3-way baseline comparison: {missing[:3]}")
    if len(instances) != 20:
        print(f"NOTE: {len(instances)} official files found; expected 20 for submitted coursework.")

    # Figure 1: per-instance mean check time, log axis reveals hard UNSAT cases.
    fig, ax = plt.subplots(figsize=(12.5, 5.2))
    for idx, (form, color) in enumerate(zip(labels, colors)):
        xs = [x + (idx - 1) * .25 for x in range(len(instances))]
        times = [number(lookup[(i, form)], "mean_check_ms") for i in instances]
        ax.bar(xs, [max(t, 1e-5) for t in times], width=.24, label=form, color=color)
    ax.set_xticks(range(len(instances)), [Path(i).stem for i in instances], rotation=50, ha="right")
    ax.set_yscale("log")
    ax.set_ylabel("Mean solver.check() time (ms, log scale)")
    ax.set_title("Official instances: F1 vs F2 vs F3 (baseline)")
    ax.legend(ncol=3)
    ax.grid(axis="y", alpha=.2, which="both")
    fig.tight_layout()
    save(fig, output / "chart_official_times_3way.png")
    plt.close(fig)

    # Figure 2: decision-variable counts. These exclude solver-internal variables.
    fig, ax = plt.subplots(figsize=(12.5, 5.2))
    for idx, (form, color) in enumerate(zip(labels, colors)):
        xs = [x + (idx - 1) * .25 for x in range(len(instances))]
        values = [number(lookup[(i, form)], "variables") for i in instances]
        ax.bar(xs, [max(v, 0.01) for v in values], width=.24, label=form, color=color)
    ax.set_xticks(range(len(instances)), [Path(i).stem for i in instances], rotation=50, ha="right")
    ax.set_yscale("log")
    ax.set_ylabel("Declared decision variables (log scale)")
    ax.set_title("Decision-variable counts by formulation (official instances)")
    ax.legend(ncol=3)
    ax.grid(axis="y", alpha=.2, which="both")
    fig.tight_layout()
    save(fig, output / "chart_variables_3way.png")
    plt.close(fig)

    # Figure 3: means by outcome; keeps SAT and UNSAT categories separate.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for idx, (form, color) in enumerate(zip(labels, colors)):
        means = []
        for outcome in ("sat", "unsat"):
            samples = [number(r, "mean_check_ms") for r in official
                       if r["formulation"] == form and r["expected"] == outcome]
            means.append(statistics.fmean(samples) if samples else 0)
        ax.bar([k + (idx - 1) * .25 for k in range(2)], means, .24, color=color, label=form)
    ax.set_xticks([0, 1], ["SAT (10 cases)", "UNSAT (10 cases)"])
    ax.set_ylabel("Mean of instance-level mean solve times (ms)")
    ax.set_title("Average difficulty: SAT versus UNSAT")
    ax.legend()
    ax.grid(axis="y", alpha=.2)
    fig.tight_layout()
    save(fig, output / "chart_sat_vs_unsat_3way.png")
    plt.close(fig)

    # Figure 4: mean build time separately from check time, averaged over official data.
    fig, ax = plt.subplots(figsize=(8, 4.7))
    for idx, (form, color) in enumerate(zip(labels, colors)):
        rows = [r for r in official if r["formulation"] == form]
        build = statistics.fmean(number(r, "mean_build_ms") for r in rows)
        check = statistics.fmean(number(r, "mean_check_ms") for r in rows)
        ax.bar(idx - .17, build, .34, color=color, alpha=.55)
        ax.bar(idx + .17, check, .34, color=color)
    ax.set_xticks(range(3), labels)
    ax.set_ylabel("Mean elapsed time (ms)")
    ax.set_title("Model construction (lighter) versus solver check (darker)")
    ax.grid(axis="y", alpha=.2)
    fig.tight_layout()
    save(fig, output / "chart_build_vs_solve_3way.png")
    plt.close(fig)

    if scalability:
        # Aggregate across fixed seeds; status column allows explicit interpretation.
        fig, ax = plt.subplots(figsize=(8.7, 5))
        for form, color in zip(labels, colors):
            by_size = defaultdict(list)
            for r in scalability:
                if r["formulation"] == form and r["status"] in ("sat", "unsat"):
                    by_size[int(r["exams"])].append(number(r, "median_check_ms"))
            sizes = sorted(by_size)
            medians = [statistics.median(by_size[n]) for n in sizes]
            ax.plot(sizes, medians, marker="o", linewidth=2, label=form, color=color)
        ax.set_yscale("log")
        ax.set_xlabel("Number of exams")
        ax.set_ylabel("Median check time across seeded cases (ms, log scale)")
        ax.set_title("Scalability: fixed-seed synthetic problems (mixed SAT/UNSAT)")
        ax.legend()
        ax.grid(alpha=.2, which="both")
        fig.tight_layout()
        save(fig, output / "chart_scalability_3way.png")
        plt.close(fig)

    # A compact markdown summary table can be pasted into the report.
    table = ["# Report tables (measured data)", "", "## Official baseline results", "",
             "| Formulation | SAT correct | UNSAT correct | Mean check (ms) | Mean build (ms) |",
             "|---|---:|---:|---:|---:|"]
    for form in labels:
        rows = [r for r in official if r["formulation"] == form]
        sat = sum(r["expected"] == "sat" and r["status"] == "sat" for r in rows)
        unsat = sum(r["expected"] == "unsat" and r["status"] == "unsat" for r in rows)
        table.append(f"| {form} | {sat} | {unsat} | "
                     f"{statistics.fmean(number(r, 'mean_check_ms') for r in rows):.3f} | "
                     f"{statistics.fmean(number(r, 'mean_build_ms') for r in rows):.3f} |")
    table.extend(["", "*Timing is machine-dependent. Means aggregate the official instances equally. "
                  "Construction excludes solver.check(); alternate-model search is excluded.*", ""])
    (output / "report_tables.md").write_text("\n".join(table), encoding="utf-8")
    print(f"Created {output / 'report_tables.md'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    comparison = read_rows(args.input / "comparison_3way.csv")
    scalable_file = args.input / "scalability_3way.csv"
    scalability = read_rows(scalable_file) if scalable_file.is_file() else []
    draw(comparison, scalability, args.output)


if __name__ == "__main__":
    main()
