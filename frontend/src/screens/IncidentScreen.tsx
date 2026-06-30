import React, { useState } from "react";
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import * as Location from "expo-location"; // 📍 Import the location library
import apiClient from "../api/client";

export default function IncidentScreen({ navigation }: any) {
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitReport = async () => {
    if (!description.trim()) {
      Alert.alert("Missing Info", "Please describe the incident.");
      return;
    }

    setIsSubmitting(true);

    try {
      // 1. Request GPS Permissions from the user
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        Alert.alert(
          "Permission Denied",
          "We need location access to drop the pin on the safety map.",
        );
        setIsSubmitting(false);
        return;
      }

      // 2. Fetch the exact live coordinates
      let location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High, // Ensures pinpoint accuracy for emergencies
      });

      const realLat = location.coords.latitude;
      const realLon = location.coords.longitude;

      // 3. Send the real GPS data to your live Railway backend!
      await apiClient.post("/routes/incidents", {
        category: "general_safety", // You can make this a dropdown menu later!
        description: description,
        latitude: realLat,
        longitude: realLon,
      });

      Alert.alert(
        "Report Submitted",
        "Your incident has been pinned to the community map.",
      );
      navigation.goBack();
    } catch (error) {
      console.error(error);
      Alert.alert(
        "Submission Failed",
        "Could not upload report to the server.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Describe the incident..."
        value={description}
        onChangeText={setDescription}
        multiline
      />
      {/* Disable the button while the GPS is fetching to prevent double-clicks */}
      <TouchableOpacity
        style={[
          styles.submitButton,
          isSubmitting && styles.submitButtonDisabled,
        ]}
        onPress={submitReport}
        disabled={isSubmitting}
      >
        {isSubmitting ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Submit Incident Report</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 10,
    marginBottom: 20,
    textAlignVertical: "top",
  },
  submitButton: {
    backgroundColor: "#dc2626",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
    height: 50,
    justifyContent: "center",
  },
  submitButtonDisabled: { opacity: 0.7 },
  buttonText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
});
