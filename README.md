# 🚆 MTA Notifier – NYC Commute Assistant

A mobile app that notifies NYC subway riders about train delays, service changes, and disruptions in real-time. The project fetches MTA alert feeds and filters them server-side on demand.

See `docs/MTA.md` for details on fetching MTA feeds and the filtering utilities in `app/alerts.py`.

## Current Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend / Mobile | React Native (Expo) | Client manages preferences and requests filtered alerts from the backend |
| Backend | Python (lightweight scripts) | Uses `requests` to pull MTA JSON feeds and `app/alerts.py` to filter relevant alerts |

## Data Flow (current)
1. Mobile app maintains user preferences (favorite station IDs and/or favorite lines) locally.
2. When the app needs updates, it calls the backend endpoint (or a function) with the user's relevant context: station id, line id, and optionally current lat/lon for proximity queries.
3. Backend fetches the MTA alerts feed (JSON) and filters alerts using `app/alerts.py` functions:
   - `filter_by_station(alerts, station_id)`
   - `filter_by_line(alerts, line_id)`
   - `filter_by_location(alerts, lat, lon, radius_m, station_lookup)`
4. Backend returns only the filtered alerts to the client. The client decides whether to show a notification.

## Developer quickstart

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run unit tests (alerts filtering logic):

   ```bash
   pytest -q
   ```

3. Use the MTA utilities (example usage documented in `docs/MTA.md`):

   - `app/mta_client.py` — fetch JSON alert feeds (`fetch_json_feed`, `fetch_with_api_key`).
   - `app/alerts.py` — filtering helpers and CSV loader for station coordinates.

## Notes & Next steps
- If you want server-side persistence later (per-user preferences or logging), we can add a lightweight DB or external store then.
- If you prefer the backend to accept device tokens and push notifications directly, we can add an authenticated endpoint and store device tokens securely (requires a DB or key-value store).
- If the production data source is GTFS-RT (protobuf), we can add a GTFS-RT parser to map realtime entities to the same alert shape consumed by `app/alerts.py`.

## Reference docs
- `docs/MTA.md` — guide for fetching and filtering MTA alerts.
# 🚆 MTA Notifier – NYC Commute Assistant

A mobile app that **notifies NYC subway riders about train delays, service changes, and disruptions** in real-time, especially for commuters who are often distracted by music, phones, or crowds. The app uses **location-based alerts** and **user preferences** to ensure you never miss an important announcement.

---

## **Features**

### **Core Features (MVP)**
- Real-time notifications for:
  - Train delays
  - Service changes or reroutes
  - Platform closures
- Personalized alerts:
  - Favorite stations (all trains at that station)
  - Favorite trains (alerts wherever that train runs)
- Location-aware notifications:
  - Only alert users when they are near a relevant station
- Simple and clean UI to display alerts

---

## **Tech Stack**

| Layer      | Technology | Notes |
|-----------|------------|-------|
| **Frontend / Mobile** | React Native | Cross-platform app (iOS + Android) |
| **Backend** | Python + Flask / FastAPI | Fetch real-time MTA GTFS-RT feeds and filter alerts by location |
| **Data Sources** | MTA GTFS-RT & Static GTFS | Real-time and static subway data, including station coordinates and line schedules |

---

## **Data Flow**

1. User installs the app and registers device token with Firebase
2. User selects favorite stations and/or trains
3. App tracks user location
4. Backend checks nearby stations and trains
5. Fetches real-time alerts from MTA GTFS-RT feed
6. Sends **push notification** to the user if relevant

---

## **How to Run (Hackathon MVP)**

1. Clone the repository  
2. Install dependencies for backend and mobile app  
3. Seed station and train data from MTA static GTFS feed  
4. Register app with Firebase for push notifications  
5. Run backend server (Flask/FastAPI)  
6. Run mobile app (React Native)  
7. Simulate location near a station to receive a test notification  

---

## **Unique Selling Point**
- **Location-based notifications**: only alert users when they are near the affected station  
- **Personalized preferences**: favorite stations or trains  
- **Community and safety-ready**: can expand to include street/sidewalk alerts for safer commutes  

---
