"""Shared normalization helpers for QMI technical scoring."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value to the supplied interval."""

    return max(minimum, min(maximum, value))


def clamp_score(value: float) -> float:
    """Clamp a directional QMI score to [-100, 100]."""

    return clamp(float(value), -100.0, 100.0)


def linear_score(
    value: float,
    points: list[tuple[float, float]],
) -> float:
    """
    Linearly interpolate a score through ordered (x, score) points.

    Values outside the supplied x-range receive the nearest endpoint
    score. This avoids abrupt jumps at scoring thresholds while keeping
    the mathematical specification transparent.
    """

    if not points:
        raise ValueError("points cannot be empty.")

    ordered = sorted(points, key=lambda item: item[0])

    if value <= ordered[0][0]:
        return float(ordered[0][1])

    if value >= ordered[-1][0]:
        return float(ordered[-1][1])

    for (x0, y0), (x1, y1) in zip(ordered, ordered[1:]):
        if x0 <= value <= x1:
            if x1 == x0:
                return float(y1)

            ratio = (value - x0) / (x1 - x0)
            return float(y0 + ratio * (y1 - y0))

    return 0.0
