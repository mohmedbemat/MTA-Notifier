from typing import Dict, Iterable, List, Any, Tuple
import csv
import io
import math

def filter_by_station(alerts: Iterable[Dict[str, Any]], station_id: str) -> List[Dict[str, Any]]:    
    out = []
    for a in alerts:
        stns = a.get("affected_stations") or a.get("stations") or []
        if station_id in stns:
            out.append(a)
    
    out = list({a["id"]: a for a in out}.values())

    return out


def filter_by_line(alerts: Iterable[Dict[str, Any]], line_id: str) -> List[Dict[str, Any]]:
    out = []
    for a in alerts:
        lines = a.get("affected_lines") or a.get("lines") or []
        if line_id in lines:
            out.append(a)
    return out


def load_stations_from_csv(csv_content: str) -> Dict[str, Tuple[str, float, float]]:
    """Build stop_id -> (name, lat, lon) lookup from CSV content."""
    lookup: Dict[str, Tuple[str, float, float]] = {}
    reader = csv.DictReader(io.StringIO(csv_content))
    for row in reader:
        stop_id = (row.get("stop_id") or "").strip()
        if not stop_id:
            continue
        try:
            name = (row.get("stop_name") or "").strip()
            lat = float(row.get("stop_lat") or "")
            lon = float(row.get("stop_lon") or "")
            lookup[stop_id] = (name, lat, lon)
        except (TypeError, ValueError):
            continue
    return lookup


def _distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate great-circle distance using Haversine formula."""
    r = 6_371_000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def filter_by_location(
    alerts: Iterable[Dict[str, Any]],
    lat: float,
    lon: float,
    radius_m: int,
    station_lookup: Dict[str, Tuple[str, float, float]],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for alert in alerts:
        station_ids = alert.get("affected_stations") or alert.get("stations") or []
        for station_id in station_ids:
            station = station_lookup.get(str(station_id))
            if not station:
                continue
            _, station_lat, station_lon = station
            if _distance_meters(lat, lon, station_lat, station_lon) <= radius_m:
                out.append(alert)
                break
    return out