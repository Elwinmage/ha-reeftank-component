"""Rules of the water analysis, on simulated tanks."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from datetime import UTC
from typing import Any

import pytest

from custom_components.reeftank import analysis as a
from custom_components.reeftank.analysis import Series
from custom_components.reeftank.models import MONITORING_SCHEMA

CONFIG = MONITORING_SCHEMA({})
START = 1_800_000_000 // a.DAY_S * a.DAY_S
EVENT_DAY = 16.0
DAYS = 18

Change = Callable[[float, float], float | None]


def _same(_day: float, value: float) -> float | None:
    return value


def tank(
    days: int = DAYS,
    ph: Change = _same,
    orp: Change = _same,
    co2: Change = _same,
    seed: int = 1,
) -> tuple[Series, Series, Series, float]:
    """A healthy tank (pH up by day, ORP the other way), with changes applied."""
    rng = random.Random(seed)
    series = (Series(), Series(), Series())
    time = float(START)
    for index in range(days * a.SAMPLES_PER_DAY):
        time = START + index * a.STEP_S
        day = index / a.SAMPLES_PER_DAY
        wave = math.sin((day % 1) * 2 * math.pi)
        ph_value = 8.2 + 0.1 * wave + rng.gauss(0, 0.003)
        orp_value = 350 - 50 * (ph_value - 8.2) + rng.gauss(0, 1)
        co2_value = 900 + rng.gauss(0, 10)
        values = (ph(day, ph_value), orp(day, orp_value), co2(day, co2_value))
        for one, value in zip(series, values, strict=True):
            one.add(time, value)
    return *series, time + a.STEP_S


def run(
    ph: Series | None,
    orp: Series | None,
    co2: Series | None,
    now: float,
    previous: dict[str, Any] | None = None,
    **config: Any,
) -> dict[str, Any]:
    """Analyse with the default settings."""
    return a.analyze(ph, orp, co2, now, {**CONFIG, **config}, previous or {}, UTC)


def after(change: float) -> Change:
    """A constant shift from the event on."""

    def apply(day: float, value: float) -> float:
        return value + change if day >= EVENT_DAY else value

    return apply


# ---------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------


def test_series_grid() -> None:
    """Values land on a regular grid, gaps included."""
    series = Series()
    series.add(600, None)
    assert series.start is None
    series.add(600, 1.0)
    series.add(610, 9.0)  # same slot: the first value stays
    series.add(1500, 2.0)
    assert (series.start, series.values) == (2, [1.0, None, None, 2.0])
    assert len(series) == 4
    assert series.window(300, 1200) == [None, 1.0, None]
    assert series.first_time() == 600


def test_series_edit() -> None:
    """A series is trimmed, blanked and shifted."""
    series = Series(0, [None, 1.0, 2.0, 3.0, 4.0])
    assert series.first_time() == 300
    series.trim(300)
    assert (series.start, series.values) == (1, [1.0, 2.0, 3.0, 4.0])
    series.trim(0)
    assert series.start == 1
    series.blank(600, 900)
    assert series.values == [1.0, None, 3.0, 4.0]
    series.shift_before(1200, 0.5)
    assert series.values == [1.5, None, 3.5, 4.0]
    copied = series.copy()
    copied.values[0] = 0.0
    assert series.values[0] == 1.5
    assert Series.from_dict(series.as_dict()).values == series.values


def test_empty_series() -> None:
    """Nothing to do on an empty series."""
    series = Series()
    series.trim(1000)
    series.blank(0, 1000)
    series.shift_before(1000, 1)
    assert series.first_time() is None
    assert series.window(0, 600) == [None, None]
    assert Series(5, [None]).first_time() is None


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def test_despike() -> None:
    """An outlier goes, a step stays."""
    spiked = [8.0, 8.0, 8.6, 8.0, 7.5, 8.0, 8.0, None, 9.0]
    cleaned, count = a.despike(spiked, 0.2)
    assert count == 2
    assert cleaned[2] is None and cleaned[4] is None
    stepped, count = a.despike([8.0, 8.0, 8.6, 8.6, 8.6], 0.2)
    assert count == 0
    assert a.has_step(stepped, 0.2)
    assert not a.has_step([8.0, None, 8.6], 0.2)


def test_correlation_undefined() -> None:
    """Too few points or a flat line have no correlation."""
    assert a.correlation([(1, 1), (2, 2)]) is None
    assert a.correlation([(1, 1), (1, 2), (1, 3)]) is None


def test_hourly_needs_samples() -> None:
    """An hour with too few samples is a gap."""
    assert a.hourly([1.0, None, None, None, None, None] * 2) == [None]


def test_covered() -> None:
    """A window needs most of its samples."""
    assert not a.covered([])
    assert not a.covered([1.0, None, None])
    assert a.covered([1.0, 1.0, 1.0, None])


# ---------------------------------------------------------------------------
# Learning
# ---------------------------------------------------------------------------


def test_healthy_tank_is_quiet() -> None:
    """Nothing fires on a tank behaving as usual."""
    for seed in range(3):
        report = run(*tank(seed=seed))
        assert report["learning"] == 1.0
        assert not any(report["alarms"].values()), report
        assert report["probes"] == {}


def test_no_alarm_while_learning() -> None:
    """Without a baseline, only the probes are judged."""
    ph, orp, co2, now = tank(days=5)
    report = run(ph, orp, co2, now)
    assert 0 < report["learning"] < 1
    alarms = report["alarms"]
    assert alarms.pop(a.ALARM_PROBE) is False
    assert set(alarms.values()) == {None}
    assert report["ph"]["mean_24h"] == pytest.approx(8.2, abs=0.01)
    assert report["orp"]["compensated"] == pytest.approx(350, abs=10)


def test_learning_without_recent_orp() -> None:
    """ORP gone while learning: no figure to give."""
    orp = Series()
    orp.add(START, 350.0)
    report = run(None, orp, None, START + 5 * a.DAY_S)
    assert "compensated" not in report["orp"]


def test_gaps_delay_learning() -> None:
    """A history full of holes is no baseline."""

    def holes(day: float, value: float) -> float | None:
        return value if day % 1 < 0.4 else None

    ph, orp, co2, now = tank(ph=holes, orp=holes)
    report = run(ph, orp, co2, now)
    assert report["learning"] < 1


def test_no_probe_nothing_learned() -> None:
    """Nothing configured, nothing recorded."""
    report = run(None, None, None, START)
    assert report["learning"] == 0
    assert a.learning_progress(Series(), a.Windows(START, 14)) == 0
    assert report["alarms"][a.ALARM_PROBE] is False


def test_recent_gap_stops_the_alarms() -> None:
    """Too little of the last day: no judgement, and the probe is suspect."""

    def stop(day: float, value: float) -> float | None:
        return value if day < DAYS - 0.6 else None

    ph, orp, co2, now = tank(ph=stop, orp=stop)
    report = run(ph, orp, co2, now)
    assert report["alarms"][a.ALARM_PH_BASE] is None
    assert report["alarms"][a.ALARM_ORP] is None
    assert report["alarms"][a.ALARM_PROBE] is True
    assert report["probes"] == {"ph": ["missing"], "orp": ["missing"]}


# ---------------------------------------------------------------------------
# pH
# ---------------------------------------------------------------------------


def test_ph_base_drop_and_hysteresis() -> None:
    """A lower pH fires, and clears a little below the threshold."""
    ph, orp, co2, now = tank(ph=after(-0.15))
    report = run(ph, orp, co2, now)
    assert report["alarms"][a.ALARM_PH_BASE] is True
    assert report["ph"]["drop"] == pytest.approx(0.15, abs=0.02)

    ph, orp, co2, now = tank(ph=after(-0.09))
    assert run(ph, orp, co2, now)["alarms"][a.ALARM_PH_BASE] is False
    active = {a.ALARM_PH_BASE: True}
    assert run(ph, orp, co2, now, active)["alarms"][a.ALARM_PH_BASE] is True


@pytest.mark.parametrize(
    ("co2", "cause"),
    [
        (lambda day, value: value * (1.7 if day >= EVENT_DAY else 1), a.CAUSE_CO2),
        (_same, a.CAUSE_OTHER),
    ],
)
def test_ph_drop_cause(co2: Change, cause: str) -> None:
    """The CO2 of the room tells a CO2 effect from the rest."""
    ph, orp, series, now = tank(ph=after(-0.2), co2=co2)
    report = run(ph, orp, series, now)
    assert report["alarms"][a.ALARM_PH_BASE] is True
    assert report["ph"]["cause"] == cause


def test_ph_drop_cause_unknown() -> None:
    """Without a usable CO2 reading the cause stays unknown."""

    def stopped(day: float, value: float) -> float | None:
        return value if day < EVENT_DAY else None

    def zero(_day: float, _value: float) -> float:
        return 0.0

    ph, orp, co2, now = tank(ph=after(-0.2), co2=stopped)
    assert run(ph, orp, None, now)["ph"]["cause"] == a.CAUSE_UNKNOWN
    assert run(ph, orp, co2, now)["ph"]["cause"] == a.CAUSE_UNKNOWN
    ph, orp, co2, now = tank(ph=after(-0.2), co2=zero)
    assert run(ph, orp, co2, now)["ph"]["cause"] == a.CAUSE_UNKNOWN


def test_ph_swing() -> None:
    """A wider day than usual fires."""

    def wider(day: float, value: float) -> float:
        return 8.2 + (value - 8.2) * 2 if day >= EVENT_DAY else value

    ph, orp, co2, now = tank(ph=wider)
    report = run(ph, orp, co2, now)
    assert report["alarms"][a.ALARM_PH_SWING] is True
    assert report["ph"]["swing_24h"] > report["ph"]["swing_baseline"] * 1.5


def test_ph_profile_flat_day() -> None:
    """A day losing its usual shape fires, whatever its mean."""

    def flat(day: float, value: float) -> float:
        return 8.2 + (value - 8.2) * 0.1 if day >= EVENT_DAY else value

    ph, orp, co2, now = tank(ph=flat)
    # The sine crosses its mean at the end of the day: look at its crest
    report = run(ph, orp, co2, now - 0.75 * a.DAY_S)
    assert report["alarms"][a.ALARM_PH_PROFILE] is True
    assert report["ph"]["profile_hours_off"] == CONFIG["ph_profile_hours"]


def test_ph_profile_needs_hours() -> None:
    """Too little history per hour: no profile, so no judgement."""

    def holes(day: float, value: float) -> float | None:
        return value if day % 1 > 0.35 or day >= DAYS - 1 else None

    ph, _orp, _co2, now = tank(days=9, ph=holes)
    profile = a._ph_profile(ph.window(now - 8 * a.DAY_S, now - a.DAY_S), [], now, UTC)
    assert 0 not in profile


def test_ph_without_daily_swings() -> None:
    """No full day in the baseline: the amplitude cannot be judged."""
    assert a._ph_day_swings([8.2] * 100) == []


def test_ph_profile_missing() -> None:
    """Without a usable profile the alarm stays unknown."""

    def alternate(day: float, value: float) -> float | None:
        return value if int(day * 24 * 4) % 2 else None

    ph, _orp, _co2, now = tank(ph=alternate)
    report = run(ph, None, None, now)
    assert report["alarms"][a.ALARM_PH_PROFILE] is None


def test_ph_profile_hour_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """An hour without a profile counts neither way."""
    ph, orp, co2, now = tank()
    monkeypatch.setattr(a, "_ph_profile", lambda *_: {25: (0.0, 0.0)})
    report = run(ph, orp, co2, now)
    assert report["alarms"][a.ALARM_PH_PROFILE] is False
    assert report["ph"]["profile_hours_off"] == 0


# ---------------------------------------------------------------------------
# ORP
# ---------------------------------------------------------------------------


def test_orp_drop_needs_hours() -> None:
    """A lasting drop fires, a short one does not."""
    ph, orp, co2, now = tank(orp=after(-50))
    report = run(ph, orp, co2, now)
    assert report["alarms"][a.ALARM_ORP] is True
    assert report["orp"]["drop"] == pytest.approx(50, abs=5)
    assert report["orp"]["ph_slope"] == pytest.approx(-50, abs=15)

    def short(day: float, value: float) -> float:
        return value - 50 if day >= DAYS - 0.2 else value

    ph, orp, co2, now = tank(orp=short)
    assert run(ph, orp, co2, now)["alarms"][a.ALARM_ORP] is False


def test_orp_clears_below_threshold() -> None:
    """An active alarm holds until ORP really came back."""
    ph, orp, co2, now = tank(orp=after(-27))
    assert run(ph, orp, co2, now)["alarms"][a.ALARM_ORP] is False
    assert run(ph, orp, co2, now, {a.ALARM_ORP: True})["alarms"][a.ALARM_ORP] is True


def test_orp_daily_cycle_is_compensated() -> None:
    """The daily move of the pH stays out of the compensated ORP."""
    ph, orp, co2, now = tank()
    report = run(ph, orp, co2, now - 0.25 * a.DAY_S)
    assert abs(report["orp"]["drop"]) < 3


def test_orp_alone() -> None:
    """Without pH, ORP is judged as it reads."""
    _ph, orp, _co2, now = tank(orp=after(-50))
    report = run(None, orp, None, now)
    assert report["alarms"][a.ALARM_ORP] is True
    assert "ph_slope" not in report["orp"]
    assert report["alarms"][a.ALARM_PH_BASE] is None


def test_orp_uncoupled_is_not_compensated() -> None:
    """A slope without correlation is noise."""
    rng = random.Random(3)

    def noise(_day: float, _value: float) -> float:
        return 350 + rng.gauss(0, 3)

    ph, orp, co2, now = tank(orp=noise)
    report = run(ph, orp, co2, now)
    assert "ph_slope" not in report["orp"]
    assert report["probes"] == {}


def test_orp_hole_in_recent_hours() -> None:
    """Hours without a value: no judgement on a drop."""

    def gap(day: float, value: float) -> float | None:
        return None if day >= DAYS - 0.25 else value

    ph, orp, co2, now = tank(orp=gap)
    report = run(None, orp, co2, now, orp_drop_hours=4)
    assert report["alarms"][a.ALARM_ORP] is None
    assert "compensated" not in report["orp"]
    assert report["ph"] == {}
    assert ph is not None


def test_orp_learned_without_ph_baseline() -> None:
    """A pH probe added lately does not block the ORP."""

    def late(day: float, value: float) -> float | None:
        return value if day >= DAYS - 2 else None

    ph, orp, co2, now = tank(ph=late)
    report = run(ph, orp, co2, now)
    assert report["alarms"][a.ALARM_ORP] is False
    assert report["alarms"][a.ALARM_PH_BASE] is None


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


def test_probe_frozen() -> None:
    """A value that stopped moving is no measure."""

    def frozen(day: float, value: float) -> float:
        return 8.21 if day >= EVENT_DAY else value

    ph, orp, co2, now = tank(ph=frozen)
    report = run(ph, orp, co2, now)
    assert report["alarms"][a.ALARM_PROBE] is True
    assert "frozen" in report["probes"]["ph"]


def test_probe_spikes() -> None:
    """Repeated outliers make a probe suspect, a single one does not."""
    index = {"n": 0}

    def spikes(day: float, value: float) -> float:
        index["n"] += 1
        return value + 0.5 if day >= EVENT_DAY and index["n"] % 50 == 0 else value

    ph, orp, co2, now = tank(ph=spikes)
    assert run(ph, orp, co2, now)["probes"] == {"ph": ["spikes"]}

    def one(day: float, value: float) -> float:
        return value + 0.5 if abs(day - (DAYS - 0.5)) < 0.002 else value

    ph, orp, co2, now = tank(ph=one)
    assert run(ph, orp, co2, now)["probes"] == {}


def test_probe_step() -> None:
    """A new level in one sample is no water chemistry."""
    ph, orp, co2, now = tank(ph=after(-0.4), orp=_same)
    report = run(ph, orp, co2, now - a.DAY_S * 1.5)
    assert report["probes"] == {"ph": ["step"]}


def test_probe_decoupled() -> None:
    """ORP no longer following a moving pH: one of them lies."""

    def steady(day: float, value: float) -> float:
        return 350 + math.sin(day * 300) if day >= EVENT_DAY else value

    ph, orp, co2, now = tank(orp=steady)
    assert run(ph, orp, co2, now)["probes"] == {"orp": ["decoupled"]}


def test_probe_not_decoupled_without_swing() -> None:
    """Nothing to correlate on a flat pH."""
    assert a._day_decoupled([350.0] * 288, [8.2] * 288, -0.9) is False
    assert a._day_decoupled([None] * 288, [None] * 288, -0.9) is False
    assert a._decoupled(([350.0],), ([8.2],), 0.1) == []


def test_positive_coupling_is_learned() -> None:
    """A hub compensating ORP gives a positive slope: it is learned as well."""

    def rising(_day: float, value: float) -> float:
        return 700 - value

    ph, orp, co2, now = tank(orp=rising)
    report = run(ph, orp, co2, now)
    assert report["orp"]["ph_slope"] > 0
    assert report["alarms"][a.ALARM_ORP] is False
    assert report["probes"] == {}


def test_no_series_no_reason() -> None:
    """A probe not configured has nothing wrong."""
    assert a.probe_reasons("ph", None, START) == []
    assert a.probe_reasons("ph", Series(), START) == []


# ---------------------------------------------------------------------------
# KH tests
# ---------------------------------------------------------------------------


def _kh_tests(*values: tuple[float, float]) -> list[a.KhTest]:
    """Tests given as (days before now, dKH), oldest first."""
    now = START + DAYS * a.DAY_S
    return [(now - days * a.DAY_S, value) for days, value in values]


def run_kh(tests: list[a.KhTest] | None, **changes: Any) -> dict[str, Any]:
    """Analyse a tank with KH tests."""
    ph, orp, co2, now = tank(**changes)
    return a.analyze(ph, orp, co2, now, CONFIG, {}, UTC, tests)


def test_no_kh_entity_nothing_changes() -> None:
    """Without KH tests the alarm stays unknown and the cause as it was."""
    report = run(*tank(ph=after(-0.2)))
    assert report["alarms"][a.ALARM_KH] is None
    assert "kh" not in report["ph"]
    assert "kh_test_due" not in report["ph"]
    assert report["ph"]["cause"] == a.CAUSE_OTHER


def test_kh_entity_without_tests() -> None:
    """An entity without a test yet asks for one."""
    report = run_kh([], ph=after(-0.2))
    assert report["kh"] == {}
    assert report["alarms"][a.ALARM_KH] is None
    assert report["ph"]["kh_test_due"] is True


def test_kh_drop_explains_the_ph() -> None:
    """A recent test confirming the drop names the KH."""
    tests = _kh_tests((9, 8.0), (5, 8.0), (1, 5.0))
    report = run_kh(tests, ph=after(-0.2))
    assert report["alarms"][a.ALARM_PH_BASE] is True
    assert report["ph"]["cause"] == a.CAUSE_KH
    assert report["ph"]["kh_test_due"] is False
    assert report["ph"]["kh_explained_drop"] == pytest.approx(0.204, abs=0.001)


def test_co2_explains_when_kh_is_stable() -> None:
    """KH stable and CO2 up: the air, not the water."""

    def more(day: float, value: float) -> float:
        return value * (1.7 if day >= EVENT_DAY else 1)

    tests = _kh_tests((9, 8.0), (1, 8.0))
    report = run_kh(tests, ph=after(-0.2), co2=more)
    assert report["ph"]["cause"] == a.CAUSE_CO2


def test_neither_kh_nor_co2_suspects_the_probe() -> None:
    """The pH dropped, but neither the water nor the air did."""
    tests = _kh_tests((9, 8.0), (1, 8.0))
    report = run_kh(tests, ph=after(-0.2))
    assert report["ph"]["cause"] == a.CAUSE_PROBE


def test_stable_kh_without_co2() -> None:
    """Without the CO2, a stable KH does not tell the rest apart."""
    ph, orp, _co2, now = tank(ph=after(-0.2))
    tests = _kh_tests((9, 8.0), (1, 8.0))
    report = a.analyze(ph, orp, None, now, CONFIG, {}, UTC, tests)
    assert report["ph"]["cause"] == a.CAUSE_OTHER


def test_old_test_asks_for_a_new_one() -> None:
    """A test older than the drop says nothing about it."""
    tests = _kh_tests((9, 8.0), (5, 8.0))
    report = run_kh(tests, ph=after(-0.2))
    assert report["ph"]["kh_test_due"] is True
    assert report["ph"]["cause"] == a.CAUSE_OTHER


def test_recent_test_without_reference() -> None:
    """One test alone compares with nothing."""
    assert run_kh(_kh_tests((1, 8.0)))["ph"]["kh_test_due"] is True
    assert run_kh(_kh_tests((9, 8.0), (1, 0.0)))["ph"]["kh_test_due"] is True


def test_kh_fast_change() -> None:
    """Two tests apart by more than the limit fire, in both directions."""
    for last in (7.3, 8.7):
        report = run_kh(_kh_tests((7, 8.0), (1, last)))
        assert report["alarms"][a.ALARM_KH] is True
        assert report["kh"]["change"] == pytest.approx(last - 8.0)
    assert run_kh(_kh_tests((7, 8.0), (1, 8.3)))["alarms"][a.ALARM_KH] is False


def test_kh_change_needs_close_tests() -> None:
    """Tests too far apart, or alone, tell nothing about a speed."""
    assert run_kh(_kh_tests((20, 8.0), (1, 7.0)))["alarms"][a.ALARM_KH] is None
    assert run_kh(_kh_tests((1, 7.0)))["alarms"][a.ALARM_KH] is None


def test_kh_alarm_while_learning() -> None:
    """Tests need no baseline."""
    ph, orp, co2, now = tank(days=5)
    tests = [(now - 3 * a.DAY_S, 8.0), (now - a.DAY_S, 7.0)]
    report = a.analyze(ph, orp, co2, now, CONFIG, {}, UTC, tests)
    assert report["alarms"][a.ALARM_KH] is True
    assert report["alarms"][a.ALARM_PH_BASE] is None


def test_kh_estimate_follows_ph_and_co2() -> None:
    """KH follows 10^pH x CO2 from the last test."""
    tests = _kh_tests((5, 8.0))
    stable = run_kh(tests)["kh"]["estimated"]
    assert stable == pytest.approx(8.0, abs=0.1)
    lower = run_kh(tests, ph=lambda d, v: v - 0.1 if d >= DAYS - 1 else v)
    assert lower["kh"]["estimated"] == pytest.approx(8.0 * 10**-0.1, abs=0.1)
    # Same pH with more CO2 in the air: the KH must be higher
    richer = run_kh(tests, co2=lambda d, v: v * 1.5 if d >= DAYS - 1 else v)
    assert richer["kh"]["estimated"] == pytest.approx(12.0, abs=0.2)


def test_kh_estimate_right_after_a_test() -> None:
    """The window of a test just taken ends now."""
    report = run_kh(_kh_tests((0.1, 8.0)))
    assert report["kh"]["estimated"] == pytest.approx(8.0, abs=0.1)


def test_kh_no_estimate_without_its_inputs() -> None:
    """Without CO2, recent readings or a recent test, nothing is estimated."""
    ph, orp, _co2, now = tank()
    tests = _kh_tests((5, 8.0))
    report = a.analyze(ph, orp, None, now, CONFIG, {}, UTC, tests)
    assert "estimated" not in report["kh"]
    assert report["kh"]["last"] == 8.0
    assert "estimated" not in run_kh(_kh_tests((16, 8.0)))["kh"]

    def stopped(day: float, value: float) -> float | None:
        return value if day < DAYS - 0.6 else None

    assert "estimated" not in run_kh(tests, ph=stopped)["kh"]
