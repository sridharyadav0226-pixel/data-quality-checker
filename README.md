# dq-checker

A small, dependency-free CSV data quality checker. Configure rules in a
JSON file, run it against any CSV, get a pass/fail report — and a
non-zero exit code on failure, so it can gate a CI pipeline.

No external packages required — pure Python standard library (`csv`,
`json`, `argparse`, `unittest`). Works with just `python3`, nothing to
`pip install`.

## Checks supported

| Check              | What it does                                      |
|---------------------|----------------------------------------------------|
| `required_columns`  | fails if any expected column is missing from the CSV header |
| `not_null_columns`  | fails if a column has empty values                |
| `unique_columns`    | fails if a column has duplicate values            |
| `numeric_columns`   | fails if a value in the column isn't numeric       |
| `value_ranges`      | fails if a numeric value falls outside `[min, max]` |

## Usage

```bash
python3 dq_checker.py sample_data.csv --rules rules_example.json
```

Example output against the included `sample_data.csv` (which has planted
issues — a null email, a null quantity, a duplicate order_id, a
non-numeric price, a negative quantity, and an absurd price):

```
Checked 8 rows
------------------------------------------------------------
[PASS] required_columns             all required columns present
[PASS] not_null[order_id]           no nulls
[FAIL] not_null[customer_email]     1 null row(s), e.g. rows [4]
[FAIL] not_null[quantity]           1 null row(s), e.g. rows [2]
[FAIL] unique[order_id]             1 duplicate value(s), e.g. ['O1001']
[FAIL] numeric[quantity]            1 non-numeric row(s), e.g. rows [2]
[FAIL] numeric[unit_price]          1 non-numeric row(s), e.g. rows [3]
[FAIL] range[quantity]              2 out-of-range row(s), e.g. rows [2, 7]
[FAIL] range[unit_price]            2 out-of-range row(s), e.g. rows [3, 8]
------------------------------------------------------------
2/9 checks passed
```

## Writing your own rules

Point `--rules` at any JSON file shaped like `rules_example.json`:

```json
{
  "required_columns": ["id", "email"],
  "not_null_columns": ["id"],
  "unique_columns": ["id"],
  "numeric_columns": ["amount"],
  "value_ranges": { "amount": [0, 10000] }
}
```

## Running the tests

```bash
python3 -m unittest discover tests -v
```

## Why this exists

Most portfolio ETL projects only show the "happy path." This is meant to
sit in front of a pipeline (or inside a CI job) and be the piece that
actually catches bad data before it reaches a warehouse or dashboard —
the same kind of validation/reconciliation gate referenced in the retail
ETL pipeline project.
