# MTA alerts — fetching and filtering

This document explains the new scripts for fetching MTA alert data and filtering it to only show alerts relevant to a user's station or train line.

Modules added:

- `app/mta_client.py` — small HTTP client to fetch JSON alert feeds. Use `fetch_json_feed(url, ...)` or `fetch_with_api_key(url, api_key)`.
- `app/alerts.py` — filtering utilities:
  - `filter_by_station(alerts, station_id)`
  - `filter_by_line(alerts, line_id)`
  - `filter_by_location(alerts, lat, lon, radius_m, station_lookup)`
  - `load_stations_from_csv(csv_content)` to build station coordinate lookup from a CSV.

Quick example

1. Fetch alerts from your transit feed (replace URL and API key as needed):

```python
from app import mta_client, alerts

alerts_raw = mta_client.fetch_json_feed("https://example.org/mta/alerts.json")

# station lookup: map stop_id -> (lat, lon). Build from GTFS stops.txt or a CSV
station_lookup = {"STN_C": (40.0, -73.0)}

# filter alerts relevant to the user's location within 100m
relevant = alerts.filter_by_location(alerts_raw, user_lat, user_lon, 100.0, station_lookup)
```

Notes

- The client currently expects JSON feeds. If you use GTFS-RT (protobuf), we'll add a parser for that.
- The filtering functions look for common keys: `affected_stations`, `affected_lines`, `stations`, `lines`.
