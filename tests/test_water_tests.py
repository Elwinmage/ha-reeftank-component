"""Water-test records of a Monitor: pure storage logic, no Home Assistant.

The manager, the sensors and the service are covered by the integration
tests; here only the per-chemistry record keeping and its round trip.
"""

from __future__ import annotations

from custom_components.reeftank.monitoring import Monitor, _load_tests


def test_record_keeps_one_value_per_timestamp() -> None:
    monitor = Monitor()
    monitor.record_test("kh", 100.0, 8.2, keep=100)
    # Same timestamp: the later value replaces the earlier one.
    monitor.record_test("kh", 100.0, 8.3, keep=100)
    monitor.record_test("kh", 200.0, 8.1, keep=100)
    assert monitor.recorded("kh") == [(100.0, 8.3), (200.0, 8.1)]
    assert monitor.last_recorded("kh") == (200.0, 8.1)


def test_record_sorts_and_trims_to_keep() -> None:
    monitor = Monitor()
    for stamp in (300.0, 100.0, 200.0):
        monitor.record_test("ca", stamp, 420.0, keep=2)
    # Sorted by date, only the newest two kept.
    assert [at for at, _ in monitor.recorded("ca")] == [200.0, 300.0]


def test_unknown_chemistry_is_empty() -> None:
    monitor = Monitor()
    assert monitor.recorded("mg") == []
    assert monitor.last_recorded("mg") is None


def test_round_trip_carries_the_tests() -> None:
    monitor = Monitor()
    monitor.record_test("kh", 100.0, 8.2, keep=100)
    monitor.record_test("po4", 150.0, 0.05, keep=100)
    again = Monitor.from_dict(monitor.as_dict())
    assert again.recorded("kh") == [(100.0, 8.2)]
    assert again.recorded("po4") == [(150.0, 0.05)]


def test_load_tests_drops_bad_entries_and_sorts() -> None:
    loaded = _load_tests(
        {
            "kh": [[200.0, 8.1], [100.0, 8.2], ["x", 1], [1, 2, 3], 7],
            "ca": "nonsense",
        }
    )
    assert loaded == {"kh": [(100.0, 8.2), (200.0, 8.1)]}


def test_load_tests_ignores_non_mapping() -> None:
    assert _load_tests(None) == {}
    assert _load_tests([1, 2]) == {}
