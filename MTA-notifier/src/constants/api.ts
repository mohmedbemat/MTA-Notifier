// Backend API configuration
// Update BACKEND_URL for different environments (development, staging, production)

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:4000'

export default {
  BACKEND_URL,
  ALERTS_ENDPOINT: `${BACKEND_URL}/alerts`,
  HEALTH_CHECK_ENDPOINT: `${BACKEND_URL}/health`,
}
