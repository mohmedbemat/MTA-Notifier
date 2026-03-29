import { useState } from 'react'
import {
  View, Text, TextInput, TouchableOpacity,
  FlatList, Modal, StyleSheet
} from 'react-native'
import { STATIONS } from '../constants/stations'

type Props = {
  value: string
  onChange: (station: string) => void
}

// remove duplicates
const UNIQUE_STATIONS = [...new Set(STATIONS)].sort()

export default function StationPicker({ value, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')

  const filtered = UNIQUE_STATIONS.filter(s =>
    s.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <>
      <TouchableOpacity style={styles.trigger} onPress={() => setOpen(true)}>
        <Text style={value ? styles.triggerTextSelected : styles.triggerPlaceholder}>
          {value || 'Search for your station...'}
        </Text>
        <Text style={styles.arrow}>▼</Text>
      </TouchableOpacity>

      <Modal visible={open} animationType="slide">
        <View style={styles.modal}>

          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Select Station</Text>
            <TouchableOpacity onPress={() => setOpen(false)}>
              <Text style={styles.closeBtn}>✕</Text>
            </TouchableOpacity>
          </View>

          <TextInput
            style={styles.search}
            placeholder="Type to search stations..."
            placeholderTextColor="#555"
            value={search}
            onChangeText={setSearch}
            autoFocus
          />

          <FlatList
            data={filtered}
            keyExtractor={(item, index) => `${item}-${index}`}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.item}
                onPress={() => {
                  onChange(item)
                  setOpen(false)
                  setSearch('')
                }}
              >
                <Text style={styles.itemText}>{item}</Text>
              </TouchableOpacity>
            )}
          />
        </View>
      </Modal>
    </>
  )
}

const styles = StyleSheet.create({
  trigger: {
    backgroundColor: '#1a1a1a',
    padding: 14,
    borderRadius: 12,
    marginBottom: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  triggerTextSelected: { color: 'white', fontSize: 16 },
  triggerPlaceholder: { color: '#555', fontSize: 16 },
  arrow: { color: '#555', fontSize: 12 },
  modal: { flex: 1, backgroundColor: '#0a0a0a', padding: 24, paddingTop: 60 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  modalTitle: { color: 'white', fontSize: 22, fontWeight: 'bold' },
  closeBtn: { color: '#888', fontSize: 22 },
  search: { backgroundColor: '#1a1a1a', color: 'white', padding: 14, borderRadius: 12, fontSize: 16, marginBottom: 16 },
  item: { paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#1a1a1a' },
  itemText: { color: 'white', fontSize: 16 },
})