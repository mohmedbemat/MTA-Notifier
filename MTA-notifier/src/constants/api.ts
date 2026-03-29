// Backend API configuration
// Update BACKEND_URL for different environments (development, staging, production)

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'https://mta-notifier.onrender.com'

export default {
  BACKEND_URL,
  ALERTS_ENDPOINT: `${BACKEND_URL}/alerts`,
  HEALTH_CHECK_ENDPOINT: `${BACKEND_URL}/health`,
  REGISTER_DEVICE_ENDPOINT: `${BACKEND_URL}/register-device`,
  UPDATE_DEVICE_PREFERENCES_ENDPOINT: `${BACKEND_URL}/device-preferences`,
  UNREGISTER_DEVICE_ENDPOINT: `${BACKEND_URL}/unregister-device`,
}
