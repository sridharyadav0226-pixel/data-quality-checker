"""
Tests for dq_checker.py using only the Python standard library, so this
runs with zero setup — no pip install, no network.

Usage:
    python -m unittest discover tests
"""
import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from dq_checker import run_checks


def result_map(results):
    return {r.name: r.passed for r in results}


class TestDQChecker(unittest.TestCase):
    def setUp(self):
        self.fieldnames = ["order_id", "customer_email", "quantity", "unit_price"]
        self.rules = {
            "required_columns": ["order_id", "customer_email", "quantity", "unit_price"],
            "not_null_columns": ["order_id", "customer_email", "quantity"],
            "unique_columns": ["order_id"],
            "numeric_columns": ["quantity", "unit_price"],
            "value_ranges": {"quantity": [1, 1000], "unit_price": [0.01, 10000]},
        }

    def test_all_checks_pass_on_clean_data(self):
        rows = [
            {"order_id": "O1", "customer_email": "a@example.com", "quantity": "2", "unit_price": "9.99"},
            {"order_id": "O2", "customer_email": "b@example.com", "quantity": "1", "unit_price": "5.00"},
        ]
        results = run_checks(self.fieldnames, rows, self.rules)
        self.assertTrue(all(r.passed for r in results))

    def test_missing_required_column_fails(self):
        results = run_checks(["order_id", "quantity"], [], self.rules)
        rmap = result_map(results)
        self.assertFalse(rmap["required_columns"])

    def test_null_detection(self):
        rows = [{"order_id": "O1", "customer_email": "", "quantity": "1", "unit_price": "5.00"}]
        results = run_checks(self.fieldnames, rows, self.rules)
        rmap = result_map(results)
        self.assertFalse(rmap["not_null[customer_email]"])

    def test_duplicate_detection(self):
        rows = [
            {"order_id": "O1", "customer_email": "a@example.com", "quantity": "1", "unit_price": "5.00"},
            {"order_id": "O1", "customer_email": "b@example.com", "quantity": "2", "unit_price": "6.00"},
        ]
        results = run_checks(self.fieldnames, rows, self.rules)
        rmap = result_map(results)
        self.assertFalse(rmap["unique[order_id]"])

    def test_non_numeric_detection(self):
        rows = [{"order_id": "O1", "customer_email": "a@example.com", "quantity": "abc", "unit_price": "5.00"}]
        results = run_checks(self.fieldnames, rows, self.rules)
        rmap = result_map(results)
        self.assertFalse(rmap["numeric[quantity]"])

    def test_out_of_range_detection(self):
        rows = [{"order_id": "O1", "customer_email": "a@example.com", "quantity": "-5", "unit_price": "5.00"}]
        results = run_checks(self.fieldnames, rows, self.rules)
        rmap = result_map(results)
        self.assertFalse(rmap["range[quantity]"])


if __name__ == "__main__":
    unittest.main()
