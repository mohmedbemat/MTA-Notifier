from flask import Flask, request, jsonify
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

from app.mta_client import fetch_json_feed
from app.alerts import filter_by_station, filter_by_line, filter_by_location, load_stations_from_csv

load_dotenv()

app = Flask(__name__)

# Configuration
MTA_ALERTS_URL = os.getenv("MTA_ALERTS_URL", "http://localhost:5000/mock/alerts")
MTA_API_KEY = os.getenv("MTA_API_KEY", "")
STATIONS_CSV_PATH = os.getenv("STATIONS_CSV_PATH", "data/stations.csv")

# Load station coordinates at startup
station_lookup: Dict[str, tuple] = {}

def load_stations():
    """Load station data from CSV file."""
    global station_lookup
    if os.path.exists(STATIONS_CSV_PATH):
        with open(STATIONS_CSV_PATH, "r") as f:
            csv_content = f.read()
        station_lookup = load_stations_from_csv(csv_content)
        print(f"Loaded {len(station_lookup)} stations from {STATIONS_CSV_PATH}")
    else:
        print(f"Warning: Station file not found at {STATIONS_CSV_PATH}")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route("/alerts", methods=["GET", "POST"])
def get_alerts():
    """
    Fetch and filter alerts based on user context.
    
    JSON Request body:
    {
        "station_id": "001" (optional),
        "line_id": "1" (optional),
        "lat": 40.756,
        "lon": -73.987,
        "radius_m": 1000 (optional, default 2000)
    }
    
    Returns:
    {
        "success": true,
        "alerts": [...],
        "count": 3
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Validate request
        station_id = data.get("station_id")
        line_id = data.get("line_id")
        lat = data.get("lat")
        lon = data.get("lon")
        radius_m = data.get("radius_m", 2000)
        
        # Fetch MTA alerts
        try:
            headers = {}
            if MTA_API_KEY:
                headers["x-api-key"] = MTA_API_KEY
            alerts = fetch_json_feed(MTA_ALERTS_URL, headers=headers if headers else None)
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to fetch MTA alerts: {str(e)}"}), 500
        
        # Apply filters based on what's provided
        filtered = alerts
        
        if station_id:
            filtered = filter_by_station(filtered, station_id)
        
        if line_id:
            filtered = filter_by_line(filtered, line_id)
        
        if lat is not None and lon is not None:
            if not station_lookup:
                return jsonify({"success": False, "error": "Station data not loaded"}), 500
            filtered = filter_by_location(filtered, lat, lon, radius_m, station_lookup)
        
        return jsonify({
            "success": True,
            "alerts": filtered,
            "count": len(filtered)
        }), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/mock/alerts", methods=["GET"])
def mock_alerts():
    """Mock MTA alerts endpoint for development/testing."""
    return jsonify([
        {
            "id": "alert-001",
            "title": "Delays on Red Line",
            "description": "Signal problems at Times Square causing 5-10 minute delays",
            "affected_lines": ["1", "2", "3"],
            "affected_stations": ["001", "002", "003"],
            "updated_at": "2026-03-28T12:34:56Z"
        },
        {
            "id": "alert-002",
            "title": "Platform Closure at 42nd Street",
            "description": "Downtown platform closed for maintenance. Use uptown platform.",
            "affected_lines": ["4", "5"],
            "affected_stations": ["002"],
            "updated_at": "2026-03-28T12:30:00Z"
        },
        {
            "id": "alert-003",
            "title": "Service Change on Blue Line",
            "description": "No service between 14th St and Union Square due to emergency repairs",
            "affected_lines": ["L"],
            "affected_stations": ["004", "005"],
            "updated_at": "2026-03-28T11:50:00Z"
        }
    ]), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    load_stations()
    app.run(host="0.0.0.0", port=4000, debug=True)
