# Getting Started with MTA Notifier

## Backend Setup

### Prerequisites
- Python 3.8+
- Virtual environment created: `.venv`

### Initial Setup

1. **Create and activate virtual environment** (one-time):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the backend server**:
   ```bash
   source .venv/bin/activate
   export PYTHONPATH=.
   python3 app/server.py
   ```

   The server will start on `http://localhost:8000`

   Or use the startup script:
   ```bash
   ./start-backend.sh
   ```

### API Endpoints

- **Health Check**: `GET http://localhost:8000/health`
  - Returns: `{"status": "healthy"}`

- **Get Alerts**: `GET http://localhost:8000/alerts?station=<station>&line=<line>`
  - Query parameters:
    - `station`: Station name (optional)
    - `line`: Line ID (optional)
    - `lat`: User latitude (optional)
    - `lon`: User longitude (optional)
    - `radius_m`: Search radius in meters (optional, default 2000)
  - Returns: Filtered alerts for the given criteria

- **Mock Alerts** (for testing): `GET http://localhost:8000/mock/alerts`
  - Returns: Sample MTA alerts

### Configuration

Edit `.env` to configure:
- `MTA_ALERTS_URL` - MTA API endpoint (default: mock endpoint)
- `MTA_API_KEY` - API key for MTA (if required)
- `STATIONS_CSV_PATH` - Path to stations CSV

## Frontend Setup

### Prerequisites
- Node.js 16+
- npm or yarn

### Initial Setup

1. **Install dependencies**:
   ```bash
   cd MTA-notifier
   npm install
   ```

2. **Run the frontend**:
   ```bash
   npm start
   ```

   Or use the startup script:
   ```bash
   ./start-frontend.sh
   ```

### Environment Variables

Frontend uses `EXPO_PUBLIC_BACKEND_URL` environment variable:
```bash
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000 npm start
```

## Development Workflow

### Terminal 1 - Backend
```bash
./start-backend.sh
```

### Terminal 2 - Frontend
```bash
./start-frontend.sh
```

Then choose how to run:
- Press `w` for web
- Press `i` for iOS simulator
- Press `a` for Android emulator
- Scan QR code with Expo Go app on your phone

## Testing

### Backend Tests
```bash
source .venv/bin/activate
pytest -q
```

### Manual API Testing
```bash
# Test health check
curl http://localhost:8000/health

# Test alerts endpoint
curl "http://localhost:8000/alerts?station=Times%20Square-42%20St&line=A"

# Test mock alerts
curl http://localhost:8000/mock/alerts
```

## Troubleshooting

### Port Already in Use
If port 8000 is in use:
1. Find the process: `lsof -i :8000`
2. Kill it: `kill -9 <PID>`
3. Or modify port in `app/server.py` and `api.ts`

### CORS Errors
- Backend has CORS enabled for all origins
- Check that `BACKEND_URL` in frontend matches backend server address

### Module Not Found
- Ensure `PYTHONPATH=.` is set when running backend
- Virtual environment must be activated

## Next Steps

To complete the project, consider:

1. **Use Real MTA API**: Replace mock endpoint with actual MTA GTFS-RT feed
   - Get API key from MTA
   - Update `MTA_ALERTS_URL` in `.env`

2. **Add Push Notifications**: Implement Firebase Cloud Messaging
   - Register device tokens: `POST /register-device`
   - Push notifications when alerts change

3. **Location-Based Alerts**: Implement geolocation tracking
   - Use `expo-location` in frontend
   - Send user location to backend for filtering

4. **Expand Station Data**: Use full MTA GTFS dataset instead of 10 sample stations
   - Download from MTA: https://new.mta.info/developers
   - Parse stops.txt for all stations and coordinates

5. **Production Deployment**:
   - Use production WSGI server (Gunicorn, uWSGI)
   - Add database for user preferences
   - Deploy frontend to Expo / App Store
