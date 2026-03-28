import { View, Text, StyleSheet } from 'react-native'

export default function StatusBanner({ status }: { status: string }) {
  const isDisrupted = status === 'disrupted'
  return (
    <View style={[styles.banner, { backgroundColor: isDisrupted ? '#FF3B3020' : '#34C75920' }]}>
      <Text style={[styles.text, { color: isDisrupted ? '#FF3B30' : '#34C759' }]}>
        {isDisrupted ? '⚠️ Service Disrupted' : '✅ All Clear'}
      </Text>
    </View>
  )
}

const styles = StyleSheet.create({
  banner: { padding: 14, borderRadius: 10, marginBottom: 20, alignItems: 'center' },
  text: { fontSize: 16, fontWeight: 'bold' }
})