import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  SafeAreaView,
  ScrollView,
} from "react-native";
import apiClient from "../api/client";
import { useLocationTracker } from "../hooks/useLocationTracker";
import { SafetyMap } from "../components/SafetyMap";

export default function DashboardScreen({ navigation }: any) {
  useLocationTracker();

  // PROD FIX 2.4: Accurate State Machine for SOS
  const [sosState, setSosState] = useState<"IDLE" | "COUNTDOWN" | "ACTIVE">(
    "IDLE",
  );
  const [countdown, setCountdown] = useState(10);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (sosState === "COUNTDOWN" && countdown > 0) {
      timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    } else if (sosState === "COUNTDOWN" && countdown === 0) {
      setSosState("ACTIVE"); // 10s passed, backend has definitively fired the webhooks/SMS
    }
    return () => clearTimeout(timer);
  }, [sosState, countdown]);

  const triggerSOS = async () => {
    try {
      // Tells the server to start the 10-second buffer
      await apiClient.post("/escalation/sos/start");
      setSosState("COUNTDOWN");
      setCountdown(10);
    } catch (error) {
      Alert.alert(
        "Network Error",
        "SOS logging failed locally. Cannot reach server.",
      );
    }
  };

  const cancelSOS = async () => {
    try {
      // Calls the actual backend endpoint you built to abort the escalation
      await apiClient.post("/escalation/sos/cancel");
      setSosState("IDLE");
      setCountdown(10);
    } catch (error) {
      Alert.alert("Error", "Failed to cancel SOS. Contact authorities.");
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={{ padding: 20 }}>
        <Text style={{ fontSize: 24, fontWeight: "bold", marginBottom: 20 }}>
          AWAAZ Guard
        </Text>

        <SafetyMap />

        {sosState === "IDLE" && (
          <TouchableOpacity style={styles.sosButton} onPress={triggerSOS}>
            <Text style={styles.sosText}>TRIGGER SOS</Text>
          </TouchableOpacity>
        )}

        {sosState === "COUNTDOWN" && (
          <View style={styles.countdownBox}>
            <Text style={styles.warningText}>Alerting in {countdown}s</Text>
            <TouchableOpacity style={styles.cancelButton} onPress={cancelSOS}>
              <Text style={styles.sosText}>ABORT</Text>
            </TouchableOpacity>
          </View>
        )}

        {sosState === "ACTIVE" && (
          <View style={[styles.countdownBox, { backgroundColor: "#991b1b" }]}>
            <Text style={styles.warningText}>🚨 SOS DISPATCHED 🚨</Text>
            <TouchableOpacity
              style={[styles.cancelButton, { marginTop: 15 }]}
              onPress={cancelSOS}
            >
              <Text style={styles.sosText}>STAND DOWN</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.navGrid}>
          <TouchableOpacity
            style={styles.navItem}
            onPress={() => navigation.navigate("Incident")}
          >
            <Text style={styles.navText}>Drop Pin</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.navItem}
            onPress={() => navigation.navigate("Assistant")}
          >
            <Text style={styles.navText}>Legal AI</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f3f4f6" },
  sosButton: {
    backgroundColor: "#dc2626",
    width: "100%",
    height: 60,
    borderRadius: 30,
    justifyContent: "center",
    alignItems: "center",
    marginTop: 30,
  },
  cancelButton: {
    backgroundColor: "#4b5563",
    width: "100%",
    height: 50,
    borderRadius: 25,
    justifyContent: "center",
    alignItems: "center",
    marginTop: 10,
  },
  sosText: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "800",
    letterSpacing: 1,
  },
  countdownBox: {
    backgroundColor: "#dc2626",
    padding: 20,
    borderRadius: 16,
    marginTop: 30,
  },
  warningText: {
    color: "#fff",
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
  },
  navGrid: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 30,
  },
  navItem: {
    backgroundColor: "#e5e7eb",
    flex: 0.48,
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
  },
  navText: { fontWeight: "600", color: "#374151" },
});
