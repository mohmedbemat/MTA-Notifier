"""MTA API client helpers.

This module provides lightweight functions to fetch alert data from HTTP
endpoints. It intentionally keeps parsing minimal — the backend should pass
in the API URL and any auth headers required by MTA or other transit providers.

The code assumes the feed is JSON with a top-level list of alert objects, for
example:

[
  {
    "id": "alert-123",
    "title": "Delays on Red Line",
    "description": "Signal problem...",
    "affected_stations": ["STN_A", "STN_B"],
    "affected_lines": ["1", "2"],
    "updated_at": "2026-03-28T12:34:56Z"
  },
  ...
]

If you're using GTFS-RT (protobuf) we can add a GTFS-RT parser later; for
now this client focuses on JSON endpoints or proxied feeds that return JSON.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import requests


def fetch_json_feed(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetch a JSON feed of alerts and return a list of alert dicts.

    Args:
        url: endpoint returning JSON array of alert objects
        params: optional query params
        headers: optional headers (e.g., API key)
        timeout: request timeout in seconds

    Returns:
        list of dicts parsed from JSON. Raises requests.HTTPError on non-2xx.
    """
    resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
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
