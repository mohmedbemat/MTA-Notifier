"""MTA API client helpers.

Supports both:
- JSON alert feeds
- GTFS-RT protobuf feeds (application/octet-stream), which are used by MTA
  realtime endpoints like subway alerts.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import requests

try:
    from google.transit import gtfs_realtime_pb2
except Exception:  # pragma: no cover - guarded in runtime path below
    gtfs_realtime_pb2 = None


def _translations_to_text(translation_obj: Any) -> str:
    if not translation_obj:
        return ""
    translations = getattr(translation_obj, "translation", None)
    if not translations:
        return ""
    for item in translations:
        text = getattr(item, "text", "")
        if text:
            return text
    return ""


def _parse_gtfs_rt_alerts(content: bytes) -> List[Dict[str, Any]]:
    if gtfs_realtime_pb2 is None:
        raise RuntimeError(
            "GTFS-RT protobuf support requires gtfs-realtime-bindings. "
            "Install dependencies from requirements.txt."
        )

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(content)

    out: List[Dict[str, Any]] = []
    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue

        alert = entity.alert
        lines: List[str] = []
        stations: List[str] = []

        for informed in alert.informed_entity:
            route_id = getattr(informed, "route_id", "")
            stop_id = getattr(informed, "stop_id", "")
            if route_id:
                lines.append(route_id)
            if stop_id:
                stations.append(stop_id)

        out.append(
            {
                "id": getattr(entity, "id", "unknown") or "unknown",
                "title": _translations_to_text(getattr(alert, "header_text", None)),
                "description": _translations_to_text(getattr(alert, "description_text", None)),
                "affected_lines": list(dict.fromkeys(lines)),
                "affected_stations": list(dict.fromkeys(stations)),
                "updated_at": "",
            }
        )

    return out


def fetch_json_feed(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetch alerts and return a normalized list of alert dicts.

    Args:
        url: endpoint returning either JSON or GTFS-RT protobuf
        params: optional query params
        headers: optional headers (e.g., API key)
        timeout: request timeout in seconds

    Returns:
        list of dicts parsed from JSON/protobuf. Raises requests.HTTPError on non-2xx.
    """
    resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()

    content_type = (resp.headers.get("content-type", "") or "").lower()
    if "application/octet-stream" in content_type or "protobuf" in content_type:
        return _parse_gtfs_rt_alerts(resp.content)

    data = resp.json()
    # normalize: if the feed wraps alerts in an object, try common keys
    if isinstance(data, dict):
        for key in ("alerts", "data", "items", "entities"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # if dict but not containing list, return empty or try to coerce
        return []
    if isinstance(data, list):
        return data
    return []


def fetch_with_api_key(url: str, api_key: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """Helper for APIs that require an API key via header `x-api-key`.

    Adjust header name if required by the transit provider.
    """
    headers = {"x-api-key": api_key}
    return fetch_json_feed(url, headers=headers, timeout=timeout)
