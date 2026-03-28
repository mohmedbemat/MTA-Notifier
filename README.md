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
| **Database** | SQLite | Store user preferences (favorite stations, favorite trains, device tokens) |
| **Push Notifications** | Firebase Cloud Messaging | Send location-based alerts to users’ devices |
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

## **Database Structure**

**Users**
- `user_id` (PK)  
- `name`  
- `device_token` (for notifications)  

**Stations**
- `station_id` (PK)  
- `name`  
- `lat`, `lon`  
- `trains` (array of trains at this station)  

**Trains**
- `train_id` (PK, e.g., A, B, 1, 2, 5)  
- `line_name` (optional)  

**UserPreferences**
- `pref_id` (PK)  
- `user_id` (FK)  
- `station_id` (FK, optional)  
- `train_id` (FK, optional)  

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
