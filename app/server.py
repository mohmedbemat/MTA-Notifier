from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import List, Dict, Any
import os
import re
from dotenv import load_dotenv
from datetime import datetime

from app.mta_client import fetch_json_feed
from app.alerts import filter_by_station, filter_by_line, filter_by_location, load_stations_from_csv

load_dotenv()

app = Flask(__name__)
CORS(app)

DEFAULT_MTA_ALERTS_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys/subway-alerts.json"


def _looks_like_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _resolve_mta_config() -> tuple[str, str]:
    """Resolve URL/API key and tolerate swapped .env values."""
    raw_url = os.getenv("MTA_ALERTS_URL", "").strip()
    raw_key = os.getenv("MTA_API_KEY", "").strip()

    if raw_url and not _looks_like_url(raw_url) and _looks_like_url(raw_key):
        raw_url, raw_key = raw_key, raw_url

    if not raw_url:
        raw_url = DEFAULT_MTA_ALERTS_URL

    return raw_url, raw_key


MTA_ALERTS_URL, MTA_API_KEY = _resolve_mta_config()
STATIONS_CSV_PATH = os.getenv("STATIONS_CSV_PATH", "data/stations.csv")

station_lookup: Dict[str, tuple] = {}


def _get_alert_type(alert: Dict[str, Any]) -> str:
    desc = (alert.get("description", "") + alert.get("title", "")).lower()
    if "delay" in desc:
        return "delay"
    if "service change" in desc or "reroute" in desc:
        return "service_change"
    if "express" in desc:
        return "express_change"
    if "closure" in desc or "closed" in desc:
        return "closure"
    return "service_change"


def _get_severity(alert: Dict[str, Any]) -> str:
    desc = (alert.get("description", "") + alert.get("title", "")).lower()
    if any(word in desc for word in ["emergency", "suspended", "outage", "closure"]):
        return "high"
    if any(word in desc for word in ["delay", "reroute", "change"]):
        return "medium"
    return "low"


def _format_time(timestamp: str) -> str:
    try:
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%I:%M %p")
    except Exception:
        pass
    return datetime.now().strftime("%I:%M %p")


def _translations_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        translations = value.get("translation")
        if isinstance(translations, list):
            for item in translations:
                text = item.get("text") if isinstance(item, dict) else None
                if text:
                    return text
    return ""


def _normalize_alert_record(alert: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(alert, dict):
        return {}

    if isinstance(alert.get("alert"), dict):
        payload = alert["alert"]
        informed = payload.get("informed_entity") or []

        lines: List[str] = []
        stations: List[str] = []
        for entity in informed:
            if not isinstance(entity, dict):
                continue
            route_id = entity.get("route_id")
            stop_id = entity.get("stop_id")
            if route_id:
                lines.append(str(route_id))
            if stop_id:
                stations.append(str(stop_id))

        title = _translations_to_text(payload.get("header_text"))
        description = _translations_to_text(payload.get("description_text"))
        if not description:
            description = title

        return {
            "id": str(alert.get("id", "unknown")),
            "title": title,
            "description": description,
            "affected_lines": list(dict.fromkeys(lines)),
            "affected_stations": list(dict.fromkeys(stations)),
            "updated_at": datetime.now().isoformat(),
        }

    return {
        "id": str(alert.get("id", "unknown")),
        "title": str(alert.get("title", "") or ""),
        "description": str(alert.get("description", "") or ""),
        "affected_lines": alert.get("affected_lines") or alert.get("lines") or [],
        "affected_stations": alert.get("affected_stations") or alert.get("stations") or [],
        "updated_at": str(alert.get("updated_at", "") or ""),
    }


def _filter_by_station_flexible(alerts: List[Dict[str, Any]], station: str) -> List[Dict[str, Any]]:
    id_matches = filter_by_station(alerts, station)
    if id_matches:
        return id_matches

    needle = station.lower().strip()
    return [
        a
        for a in alerts
        if needle and needle in ((a.get("title", "") + " " + a.get("description", "")).lower())
    ]


def _filter_by_line_flexible(alerts: List[Dict[str, Any]], line: str) -> List[Dict[str, Any]]:
    id_matches = filter_by_line(alerts, line)
    if id_matches:
        return id_matches

    token = line.strip()
    if not token:
        return alerts

    pattern = re.compile(rf"\\b{re.escape(token)}\\b", flags=re.IGNORECASE)
    return [
        a
        for a in alerts
        if pattern.search(a.get("title", "") + " " + a.get("description", ""))
    ]


def load_stations() -> None:
    global station_lookup
    if os.path.exists(STATIONS_CSV_PATH):
        with open(STATIONS_CSV_PATH, "r", encoding="utf-8") as f:
            csv_content = f.read()
        station_lookup = load_stations_from_csv(csv_content)
        print(f"Loaded {len(station_lookup)} stations from {STATIONS_CSV_PATH}")
    else:
        print(f"Warning: Station file not found at {STATIONS_CSV_PATH}")


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


@app.route("/alerts", methods=["GET"])
def get_alerts():
    try:
        station = request.args.get("station", "")
        line = request.args.get("line", "")
        lat = request.args.get("lat", type=float, default=None)
        lon = request.args.get("lon", type=float, default=None)
        radius_m = request.args.get("radius_m", 2000, type=int)

        headers = {"x-api-key": MTA_API_KEY} if MTA_API_KEY else None
        raw_alerts = fetch_json_feed(MTA_ALERTS_URL, headers=headers)
        alerts = [_normalize_alert_record(a) for a in raw_alerts]
        alerts = [a for a in alerts if a]

        filtered = alerts

        if station:
            filtered = _filter_by_station_flexible(filtered, station)

        if line:
            filtered = _filter_by_line_flexible(filtered, line)

        if lat is not None and lon is not None and station_lookup:
            filtered = filter_by_location(filtered, lat, lon, radius_m, station_lookup)

        formatted_alerts = []
        for alert in filtered[:10]:
            formatted_alerts.append(
                {
                    "id": alert.get("id", "unknown"),
                    "type": _get_alert_type(alert),
                    "severity": _get_severity(alert),
                    "message": alert.get("description", alert.get("title", "")),
                    "time": _format_time(alert.get("updated_at", "")),
                }
            )

        status = "disrupted" if formatted_alerts else "normal"

        return (
            jsonify(
                {
                    "station": station or "NYC Subway",
                    "line": line or "All",
                    "status": status,
                    "last_updated": datetime.now().strftime("%I:%M %p"),
                    "alerts": formatted_alerts,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "station": station if "station" in locals() else "",
                    "line": line if "line" in locals() else "",
                    "status": "error",
                    "last_updated": "now",
                    "alerts": [],
                    "error": str(e),
                }
            ),
            500,
        )


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    load_stations()
    port = int(os.getenv("PORT", "4000"))
    app.run(host="0.0.0.0", port=port, debug=True)
