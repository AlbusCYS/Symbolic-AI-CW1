
"""Check whether satisfiable official instances have multiple timetables.

Run from the repository root:
    python tests/alt_solutions_check.py --f1 .
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--f1",
        required=True,
        help="Folder containing Formulation1.py",
    )
    args = parser.parse_args()

    folder = Path(args.f1).resolve()
    solver_file = folder / "Formulation1.py"

    if not solver_file.is_file():
        parser.error(f"Cannot find {solver_file}")

    sys.path.insert(0, str(folder))
    from shared_input import read_file

    spec = importlib.util.spec_from_file_location(
        "Formulation1", solver_file
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {solver_file}")

    solver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solver)

    files = sorted(
        (folder / "instances").glob("sat*.txt"),
        key=lambda path: int(
            re.search(r"\d+", path.stem).group()
        ),
    )

    for path in files:
        result = solver.solve_integer(
            read_file(path),
            check_alternatives=True,
        )

        if result["status"] != "sat":
            label = f"unexpected status: {result['status']}"
        else:
            label = {
                True: "multiple solutions",
                False: "unique solution",
                None: "alternative status unknown",
            }[result["alternative_exists"]]

        print(f"{path.name:<12} {label}")


if __name__ == "__main__":
    main()
