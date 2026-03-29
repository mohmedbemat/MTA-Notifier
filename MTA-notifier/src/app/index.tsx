import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native'
import { useState } from 'react'
import { useRouter } from 'expo-router'
import { LINES } from '../constants/lines'
import StationPicker from '../components/StationPicker'

export default function HomeScreen() {
  const [selectedLine, setSelectedLine] = useState<string | null>(null)
  const [station, setStation] = useState('')
  const router = useRouter()

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🚇 SubSync</Text>
      <Text style={styles.subtitle}>Never miss an announcement</Text>

      <Text style={styles.label}>Select your train line</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 24 }}>
        {LINES.map(line => (
          <TouchableOpacity
            key={line.id}
            onPress={() => setSelectedLine(line.id)}
            style={[
              styles.lineButton,
              { backgroundColor: line.color },
              selectedLine === line.id && styles.lineButtonSelected
            ]}
          >
            <Text style={styles.lineText}>{line.id}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <Text style={styles.label}>Select your station</Text>
      <StationPicker value={station} onChange={setStation} />

      <TouchableOpacity
        style={[styles.trackButton, (!selectedLine || !station) && styles.trackButtonDisabled]}
        disabled={!selectedLine || !station}
        onPress={() => router.push({
          pathname: '/dashboard',
          params: { line: selectedLine, station: station }
        })}
      >
        <Text style={styles.trackButtonText}>Track My Train →</Text>
      </TouchableOpacity>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a', padding: 24, paddingTop: 60 },
  title: { fontSize: 32, fontWeight: 'bold', color: 'white', marginBottom: 8 },
  subtitle: { fontSize: 16, color: '#888', marginBottom: 40 },
  label: { fontSize: 16, color: 'white', marginBottom: 12 },
  lineButton: { width: 48, height: 48, borderRadius: 24, justifyContent: 'center', alignItems: 'center', marginRight: 10 },
  lineButtonSelected: { borderWidth: 3, borderColor: 'white' },
  lineText: { color: 'white', fontWeight: 'bold', fontSize: 16 },
  trackButton: { backgroundColor: 'white', padding: 16, borderRadius: 12, alignItems: 'center' },
  trackButtonDisabled: { opacity: 0.3 },
  trackButtonText: { fontSize: 18, fontWeight: 'bold', color: 'black' }
})