import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export const RiskMonitor = ({ score }: { score: number }) => (
  <View style={styles.card}>
    <Text style={styles.title}>AI Safety Risk</Text>
    <Text style={styles.score}>{(score * 100).toFixed(0)}%</Text>
  </View>
);

const styles = StyleSheet.create({
  card: { backgroundColor: '#fff', padding: 20, borderRadius: 16, alignItems: 'center' },
  title: { fontSize: 16, color: '#666' },
  score: { fontSize: 40, fontWeight: 'bold' }
});