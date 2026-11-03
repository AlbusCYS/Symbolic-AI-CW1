"""Multiple-solution test for Formulation 1 (the integer solver).

After the first model is found, Formulation 1 blocks that exact slot/room
assignment and calls check() again. A second 'sat' means another timetable
exists; 'unsat' means the first timetable is the only one.

Usage: python alt_solutions_check.py --f1 path/to/formulation1_folder
"""
import argparse, importlib.util, re, sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--f1", required=True)
folder = Path(parser.parse_args().f1).resolve()
sys.path.insert(0, str(folder))
from shared_input import read_file

spec = importlib.util.spec_from_file_location("f1", next(folder.glob("Formulation*1*.py")))
f1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f1)

files = sorted((folder / "instances").glob("sat*.txt"),
               key=lambda p: int(re.findall(r"\d+", p.name)[0]))
for path in files:
    result = f1.solve_integer(read_file(str(path)), check_alternatives=True)
    print(f"{path.name:<12} {'multiple solutions' if result['alternative_exists'] else 'unique solution'}")
