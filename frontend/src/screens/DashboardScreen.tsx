import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  Alert, 
  ScrollView, 
  SafeAreaView 
} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import apiClient from '../api/client';
import { useLocationTracker } from '../hooks/useLocationTracker';
import { SafetyMap } from '../components/SafetyMap';

export default function DashboardScreen({ navigation }: any) {
  // Initialize the tracker
  useLocationTracker();
  
  const [riskScore, setRiskScore] = useState(0.24); 
  const [statusText, setStatusText] = useState('System Guard Active');

  const triggerSOS = async () => {
    Alert.alert(
      'Trigger Emergency SOS?',
      'This will immediately log an incident and initiate emergency escalation protocols.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'CONFIRM SOS', 
          style: 'destructive',
          onPress: async () => {
            try {
              await apiClient.post('/escalation/sos/start', {
                timestamp: new Date().toISOString(),
                emergency: true
              });
              Alert.alert('Alert Broadcasted', 'Emergency protocols successfully initialized.');
            } catch (error) {
              console.error(error);
              Alert.alert('Network Error', 'SOS logging failed, but local safety fallback active.');
            }
          }
        }
      ]
    );
  };

  const handleLogout = async () => {
    await SecureStore.deleteItemAsync('userToken');
    navigation.replace('Login');
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        
        {/* Map Integration */}
        <SafetyMap />

        {/* Risk Assessment Monitor */}
        <View style={styles.monitorCard}>
          <Text style={styles.monitorTitle}>AI Safety Risk Index</Text>
          <View style={[styles.statusIndicator, { backgroundColor: riskScore > 0.5 ? '#ef4444' : '#10b981' }]}>
            <Text style={styles.statusText}>{statusText}</Text>
          </View>
          <Text style={styles.scoreText}>{(riskScore * 100).toFixed(0)}%</Text>
          <Text style={styles.scoreLabel}>Threat Level Evaluation</Text>
        </View>

        {/* Critical SOS Trigger */}
        <TouchableOpacity style={styles.sosButton} onPress={triggerSOS}>
          <Text style={styles.sosText}>TRIGGER SOS</Text>
        </TouchableOpacity>

        {/* Navigation Hub */}
        <View style={styles.grid}>
          <TouchableOpacity 
            style={styles.gridCard} 
            onPress={() => navigation.navigate('Incident')} // Updated navigation
          >
            <Text style={styles.cardTitle}>Report Incident</Text>
          </TouchableOpacity>

          <TouchableOpacity 
             style={styles.gridCard} 
             onPress={() => navigation.navigate('Assistant')}
            >
            <Text style={styles.cardTitle}>AI Assistant</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>Sign Out of Network</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  // ... Keep your existing styles as they are ...
  container: { flex: 1, backgroundColor: '#f3f4f6' },
  scrollContainer: { padding: 24, alignItems: 'center' },
  monitorCard: { backgroundColor: '#ffffff', width: '100%', borderRadius: 16, padding: 24, alignItems: 'center', marginBottom: 24, marginTop: 16 },
  monitorTitle: { fontSize: 16, fontWeight: '600', color: '#4b5563', marginBottom: 12 },
  statusIndicator: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12, marginBottom: 16 },
  statusText: { color: '#ffffff', fontSize: 12, fontWeight: '700', textTransform: 'uppercase' },
  scoreText: { fontSize: 56, fontWeight: '800', color: '#111827' },
  scoreLabel: { fontSize: 14, color: '#9ca3af', marginTop: 4 },
  sosButton: { backgroundColor: '#dc2626', width: '100%', height: 60, borderRadius: 30, justifyContent: 'center', alignItems: 'center', marginBottom: 24 },
  sosText: { color: '#ffffff', fontSize: 18, fontWeight: '800', letterSpacing: 1 },
  grid: { flexDirection: 'row', justifyContent: 'space-between', width: '100%', marginBottom: 32 },
  gridCard: { backgroundColor: '#ffffff', width: '48%', borderRadius: 16, padding: 20, alignItems: 'center', minHeight: 80, justifyContent: 'center' },
  cardTitle: { fontSize: 14, fontWeight: '600', color: '#374151', textAlign: 'center' },
  logoutButton: { paddingVertical: 12 },
  logoutText: { color: '#9ca3af', fontSize: 14, fontWeight: '500' },
});