import { View, Text, ScrollView, StyleSheet, Platform } from 'react-native'
import { useLocalSearchParams } from 'expo-router'
import { useEffect, useState } from 'react'
import axios from 'axios'
import * as Notifications from 'expo-notifications'
import * as Device from 'expo-device'
import Constants from 'expo-constants'
import api from '../constants/api'
import AlertCard from '../components/AlertCard'
import StatusBanner from '../components/StatusBanner'

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
})

export default function DashboardScreen() {
  const { line, station } = useLocalSearchParams()
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const registerPushNotifications = async () => {
      if (!Device.isDevice) {
        return
      }

      try {
        if (Platform.OS === 'android') {
          await Notifications.setNotificationChannelAsync('default', {
            name: 'default',
            importance: Notifications.AndroidImportance.MAX,
            sound: 'default',
          })
        }

        const currentPerms = await Notifications.getPermissionsAsync()
        let status = currentPerms.status

        if (status !== 'granted') {
          const requested = await Notifications.requestPermissionsAsync()
          status = requested.status
        }

        if (status !== 'granted') {
          return
        }

        const projectId =
          Constants.expoConfig?.extra?.eas?.projectId ||
          Constants.easConfig?.projectId

        const tokenResponse = projectId
          ? await Notifications.getExpoPushTokenAsync({ projectId })
          : await Notifications.getExpoPushTokenAsync()

        const resolvedLine = typeof line === 'string' ? line : ''
        const resolvedStation = typeof station === 'string' ? station : ''

        await axios.post(api.REGISTER_DEVICE_ENDPOINT, {
          token: tokenResponse.data,
          platform: Platform.OS,
          preferences: {
            lines: resolvedLine ? [resolvedLine] : [],
            stations: resolvedStation ? [resolvedStation] : [],
          },
        })
      } catch (err) {
        console.warn('Push registration failed:', err)
      }
    }

    registerPushNotifications()
  }, [line, station])

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await axios.get(
          `${api.ALERTS_ENDPOINT}?station=${station}&line=${line}`
        )
        setData(res.data)
        setError('')
      } catch (err) {
        console.warn('Failed to fetch alerts:', err)
        setError('Could not load live alerts. Check backend and API key configuration.')
        setData(null)
      }
    }

    fetchAlerts()
    const interval = setInterval(fetchAlerts, 30000)
    return () => clearInterval(interval)
  }, [station, line])

  if (error) return (
    <View style={styles.loading}>
      <Text style={styles.errorText}>{error}</Text>
    </View>
  )

  if (!data) return (
    <View style={styles.loading}>
      <Text style={{ color: 'white' }}>Loading...</Text>
    </View>
  )

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.station}>{station}</Text>
      <Text style={styles.line}>Line {line}</Text>
      <Text style={styles.updated}>Updated {data.last_updated}</Text>
      <StatusBanner status={data.status} />
      {data.alerts.map((alert: any) => (
        <AlertCard key={alert.id} alert={alert} />
      ))}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a', padding: 24, paddingTop: 60 },
  loading: { flex: 1, backgroundColor: '#0a0a0a', justifyContent: 'center', alignItems: 'center' },
  errorText: { color: '#FF3B30', textAlign: 'center', paddingHorizontal: 20 },
  station: { fontSize: 28, fontWeight: 'bold', color: 'white' },
  line: { fontSize: 18, color: '#888', marginTop: 4 },
  updated: { fontSize: 12, color: '#555', marginTop: 4, marginBottom: 20 },
})