import { View, Text, StyleSheet } from 'react-native'

type Alert = {
  id: string
  type: string
  severity: string
  message: string
  time: string
}

const SEVERITY_COLORS: Record<string, string> = {
  high: '#FF3B30',
  medium: '#FF9500',
  low: '#34C759'
}

const TYPE_ICONS: Record<string, string> = {
  delay: '🔴',
  express_change: '⚡',
  service_change: '🔀',
  closure: '🚫'
}

export default function AlertCard({ alert }: { alert: Alert }) {
  return (
    <View style={[styles.card, { borderLeftColor: SEVERITY_COLORS[alert.severity] }]}>
      <Text style={styles.icon}>{TYPE_ICONS[alert.type] || '⚠️'}</Text>
      <View style={styles.content}>
        <Text style={styles.message}>{alert.message}</Text>
        <Text style={styles.time}>{alert.time}</Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#1a1a1a', borderRadius: 12, padding: 16, marginBottom: 12, flexDirection: 'row', borderLeftWidth: 4 },
  icon: { fontSize: 24, marginRight: 12 },
  content: { flex: 1 },
  message: { color: 'white', fontSize: 15, lineHeight: 22 },
  time: { color: '#555', fontSize: 12, marginTop: 6 }
})