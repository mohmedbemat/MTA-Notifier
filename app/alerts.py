from typing import Dict, Iterable, List, Any

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