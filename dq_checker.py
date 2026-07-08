"""
dq_checker.py — a small, dependency-free CSV data quality checker.

Runs configurable checks against a CSV file and reports pass/fail per
check, so it can be dropped into a CI pipeline (exits non-zero on
failure) or run ad hoc against a data file.

Checks supported (all optional, configured via a JSON rules file):
  - required_columns : every listed column must exist in the CSV header
  - not_null_columns  : listed columns must have no empty values
  - unique_columns    : listed columns must have no duplicate values
  - numeric_columns   : listed columns must parse as a number on every row
  - value_ranges      : {"column": [min, max]} — numeric bounds per column

Usage:
    python dq_checker.py data.csv --rules rules.json
    python dq_checker.py data.csv --rules rules.json --max-bad-rows 5
"""
import argparse
import csv
import json
import sys
from collections import Counter


class CheckResult:
    def __init__(self, name, passed, detail):
        self.name = name
        self.passed = passed
        self.detail = detail


def load_csv(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return reader.fieldnames or [], rows


def check_required_columns(fieldnames, rows, rules):
    required = rules.get("required_columns", [])
    missing = [c for c in required if c not in fieldnames]
    passed = len(missing) == 0
    detail = "all required columns present" if passed else f"missing columns: {missing}"
    return CheckResult("required_columns", passed, detail)


def check_not_null(fieldnames, rows, rules, max_bad_rows):
    columns = [c for c in rules.get("not_null_columns", []) if c in fieldnames]
    results = []
    for col in columns:
        bad_rows = [i + 1 for i, r in enumerate(rows) if not r.get(col, "").strip()]
        passed = len(bad_rows) == 0
        detail = "no nulls" if passed else f"{len(bad_rows)} null row(s), e.g. rows {bad_rows[:max_bad_rows]}"
        results.append(CheckResult(f"not_null[{col}]", passed, detail))
    return results


def check_unique(fieldnames, rows, rules, max_bad_rows):
    columns = [c for c in rules.get("unique_columns", []) if c in fieldnames]
    results = []
    for col in columns:
        values = [r.get(col, "") for r in rows]
        counts = Counter(values)
        dupes = [v for v, c in counts.items() if c > 1]
        passed = len(dupes) == 0
        detail = "no duplicates" if passed else f"{len(dupes)} duplicate value(s), e.g. {dupes[:max_bad_rows]}"
        results.append(CheckResult(f"unique[{col}]", passed, detail))
    return results


def check_numeric(fieldnames, rows, rules, max_bad_rows):
    columns = [c for c in rules.get("numeric_columns", []) if c in fieldnames]
    results = []
    for col in columns:
        bad_rows = []
        for i, r in enumerate(rows):
            val = r.get(col, "")
            try:
                float(val)
            except ValueError:
                bad_rows.append(i + 1)
        passed = len(bad_rows) == 0
        detail = "all numeric" if passed else f"{len(bad_rows)} non-numeric row(s), e.g. rows {bad_rows[:max_bad_rows]}"
        results.append(CheckResult(f"numeric[{col}]", passed, detail))
    return results


def check_value_ranges(fieldnames, rows, rules, max_bad_rows):
    ranges = rules.get("value_ranges", {})
    results = []
    for col, (lo, hi) in ranges.items():
        if col not in fieldnames:
            continue
        bad_rows = []
        for i, r in enumerate(rows):
            val = r.get(col, "")
            try:
                num = float(val)
                if not (lo <= num <= hi):
                    bad_rows.append(i + 1)
            except ValueError:
                bad_rows.append(i + 1)
        passed = len(bad_rows) == 0
        detail = f"all within [{lo}, {hi}]" if passed else f"{len(bad_rows)} out-of-range row(s), e.g. rows {bad_rows[:max_bad_rows]}"
        results.append(CheckResult(f"range[{col}]", passed, detail))
    return results


def run_checks(fieldnames, rows, rules, max_bad_rows=5):
    results = [check_required_columns(fieldnames, rows, rules)]
    results += check_not_null(fieldnames, rows, rules, max_bad_rows)
    results += check_unique(fieldnames, rows, rules, max_bad_rows)
    results += check_numeric(fieldnames, rows, rules, max_bad_rows)
    results += check_value_ranges(fieldnames, rows, rules, max_bad_rows)
    return results


def print_report(results, row_count):
    print(f"\nChecked {row_count} rows\n{'-' * 60}")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name:<28} {r.detail}")
    print("-" * 60)
    failed = [r for r in results if not r.passed]
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    return len(failed) == 0


def main():
    parser = argparse.ArgumentParser(description="Run configurable data quality checks against a CSV file.")
    parser.add_argument("csv_path", help="Path to the CSV file to check")
    parser.add_argument("--rules", required=True, help="Path to a JSON rules file")
    parser.add_argument("--max-bad-rows", type=int, default=5, help="Max example row numbers to show per failed check")
    args = parser.parse_args()

    with open(args.rules) as f:
        rules = json.load(f)

    fieldnames, rows = load_csv(args.csv_path)
    results = run_checks(fieldnames, rows, rules, args.max_bad_rows)
    all_passed = print_report(results, len(rows))

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
