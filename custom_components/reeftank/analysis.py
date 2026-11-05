"""Water analysis: compare the last 24 hours with what is usual for this tank.

Absolute limits say little about a reef: a pH swing or an ORP level that is
normal for one tank is alarming for another. So every alarm compares the tank
with its own recent history (the baseline), once enough of it was recorded.

This module is pure: no Home Assistant object, so the same rules are easy to
test and run outside the event loop. See doc/en/technical.md, "Monitoring".
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, tzinfo
from itertools import pairwise
from math import log10
from statistics import fmean, median
from typing import Any, Final

# Width of a sample. Probes are polled every minute at best, and nothing here
# needs more: 5 minutes keep a 16-day history small.
STEP_S = 300
SAMPLES_PER_HOUR = 3600 // STEP_S
SAMPLES_PER_DAY = 24 * SAMPLES_PER_HOUR
HOUR_S = 3600
DAY_S = 24 * HOUR_S

# A window is only trusted when this share of its samples exists.
MIN_COVERAGE = 0.7
# An hour needs this many samples to count.
MIN_HOUR_SAMPLES = 3
# A day of the baseline hour profile needs this many hours to be detrended.
MIN_DETREND_HOURS = 18
# Hours of the day need this many past values to form a profile.
MIN_PROFILE_VALUES = 5
# Scales a median absolute deviation into a standard deviation.
MAD_TO_SIGMA = 1.4826
# Width of the profile band, in standard deviations.
PROFILE_SIGMAS = 3.0
# An alarm clears a little below its threshold, so that it does not flap.
CLEAR_RATIO = 0.8
# A wider day than usual only counts from this much (a very flat tank
# would otherwise alarm on noise).
MIN_SWING_EXCESS = 0.02

# Probe checks.
SPIKE_LIMITS: Final = {"ph": 0.2, "orp": 40.0}
SPIKES_PER_DAY = 3
FROZEN_HOURS = 12
MISSING_HOURS = 2
# pH and ORP are coupled when their hourly variations correlate this much...
COUPLED_R = 0.5
# ...and no longer are below this, as long as pH moved enough to tell.
DECOUPLED_R = 0.1
DECOUPLED_MIN_SWING = 0.05
# Below this correlation the slope is noise: ORP is left uncompensated.
MIN_SLOPE_R = 0.3
SLOPE_LIMIT = 150.0

# KH tests. A test this old still tells what is happening now...
KH_FRESH_S = 3 * DAY_S
# ...this far apart, two tests still compare...
KH_MAX_GAP_S = 14 * DAY_S
# ...and an estimate still leans on the last one.
KH_ESTIMATE_MAX_AGE_S = 14 * DAY_S

CAUSE_CO2 = "co2"
CAUSE_KH = "kh"
CAUSE_PROBE = "probe"
CAUSE_OTHER = "other"
CAUSE_UNKNOWN = "unknown"

ALARM_PH_BASE = "ph_base_low"
ALARM_PH_SWING = "ph_swing_high"
ALARM_PH_PROFILE = "ph_profile_off"
ALARM_ORP = "orp_low"
ALARM_PROBE = "probe_suspect"
ALARM_KH = "kh_fast_change"
ALARMS: Final = (
    ALARM_PH_BASE,
    ALARM_PH_SWING,
    ALARM_PH_PROFILE,
    ALARM_ORP,
    ALARM_PROBE,
    ALARM_KH,
)

REASON_FROZEN = "frozen"
REASON_MISSING = "missing"
REASON_SPIKES = "spikes"
REASON_STEP = "step"
REASON_DECOUPLED = "decoupled"


# A KH test: when, and how much (dKH).
type KhTest = tuple[float, float]


class Series:
    """Samples of one measure, on a regular grid.

    Kept as a first slot and a list of values (None for a gap) rather than as
    (time, value) pairs: that is what makes the history cheap to store.
    """

    def __init__(
        self, start: int | None = None, values: list[float | None] | None = None
    ) -> None:
        """Create a series, from its stored form when given."""
        self.start = start
        self.values: list[float | None] = values if values is not None else []

    def __len__(self) -> int:
        """Number of slots, gaps included."""
        return len(self.values)

    def add(self, timestamp: float, value: float | None) -> None:
        """Record a value. A slot already filled keeps its first value."""
        slot = int(timestamp // STEP_S)
        if self.start is None:
            if value is None:
                return
            self.start = slot
        index = slot - self.start
        if index < len(self.values):
            return
        self.values.extend([None] * (index - len(self.values)))
        self.values.append(value)

    def trim(self, oldest: float) -> None:
        """Forget what is older than a time."""
        if self.start is None:
            return
        extra = int(oldest // STEP_S) - self.start
        if extra > 0:
            del self.values[:extra]
            self.start += extra

    def window(self, begin: float, end: float) -> list[float | None]:
        """Slots from `begin` (included) to `end` (excluded), gaps included."""
        first = int(begin // STEP_S)
        last = int(end // STEP_S)
        if self.start is None:
            return [None] * (last - first)
        return [
            self.values[slot - self.start]
            if 0 <= slot - self.start < len(self.values)
            else None
            for slot in range(first, last)
        ]

    def blank(self, begin: float, end: float) -> None:
        """Turn the slots of a period into gaps (a probe out of the water)."""
        if self.start is None:
            return
        first = max(int(begin // STEP_S) - self.start, 0)
        last = min(int(end // STEP_S) - self.start, len(self.values))
        for index in range(first, last):
            self.values[index] = None

    def shift_before(self, end: float, delta: float) -> None:
        """Add `delta` to what precedes a time (a probe was recalibrated)."""
        if self.start is None:
            return
        last = min(int(end // STEP_S) - self.start, len(self.values))
        for index in range(max(last, 0)):
            value = self.values[index]
            if value is not None:
                self.values[index] = value + delta

    def first_time(self) -> float | None:
        """Time of the oldest value."""
        if self.start is None:
            return None
        for index, value in enumerate(self.values):
            if value is not None:
                return (self.start + index) * STEP_S
        return None

    def copy(self) -> Series:
        """An independent copy, safe to read from another thread."""
        return Series(self.start, list(self.values))

    def as_dict(self) -> dict[str, Any]:
        """Stored form."""
        return {"start": self.start, "values": self.values}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Series:
        """Read the stored form."""
        return cls(data.get("start"), list(data.get("values") or []))


# ---------------------------------------------------------------------------
# Elementary statistics
# ---------------------------------------------------------------------------


def valid(values: Sequence[float | None]) -> list[float]:
    """The values of a window, without its gaps."""
    return [v for v in values if v is not None]


def percentile(values: Sequence[float], share: float) -> float:
    """Nearest-rank percentile of a non-empty list."""
    ordered = sorted(values)
    return ordered[min(int(share * len(ordered)), len(ordered) - 1)]


def swing(values: Sequence[float]) -> float:
    """Daily amplitude, not fooled by a few outliers."""
    return percentile(values, 0.95) - percentile(values, 0.05)


def covered(values: Sequence[float | None]) -> bool:
    """Whether a window holds enough samples to be trusted."""
    return bool(values) and len(valid(values)) >= MIN_COVERAGE * len(values)


def correlation(pairs: Sequence[tuple[float, float]]) -> tuple[float, float] | None:
    """Pearson correlation and slope of y over x, None when undefined."""
    if len(pairs) < 3:
        return None
    mean_x = fmean(p[0] for p in pairs)
    mean_y = fmean(p[1] for p in pairs)
    xx = sum((p[0] - mean_x) ** 2 for p in pairs)
    yy = sum((p[1] - mean_y) ** 2 for p in pairs)
    xy = sum((p[0] - mean_x) * (p[1] - mean_y) for p in pairs)
    if xx == 0 or yy == 0:
        return None
    return xy / (xx * yy) ** 0.5, xy / xx


def despike(
    values: Sequence[float | None], limit: float
) -> tuple[list[float | None], int]:
    """Remove isolated outliers; return the cleaned window and their number.

    An outlier stands away from both neighbours in the same direction. A step
    (a new level that stays) does not, and is kept.
    """
    cleaned = list(values)
    count = 0
    for index in range(1, len(values) - 1):
        before, value, after = values[index - 1 : index + 2]
        if before is None or value is None or after is None:
            continue
        if (value - before > limit and value - after > limit) or (
            before - value > limit and after - value > limit
        ):
            cleaned[index] = None
            count += 1
    return cleaned, count


def has_step(values: Sequence[float | None], limit: float) -> bool:
    """Whether consecutive samples of a cleaned window jump."""
    return any(
        before is not None and after is not None and abs(after - before) > limit
        for before, after in pairwise(values)
    )


def hourly(values: Sequence[float | None]) -> list[float | None]:
    """Hourly medians of a window, its last hour ending with the window.

    Counted from the end, so that the grid of two windows ending at the same
    time line up whatever their length.
    """
    hours: list[float | None] = []
    for end in range(len(values), 0, -SAMPLES_PER_HOUR):
        chunk = valid(values[max(end - SAMPLES_PER_HOUR, 0) : end])
        hours.append(median(chunk) if len(chunk) >= MIN_HOUR_SAMPLES else None)
    hours.reverse()
    return hours


def detrended(hours: Sequence[float | None]) -> list[float | None]:
    """Hourly values minus the centred 24 hours around them.

    Keeps the shape of the day and drops the slow moves, which would otherwise
    dominate any comparison over two weeks.
    """
    result: list[float | None] = []
    for index, value in enumerate(hours):
        around = valid(hours[max(index - 12, 0) : index + 12])
        if value is None or index < 12 or len(around) < MIN_DETREND_HOURS:
            result.append(None)
        else:
            result.append(value - fmean(around))
    return result


def hour_of_day(timestamp: float, tz: tzinfo) -> int:
    """Local hour of a time: lights follow the clock, daylight saving included."""
    return datetime.fromtimestamp(timestamp, tz).hour


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


def probe_reasons(channel: str, series: Series | None, now: float) -> list[str]:
    """What looks wrong with a probe, from its own samples.

    Needs no baseline: a broken probe must be seen while learning too, since it
    would otherwise teach the tank a wrong normal.
    """
    if series is None or series.start is None:
        return []
    limit = SPIKE_LIMITS[channel]
    missing = series.window(now - MISSING_HOURS * HOUR_S, now)
    if not valid(missing):
        return [REASON_MISSING]
    reasons: list[str] = []
    frozen = series.window(now - FROZEN_HOURS * HOUR_S, now)
    if covered(frozen) and len(set(valid(frozen))) == 1:
        reasons.append(REASON_FROZEN)
    cleaned, spikes = despike(series.window(now - DAY_S, now), limit)
    if spikes >= SPIKES_PER_DAY:
        reasons.append(REASON_SPIKES)
    if has_step(cleaned, limit):
        reasons.append(REASON_STEP)
    return reasons


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Windows:
    """The periods of an analysis."""

    now: float
    learning_days: int

    @property
    def split(self) -> float:
        """Where the baseline ends and the last 24 hours start."""
        return self.now - DAY_S

    @property
    def begin(self) -> float:
        """Where the baseline starts."""
        return self.split - self.learning_days * DAY_S


def learning_progress(series: Series | None, windows: Windows) -> float:
    """Share of the required history already recorded, 0 to 1."""
    first = series.first_time() if series else None
    if series is None or first is None:
        return 0.0
    age = (windows.now - first) / (windows.learning_days * DAY_S)
    samples = series.window(windows.begin, windows.split)
    return min(1.0, age, len(valid(samples)) / (MIN_COVERAGE * len(samples)))


def _latched(active: bool, excess: float, threshold: float) -> bool:
    """Compare with a threshold, an active alarm clearing a little below it."""
    return excess > (threshold * CLEAR_RATIO if active else threshold)


def _ph_day_swings(values: Sequence[float | None]) -> list[float]:
    """Amplitude of each covered 24-hour slice, counted from the end."""
    swings: list[float] = []
    for end in range(len(values), 0, -SAMPLES_PER_DAY):
        chunk = values[max(end - SAMPLES_PER_DAY, 0) : end]
        if len(chunk) == SAMPLES_PER_DAY and covered(chunk):
            swings.append(swing(valid(chunk)))
    return swings


def _ph_profile(
    baseline: Sequence[float | None],
    current: Sequence[float | None],
    end: float,
    tz: tzinfo,
) -> dict[int, tuple[float, float]]:
    """Usual shape of the day: hour -> (median, spread)."""
    hours = detrended(hourly([*baseline, *current]))
    # The last 24 hours only serve to detrend the end of the baseline.
    hours = hours[: len(hours) - len(current) // SAMPLES_PER_HOUR]
    by_hour: dict[int, list[float]] = {}
    for index, value in enumerate(hours):
        if value is not None:
            mid = end - (len(hours) - index - 0.5) * HOUR_S
            by_hour.setdefault(hour_of_day(mid, tz), []).append(value)
    profile: dict[int, tuple[float, float]] = {}
    for hour, values in by_hour.items():
        if len(values) >= MIN_PROFILE_VALUES:
            mid_value = median(values)
            mad = median(abs(v - mid_value) for v in values)
            profile[hour] = (mid_value, PROFILE_SIGMAS * MAD_TO_SIGMA * mad)
    return profile


def _analyze_ph(
    ph: Series,
    co2: Series | None,
    kh: Sequence[KhTest] | None,
    windows: Windows,
    config: Mapping[str, Any],
    previous: Mapping[str, Any],
    tz: tzinfo,
) -> tuple[dict[str, Any], dict[str, bool | None]]:
    """Base level, amplitude and shape of the day of the pH."""
    limit = SPIKE_LIMITS["ph"]
    baseline = despike(ph.window(windows.begin, windows.split), limit)[0]
    current = despike(ph.window(windows.split, windows.now), limit)[0]
    alarms: dict[str, bool | None] = {
        ALARM_PH_BASE: None,
        ALARM_PH_SWING: None,
        ALARM_PH_PROFILE: None,
    }
    if not covered(current):
        return {}, alarms

    samples = valid(current)
    mean = fmean(samples)
    amplitude = swing(samples)
    report: dict[str, Any] = {"mean_24h": mean, "swing_24h": amplitude}
    if learning_progress(ph, windows) < 1.0:
        return report, alarms

    # Base level
    base = median(valid(baseline))
    drop = base - mean
    report |= {"baseline": base, "drop": drop}
    report |= _co2_effect(co2, windows)
    report |= _kh_effect(kh, windows)
    report["cause"] = _cause(report, drop)
    alarms[ALARM_PH_BASE] = _latched(
        bool(previous.get(ALARM_PH_BASE)), drop, config["ph_base_drop"]
    )

    # Amplitude
    swings = _ph_day_swings(baseline)
    if swings:
        usual = median(swings)
        report["swing_baseline"] = usual
        allowed = max(usual * config["ph_swing_pct"] / 100, MIN_SWING_EXCESS)
        alarms[ALARM_PH_SWING] = _latched(
            bool(previous.get(ALARM_PH_SWING)), amplitude - usual, allowed
        )

    # Shape of the day: the last hours against the usual ones
    profile = _ph_profile(baseline, current, windows.split, tz)
    if profile:
        count = int(config["ph_profile_hours"])
        recent = hourly(current)[-count:]
        off: list[bool] = []
        for index, value in enumerate(recent):
            mid = windows.now - (len(recent) - index - 0.5) * HOUR_S
            usual_hour = profile.get(hour_of_day(mid, tz))
            if value is None or usual_hour is None:
                continue
            allowed = max(usual_hour[1], config["ph_profile_band"])
            off.append(abs(value - mean - usual_hour[0]) > allowed)
        report["profile_hours_off"] = sum(off)
        alarms[ALARM_PH_PROFILE] = len(off) == count and all(off)
    return report, alarms


def _co2_effect(co2: Series | None, windows: Windows) -> dict[str, Any]:
    """How much of a pH drop the CO2 of the room would explain.

    At constant alkalinity, pH follows -log10(CO2): a doubling of the CO2 costs
    0.3 pH. That is as much as halving the alkalinity, which is why a drop of
    the pH says nothing about KH until the CO2 is ruled out.
    """
    if co2 is None:
        return {}
    baseline = valid(co2.window(windows.begin, windows.split))
    current = co2.window(windows.split, windows.now)
    if not covered(current) or not baseline:
        return {}
    usual = median(baseline)
    level = fmean(valid(current))
    if usual <= 0 or level <= 0:
        return {}
    # Positive when the CO2 alone would lower the pH
    return {
        "co2_24h": level,
        "co2_baseline": usual,
        "co2_explained_drop": log10(level / usual),
    }


def _kh_effect(kh: Sequence[KhTest] | None, windows: Windows) -> dict[str, Any]:
    """How much of a pH drop the KH tests would explain.

    A test only says something about a drop when it is recent, and compared
    with the tests of the baseline. Without one, the alarm asks for a test.
    """
    if kh is None:
        return {}
    last_at, last = kh[-1] if kh else (0.0, 0.0)
    if windows.now - last_at > KH_FRESH_S:
        return {"kh_test_due": True}
    before = [
        value for at, value in kh if windows.begin <= at < min(last_at, windows.split)
    ]
    if not before or last <= 0:
        return {"kh_test_due": True}
    return {"kh_test_due": False, "kh_explained_drop": log10(median(before) / last)}


def _cause(report: Mapping[str, Any], drop: float) -> str:
    """What explains a drop of the pH, from what could be measured."""
    co2 = report.get("co2_explained_drop")
    kh = report.get("kh_explained_drop")
    if kh is not None and kh >= 0.5 * drop and (co2 is None or kh >= co2):
        return CAUSE_KH
    if co2 is not None and co2 >= 0.5 * drop:
        return CAUSE_CO2
    if kh is not None and co2 is not None:
        # Neither the water nor the air moved: the reading did.
        return CAUSE_PROBE
    return CAUSE_OTHER if kh is not None or co2 is not None else CAUSE_UNKNOWN


def _kh_estimate(
    last_at: float,
    last: float,
    ph: Series | None,
    co2: Series | None,
    windows: Windows,
) -> float | None:
    """KH today, from the last test and what pH and CO2 did since.

    pH ~ constant + log10(KH / CO2): both 24-hour means around the test give
    the constant. Whole days, so that the daily cycle cancels out.
    """
    if ph is None or co2 is None or windows.now - last_at > KH_ESTIMATE_MAX_AGE_S:
        return None
    end = min(last_at + DAY_S / 2, windows.now)
    ph_then = ph.window(end - DAY_S, end)
    co2_then = co2.window(end - DAY_S, end)
    ph_now = ph.window(windows.split, windows.now)
    co2_now = co2.window(windows.split, windows.now)
    windows_of_day = (ph_then, co2_then, ph_now, co2_now)
    if not all(covered(window) for window in windows_of_day):
        return None
    ph_shift = fmean(valid(ph_now)) - fmean(valid(ph_then))
    return last * 10**ph_shift * fmean(valid(co2_now)) / fmean(valid(co2_then))


def _analyze_kh(
    kh: Sequence[KhTest],
    ph: Series | None,
    co2: Series | None,
    windows: Windows,
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], bool | None]:
    """The KH tests: a move too fast between two, and an estimate since."""
    if not kh:
        return {}, None
    last_at, last = kh[-1]
    report: dict[str, Any] = {"last": last, "last_at": last_at}
    estimate = _kh_estimate(last_at, last, ph, co2, windows)
    if estimate is not None:
        report["estimated"] = estimate
    if len(kh) < 2 or last_at - kh[-2][0] > KH_MAX_GAP_S:
        return report, None
    change = last - kh[-2][1]
    report["change"] = change
    return report, abs(change) > config["kh_change_max"]


def _orp_coupling(
    orp_values: Sequence[float | None], ph_values: Sequence[float | None]
) -> tuple[float, float] | None:
    """Correlation and slope of ORP over pH, on their hourly variations.

    The last 24 hours only serve to detrend the end of the baseline: what is
    judged must not teach what is usual.
    """
    orp_hours = detrended(hourly(orp_values))[:-24]
    ph_hours = detrended(hourly(ph_values))[:-24]
    pairs = [
        (p, o)
        for p, o in zip(ph_hours, orp_hours, strict=True)
        if p is not None and o is not None
    ]
    return correlation(pairs)


def _compensated(
    orp_values: Sequence[float | None],
    ph_values: Sequence[float | None] | None,
    slope: float,
    ph_ref: float,
) -> list[float | None]:
    """ORP with the part due to the pH of the moment taken out."""
    if ph_values is None or slope == 0:
        return list(orp_values)
    return [
        None if o is None or p is None else o - slope * (p - ph_ref)
        for o, p in zip(orp_values, ph_values, strict=False)
    ]


def _analyze_orp(
    orp: Series,
    ph: Series | None,
    windows: Windows,
    config: Mapping[str, Any],
    previous: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, bool | None], list[str]]:
    """Level of the ORP, once freed from the daily move of the pH."""
    orp_limit = SPIKE_LIMITS["orp"]
    ph_limit = SPIKE_LIMITS["ph"]
    orp_base = despike(orp.window(windows.begin, windows.split), orp_limit)[0]
    orp_now = despike(orp.window(windows.split, windows.now), orp_limit)[0]
    ph_base = ph_now = None
    if ph is not None:
        ph_base = despike(ph.window(windows.begin, windows.split), ph_limit)[0]
        ph_now = despike(ph.window(windows.split, windows.now), ph_limit)[0]

    alarms: dict[str, bool | None] = {ALARM_ORP: None}
    report: dict[str, Any] = {}
    reasons: list[str] = []
    if learning_progress(orp, windows) < 1.0:
        tail = valid(orp_now[-SAMPLES_PER_HOUR:])
        if tail:
            report["compensated"] = median(tail)
        return report, alarms, reasons

    slope = 0.0
    ph_ref = 0.0
    if ph_base is not None and ph_now is not None and valid(ph_base):
        ph_ref = median(valid(ph_base))
        coupling = _orp_coupling([*orp_base, *orp_now], [*ph_base, *ph_now])
        if coupling is not None and abs(coupling[0]) >= MIN_SLOPE_R:
            slope = max(-SLOPE_LIMIT, min(SLOPE_LIMIT, coupling[1]))
            report |= {"ph_correlation": coupling[0], "ph_slope": slope}
            reasons = _decoupled(
                (orp_base[-SAMPLES_PER_DAY:], orp_now),
                (ph_base[-SAMPLES_PER_DAY:], ph_now),
                coupling[0],
            )

    baseline = valid(_compensated(orp_base, ph_base, slope, ph_ref))
    current = _compensated(orp_now, ph_now, slope, ph_ref)
    if not baseline or not covered(current):
        return report, alarms, reasons

    base = median(baseline)
    hours = int(config["orp_drop_hours"])
    recent = hourly(current)[-hours:]
    tail = valid(recent)
    report |= {"baseline": base}
    if not tail:
        return report, alarms, reasons
    report |= {"compensated": tail[-1], "drop": base - tail[-1]}
    threshold = config["orp_drop_mv"]
    if previous.get(ALARM_ORP):
        alarms[ALARM_ORP] = base - tail[-1] > threshold * CLEAR_RATIO
    else:
        alarms[ALARM_ORP] = len(tail) == len(recent) and all(
            base - value > threshold for value in tail
        )
    return report, alarms, reasons


def _day_decoupled(
    orp_day: Sequence[float | None],
    ph_day: Sequence[float | None],
    usual: float,
) -> bool:
    """Whether pH and ORP did not move together over one day."""
    samples = valid(ph_day)
    if not samples or swing(samples) < DECOUPLED_MIN_SWING:
        return False
    pairs = [
        (p, o)
        for p, o in zip(hourly(ph_day), hourly(orp_day), strict=False)
        if p is not None and o is not None
    ]
    today = correlation(pairs)
    # Compared along the usual direction: with a usual r of -0.8, a r of +0.5
    # is as lost as a r of 0.
    return today is not None and today[0] * (1 if usual > 0 else -1) < DECOUPLED_R


def _decoupled(
    orp_days: Sequence[Sequence[float | None]],
    ph_days: Sequence[Sequence[float | None]],
    usual: float,
) -> list[str]:
    """Whether pH and ORP stopped moving together, as they usually do.

    Two days in a row: on a small daily move, a slow drift of the ORP can hide
    the coupling for a day without anything being wrong.
    """
    if abs(usual) < COUPLED_R:
        return []
    days = zip(orp_days, ph_days, strict=True)
    if all(_day_decoupled(orp_day, ph_day, usual) for orp_day, ph_day in days):
        return [REASON_DECOUPLED]
    return []


def analyze(
    ph: Series | None,
    orp: Series | None,
    co2: Series | None,
    now: float,
    config: Mapping[str, Any],
    previous: Mapping[str, Any],
    tz: tzinfo,
    kh: Sequence[KhTest] | None = None,
) -> dict[str, Any]:
    """Analyse the samples of an aquarium.

    `previous` holds the alarms of the last analysis. `kh` holds the KH tests,
    oldest first, None when no entity gives them. An alarm is True, False, or
    None when it cannot be told yet. The result is JSON-friendly.
    """
    windows = Windows(now, int(config["learning_days"]))
    alarms: dict[str, bool | None] = dict.fromkeys(ALARMS)
    report: dict[str, Any] = {"ph": {}, "orp": {}}
    probes: dict[str, list[str]] = {}

    if ph is not None:
        report["ph"], ph_alarms = _analyze_ph(
            ph, co2, kh, windows, config, previous, tz
        )
        alarms |= ph_alarms
        probes["ph"] = probe_reasons("ph", ph, now)
    if orp is not None:
        report["orp"], orp_alarms, decoupled = _analyze_orp(
            orp, ph, windows, config, previous
        )
        alarms |= orp_alarms
        probes["orp"] = probe_reasons("orp", orp, now) + decoupled

    if kh is not None:
        report["kh"], alarms[ALARM_KH] = _analyze_kh(kh, ph, co2, windows, config)

    alarms[ALARM_PROBE] = any(probes.values())
    progress = [learning_progress(s, windows) for s in (ph, orp) if s is not None]
    report |= {
        "alarms": alarms,
        "probes": {k: v for k, v in probes.items() if v},
        "learning": min(progress, default=0.0),
    }
    return report
