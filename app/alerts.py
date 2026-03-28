"""Alert cleaning and filtering helpers.

This module provides pure-Python utilities to filter a list of alert dicts
down to those relevant to a given user, either by station id, line id, or
geographic proximity to the user's location.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple
import math
import csv
import io


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance between two points in meters."""
    R = 6371000.0  # earth radius meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def filter_by_station(alerts: Iterable[Dict], station_id: str) -> List[Dict]:
    """Return alerts that reference the given station id in their
    `affected_stations` (if present).
    """
    out = []
    for a in alerts:
        stns = a.get("affected_stations") or a.get("stations") or []
        if station_id in stns:
            out.append(a)
    return out


def filter_by_line(alerts: Iterable[Dict], line_id: str) -> List[Dict]:
    """Return alerts that reference the given line id in `affected_lines`.
    """
    out = []
    for a in alerts:
        lines = a.get("affected_lines") or a.get("lines") or []
        if line_id in lines:
            out.append(a)
    return out