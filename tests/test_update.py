#!/usr/bin/env python3
"""Tests for holiday-cn update module."""

import os
import sys
import json
from datetime import date, datetime, timedelta

# Add parent directory to path to import update module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from update import (
    _cast_date,
    _cast_int,
    _iter_date_ranges,
    ChinaTimezone,
    CustomJSONEncoder,
)


def test_cast_date_with_date_object():
    """Test _cast_date with date object."""
    d = date(2023, 1, 1)
    assert _cast_date(d) == d


def test_cast_date_with_string():
    """Test _cast_date with string."""
    d = date(2023, 1, 1)
    assert _cast_date("2023-01-01") == d


def test_cast_date_with_invalid_input():
    """Test _cast_date with invalid input."""
    try:
        _cast_date(123)
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass


def test_cast_int_with_valid_string():
    """Test _cast_int with valid string."""
    assert _cast_int("123") == 123


def test_cast_int_with_none():
    """Test _cast_int with None."""
    assert _cast_int(None) is None


def test_cast_int_with_empty_string():
    """Test _cast_int with empty string."""
    assert _cast_int("") is None


def test_iter_date_ranges_empty():
    """Test _iter_date_ranges with empty list."""
    result = list(_iter_date_ranges([]))
    assert result == []


def test_iter_date_ranges_single():
    """Test _iter_date_ranges with single day."""
    days = [{"date": "2023-01-01", "isOffDay": True, "name": "元旦"}]
    result = list(_iter_date_ranges(days))
    assert len(result) == 1
    assert result[0] == (days[0], days[0])


def test_iter_date_ranges_consecutive_same():
    """Test _iter_date_ranges with consecutive days same status."""
    days = [
        {"date": "2023-01-01", "isOffDay": True, "name": "元旦"},
        {"date": "2023-01-02", "isOffDay": True, "name": "元旦"},
        {"date": "2023-01-03", "isOffDay": True, "name": "元旦"},
    ]
    result = list(_iter_date_ranges(days))
    assert len(result) == 1
    assert result[0] == (days[0], days[2])


def test_iter_date_ranges_consecutive_different():
    """Test _iter_date_ranges with consecutive days different status."""
    days = [
        {"date": "2023-01-01", "isOffDay": True, "name": "元旦"},
        {"date": "2023-01-02", "isOffDay": False, "name": "元旦"},
        {"date": "2023-01-03", "isOffDay": True, "name": "元旦"},
    ]
    result = list(_iter_date_ranges(days))
    assert len(result) == 3


def test_iter_date_ranges_non_consecutive():
    """Test _iter_date_ranges with non-consecutive days."""
    days = [
        {"date": "2023-01-01", "isOffDay": True, "name": "元旦"},
        {"date": "2023-01-03", "isOffDay": True, "name": "元旦"},
    ]
    result = list(_iter_date_ranges(days))
    assert len(result) == 2


def test_china_timezone():
    """Test ChinaTimezone."""
    tz = ChinaTimezone()
    assert tz.tzname(None) == "UTC+8"
    assert tz.utcoffset(None) == timedelta(hours=8)
    assert tz.dst(None) == timedelta()


def test_custom_json_encoder():
    """Test CustomJSONEncoder."""
    encoder = CustomJSONEncoder()
    d = date(2023, 1, 1)
    assert encoder.default(d) == "2023-01-01"


def test_custom_json_encoder_with_non_date():
    """Test CustomJSONEncoder with non-date."""
    encoder = CustomJSONEncoder()
    try:
        encoder.default(123)
        assert False, "Should have raised TypeError"
    except TypeError:
        pass


if __name__ == "__main__":
    # Run tests
    import pytest

    pytest.main([__file__])
