import React, { useEffect, useState } from "react";
import { StyleSheet, View, Text } from "react-native";
import MapView, { Marker } from "react-native-maps";
import apiClient from "../api/client";

export const SafetyMap = () => {
  const [incidents, setIncidents] = useState<any[]>([]);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        // PROD FIX 2.2: Calling the real endpoint that returns actual database pins
        const response = await apiClient.get("/routes/incidents");
        setIncidents(response.data);
      } catch (error) {
        console.error("Map loading failed", error);
      }
    };
    fetchIncidents();
  }, []);

  return (
    <View style={styles.container}>
      <MapView
        style={styles.map}
        initialRegion={{
          latitude: 28.9845,
          longitude: 77.7064,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }}
      >
        {incidents.map((incident, index) => (
          <Marker
            key={index}
            coordinate={{
              latitude: incident.latitude,
              longitude: incident.longitude,
            }}
            title={incident.category || "Incident"}
            description={incident.description}
            pinColor={incident.verified_by_id ? "red" : "orange"} // Red if NGO verified, Orange if pending
          />
        ))}
      </MapView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, height: 300, borderRadius: 16, overflow: "hidden" },
  map: { width: "100%", height: "100%" },
});
