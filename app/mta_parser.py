from typing import List, Dict, Any


def normalize_mta_alerts(raw_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #Convert MTA alert format into clean, consistent structure.
    alerts = []

    for entity in raw_entities:
        alert = entity.get("alert")
        if not alert:
            continue

        title = alert.get("header_text", {}).get("text", "")
        description = alert.get("description_text", {}).get("text", "")

        lines = []
        stations = []

        for informed in alert.get("informed_entity", []):
            if "route_id" in informed:
                lines.append(informed["route_id"])
            if "stop_id" in informed:
                stations.append(informed["stop_id"])

        lines = list(set(lines))
        stations = list(set(stations))

        if not title and not description:
            continue

        alerts.append({
            "id": entity.get("id"),
            "title": title,
            "description": description,
            "affected_lines": lines,
            "affected_stations": stations,
        })

    return alerts