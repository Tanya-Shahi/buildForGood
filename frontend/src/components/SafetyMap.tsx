import React, { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import MapView, { Polyline, Marker } from 'react-native-maps';
import apiClient from '../api/client';

export const SafetyMap = () => {
  const [routeCoordinates, setRouteCoordinates] = useState([]);

  useEffect(() => {
    // Fetch calculated route from your backend's routing engine
    const fetchRoute = async () => {
      try {
        const response = await apiClient.get('/routes/get-optimized-path');
        setRouteCoordinates(response.data.path);
      } catch (error) {
        console.error('Map loading failed', error);
      }
    };
    fetchRoute();
  }, []);

  return (
    <View style={styles.container}>
      <MapView 
        style={styles.map}
        initialRegion={{
          latitude: 28.9845, // Central
          longitude: 77.7064, // Meerut coordinates
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }}
      >
        <Polyline coordinates={routeCoordinates} strokeWidth={4} strokeColor="#2563eb" />
      </MapView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, height: 300, borderRadius: 16, overflow: 'hidden' },
  map: { width: '100%', height: '100%' },
});