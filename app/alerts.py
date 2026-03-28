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


def filter_by_location(alerts: Iterable[Dict], lat: float, lon: float, radius_m: float, station_lookup: Dict[str, Tuple[float, float]]) -> List[Dict]:
    """Return alerts that affect any station within `radius_m` meters of the given
    (lat, lon). `station_lookup` maps station_id -> (lat, lon).

    Notes: alerts must include `affected_stations` (list of station ids) or
    include `stations` key for this to work.
    """
    out = []
    for a in alerts:
        stns = a.get("affected_stations") or a.get("stations") or []
        for s in stns:
            coords = station_lookup.get(s)
            if not coords:
                continue
            dist = haversine_distance_m(lat, lon, coords[0], coords[1])
            if dist <= radius_m:
                out.append(a)
                break
    return out


def load_stations_from_csv(csv_content: str) -> Dict[str, Tuple[float, float]]:
    """Parse a CSV content (string) with columns at least `stop_id,stop_lat,stop_lon`.

    Returns a mapping station_id -> (lat, lon).
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    out: Dict[str, Tuple[float, float]] = {}
    for row in reader:
        sid = row.get("stop_id") or row.get("station_id") or row.get("id")
        lat = row.get("stop_lat") or row.get("lat")
        lon = row.get("stop_lon") or row.get("lon")
        if not sid or not lat or not lon:
            continue
        try:
            out[sid] = (float(lat), float(lon))
        except ValueError:
            continue
    return out
