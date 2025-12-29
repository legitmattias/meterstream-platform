import pytest

from src.influx import _customer_filter, query_total_and_average
from src.influx import get_latest_year
from datetime import datetime


def test_customer_filter_with_id():
    s = _customer_filter("cust-xyz")
    assert 'customer' in s and 'cust-xyz' in s


def test_customer_filter_none():
    s = _customer_filter(None)
    assert s == ""


class DummyTable:
    def __init__(self, records):
        self.records = records


class DummyRecord:
    def __init__(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def get_time(self):
        # Not used in this test
        return None


class DummyQueryApi:
    def __init__(self, tables):
        self._tables = tables

    def query(self, *args, **kwargs):
        return self._tables


def test_query_total_and_average_empty():
    # When query returns no tables, function should return zeros
    dummy = DummyQueryApi(tables=[])
    result = query_total_and_average(dummy, customer_id=None, year=None)
    assert result["total"] == 0.0 and result["average"] == 0.0


def test_query_total_and_average_with_values():
    # Provide records with numeric values to ensure sum/average calculation
    records = [DummyRecord(10), DummyRecord(20), DummyRecord(30)]
    tables = [DummyTable(records)]
    dummy = DummyQueryApi(tables=tables)
    res = query_total_and_average(dummy, customer_id=None, year=None)
    assert res["total"] == pytest.approx(60.0)
    assert res["average"] == pytest.approx(20.0)


def test_get_latest_year_returns_year():
    # Create a dummy record whose get_time returns a datetime with year 2023
    class Rec:
        def __init__(self, dt):
            self._dt = dt

        def get_time(self):
            return self._dt

    tables = [DummyTable([Rec(datetime(2023, 5, 1))])]
    dummy = DummyQueryApi(tables=tables)
    y = get_latest_year(dummy, customer_id=None)
    assert y == 2023


def test_get_latest_year_none_when_no_records():
    dummy = DummyQueryApi(tables=[])
    y = get_latest_year(dummy, customer_id=None)
    assert y is None
