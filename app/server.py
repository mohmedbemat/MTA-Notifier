from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import List, Dict, Any
import os
import re
import json
import time
import threading
from dotenv import load_dotenv
from datetime import datetime
import requests

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
DEVICES_FILE_PATH = os.getenv("DEVICES_FILE_PATH", "data/devices.json")
PUSH_NOTIFICATIONS_ENABLED = os.getenv("PUSH_NOTIFICATIONS_ENABLED", "true").lower() == "true"
PUSH_POLL_INTERVAL_SECONDS = int(os.getenv("PUSH_POLL_INTERVAL_SECONDS", "90"))
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

station_lookup: Dict[str, tuple] = {}
device_registry: Dict[str, Dict[str, Any]] = {}
last_alert_fingerprints: set[str] = set()
registry_lock = threading.Lock()
poller_started = False


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


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _safe_json_load(path: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}

    if isinstance(data, dict):
        return {str(k): v for k, v in data.items() if isinstance(v, dict)}
    return {}


def _save_device_registry() -> None:
    os.makedirs(os.path.dirname(DEVICES_FILE_PATH) or ".", exist_ok=True)
    with open(DEVICES_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(device_registry, f, ensure_ascii=True, indent=2)


def _load_device_registry() -> None:
    global device_registry
    with registry_lock:
        device_registry = _safe_json_load(DEVICES_FILE_PATH)


def _normalize_list(values: Any) -> List[str]:
    if isinstance(values, list):
        return [str(v).strip() for v in values if str(v).strip()]
    if isinstance(values, str) and values.strip():
        return [values.strip()]
    return []


def _normalize_preferences(payload: Dict[str, Any]) -> Dict[str, Any]:
    prefs = payload if isinstance(payload, dict) else {}

    return {
        "lines": [v.upper() for v in _normalize_list(prefs.get("lines"))],
        "stations": _normalize_list(prefs.get("stations")),
        "radius_m": int(prefs.get("radius_m", 2000)) if str(prefs.get("radius_m", "")).strip() else 2000,
        "lat": prefs.get("lat"),
        "lon": prefs.get("lon"),
    }


def _normalize_platform(value: Any) -> str:
    platform = str(value or "").lower().strip()
    if platform in {"ios", "android", "web"}:
        return platform
    return "unknown"


def _valid_expo_token(token: str) -> bool:
    return bool(re.match(r"^ExponentPushToken\[[^\]]+\]$", token))


def _alert_fingerprint(alert: Dict[str, Any]) -> str:
    lines = ",".join(sorted(str(v) for v in alert.get("affected_lines", []) if v))
    stations = ",".join(sorted(str(v) for v in alert.get("affected_stations", []) if v))
    return "|".join(
        [
            str(alert.get("id", "")),
            str(alert.get("updated_at", "")),
            lines,
            stations,
            str(alert.get("description", ""))[:100],
        ]
    )


def _get_normalized_alerts() -> List[Dict[str, Any]]:
    headers = {"x-api-key": MTA_API_KEY} if MTA_API_KEY else None
    raw_alerts = fetch_json_feed(MTA_ALERTS_URL, headers=headers)
    alerts = [_normalize_alert_record(a) for a in raw_alerts]
    return [a for a in alerts if a]


def _device_matches_alert(device: Dict[str, Any], alert: Dict[str, Any]) -> bool:
    prefs = device.get("preferences") or {}
    lines = [v.upper() for v in _normalize_list(prefs.get("lines"))]
    stations = _normalize_list(prefs.get("stations"))

    line_match = True
    station_match = True

    if lines:
        line_match = any(_filter_by_line_flexible([alert], line) for line in lines)

    if stations:
        station_match = any(_filter_by_station_flexible([alert], station) for station in stations)

    if not (line_match and station_match):
        return False

    lat = prefs.get("lat")
    lon = prefs.get("lon")
    radius_m = int(prefs.get("radius_m", 2000) or 2000)
    if lat is not None and lon is not None and station_lookup:
        nearby = filter_by_location([alert], float(lat), float(lon), radius_m, station_lookup)
        return bool(nearby)

    return True


def _build_push_message(alert: Dict[str, Any]) -> Dict[str, Any]:
    lines = alert.get("affected_lines") or []
    line_label = f"{lines[0]} line" if lines else "Subway"
    title = f"{line_label} {_get_alert_type(alert).replace('_', ' ')}"
    body = (alert.get("description") or alert.get("title") or "Service update")[:160]
    return {
        "title": title,
        "body": body,
        "data": {
            "alertId": alert.get("id", ""),
            "severity": _get_severity(alert),
            "lines": lines,
        },
    }


def _mark_device_notified(token: str, fingerprint: str) -> None:
    device = device_registry.get(token)
    if not device:
        return

    fingerprints = device.get("last_notified_fingerprints") or []
    fingerprints.append(fingerprint)
    device["last_notified_fingerprints"] = fingerprints[-50:]
    device["last_notified_at"] = _utc_now_iso()


def _dispatch_push_notifications(changed_alerts: List[Dict[str, Any]]) -> None:
    if not changed_alerts:
        return

    messages: List[Dict[str, Any]] = []
    metadata: List[Dict[str, str]] = []

    with registry_lock:
        active_devices = [d for d in device_registry.values() if d.get("enabled") and d.get("token")]

        for device in active_devices:
            token = str(device.get("token"))
            sent_fingerprints = set(device.get("last_notified_fingerprints") or [])

            for alert in changed_alerts:
                fingerprint = _alert_fingerprint(alert)
                if fingerprint in sent_fingerprints:
                    continue
                if not _device_matches_alert(device, alert):
                    continue

                msg = _build_push_message(alert)
                msg["to"] = token
                msg["sound"] = "default"
                messages.append(msg)
                metadata.append({"token": token, "fingerprint": fingerprint})
                break

    if not messages:
        return

    for i in range(0, len(messages), 100):
        chunk = messages[i:i + 100]
        chunk_meta = metadata[i:i + 100]

        try:
            response = requests.post(
                EXPO_PUSH_URL,
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
                json=chunk,
                timeout=12,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            print(f"Push send failed for chunk: {exc}")
            continue

        results = payload.get("data") if isinstance(payload, dict) else []
        if not isinstance(results, list):
            continue

        with registry_lock:
            for idx, result in enumerate(results):
                if idx >= len(chunk_meta):
                    continue

                token = chunk_meta[idx]["token"]
                fingerprint = chunk_meta[idx]["fingerprint"]
                if not isinstance(result, dict):
                    continue

                if result.get("status") == "ok":
                    _mark_device_notified(token, fingerprint)
                    continue

                details = result.get("details") if isinstance(result.get("details"), dict) else {}
                if details.get("error") == "DeviceNotRegistered" and token in device_registry:
                    device_registry[token]["enabled"] = False

            _save_device_registry()


def _push_worker_loop() -> None:
    global last_alert_fingerprints
    print(f"Push worker started (interval={PUSH_POLL_INTERVAL_SECONDS}s)")

    while True:
        try:
            alerts = _get_normalized_alerts()
            current = {_alert_fingerprint(a) for a in alerts}
            changed = [a for a in alerts if _alert_fingerprint(a) not in last_alert_fingerprints]

            if changed:
                _dispatch_push_notifications(changed)

            last_alert_fingerprints = current
        except Exception as exc:
            print(f"Push worker cycle failed: {exc}")

        time.sleep(max(30, PUSH_POLL_INTERVAL_SECONDS))


def _start_push_poller() -> None:
    global poller_started
    if poller_started or not PUSH_NOTIFICATIONS_ENABLED:
        return

    thread = threading.Thread(target=_push_worker_loop, daemon=True, name="push-worker")
    thread.start()
    poller_started = True


def _should_start_background_workers() -> bool:
    # Flask's debug reloader spawns a child process; only run background workers once.
    return os.getenv("WERKZEUG_RUN_MAIN") in (None, "true")


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

        alerts = _get_normalized_alerts()

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


@app.route("/register-device", methods=["POST"])
def register_device():
    payload = request.get_json(silent=True) or {}
    token = str(payload.get("token", "")).strip()

    if not token or not _valid_expo_token(token):
        return jsonify({"success": False, "error": "Valid Expo token is required"}), 400

    platform = _normalize_platform(payload.get("platform"))
    preferences = _normalize_preferences(payload.get("preferences") or {})
    now = _utc_now_iso()

    with registry_lock:
        existing = device_registry.get(token)
        created_at = existing.get("created_at", now) if isinstance(existing, dict) else now

        device_registry[token] = {
            "token": token,
            "platform": platform,
            "enabled": True,
            "created_at": created_at,
            "last_seen_at": now,
            "preferences": preferences,
            "last_notified_fingerprints": (existing or {}).get("last_notified_fingerprints", []),
        }
        _save_device_registry()

    return jsonify({"success": True, "token": token, "preferences": preferences}), 200


@app.route("/device-preferences", methods=["PATCH"])
def update_device_preferences():
    payload = request.get_json(silent=True) or {}
    token = str(payload.get("token", "")).strip()

    if not token:
        return jsonify({"success": False, "error": "Token is required"}), 400

    with registry_lock:
        device = device_registry.get(token)
        if not device:
            return jsonify({"success": False, "error": "Device not found"}), 404

        preferences = _normalize_preferences(payload.get("preferences") or {})
        device["preferences"] = preferences
        device["last_seen_at"] = _utc_now_iso()
        device["enabled"] = True
        _save_device_registry()

    return jsonify({"success": True, "token": token, "preferences": preferences}), 200


@app.route("/unregister-device", methods=["POST"])
def unregister_device():
    payload = request.get_json(silent=True) or {}
    token = str(payload.get("token", "")).strip()
    if not token:
        return jsonify({"success": False, "error": "Token is required"}), 400

    with registry_lock:
        device = device_registry.get(token)
        if not device:
            return jsonify({"success": True, "removed": False}), 200
        device["enabled"] = False
        device["last_seen_at"] = _utc_now_iso()
        _save_device_registry()

    return jsonify({"success": True, "removed": True}), 200


@app.route("/push/devices", methods=["GET"])
def list_push_devices():
    with registry_lock:
        enabled = sum(1 for d in device_registry.values() if d.get("enabled"))
        total = len(device_registry)
    return jsonify({"success": True, "total": total, "enabled": enabled}), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    load_stations()
    _load_device_registry()
    if _should_start_background_workers():
        _start_push_poller()
    port = int(os.getenv("PORT", "4000"))
    app.run(host="0.0.0.0", port=port)
