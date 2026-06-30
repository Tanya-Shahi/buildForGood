import React, { useState } from "react";
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  Alert,
  ScrollView,
} from "react-native";
import apiClient from "../api/client";

export default function AssistantScreen() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const submitLegalQuery = async () => {
    if (!query.trim()) return;

    setIsProcessing(true);
    try {
      // PROD FIX 2.3: Call the actual backend endpoint that handles AI Legal queries
      const res = await apiClient.post("/legal/intake", {
        text_fallback: query,
      });
      setResponse(
        res.data.advice || "Your query has been logged for NGO legal review.",
      );
      setQuery("");
    } catch (error) {
      Alert.alert("Error", "Could not reach legal AI services.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Legal Rights & Advice</Text>
      <Text style={styles.sub}>
        Ask a question regarding workplace harassment, domestic rights, or legal
        protections. Our AI will guide you.
      </Text>

      <TextInput
        style={styles.input}
        value={query}
        onChangeText={setQuery}
        placeholder="e.g., What are my rights if..."
        multiline
      />

      <TouchableOpacity
        style={[styles.button, isProcessing && { opacity: 0.6 }]}
        onPress={submitLegalQuery}
        disabled={isProcessing}
      >
        <Text style={styles.buttonText}>
          {isProcessing ? "Analyzing..." : "Submit Query"}
        </Text>
      </TouchableOpacity>

      {response ? (
        <ScrollView style={styles.responseBox}>
          <Text style={styles.responseLabel}>Guidance:</Text>
          <Text style={styles.responseText}>{response}</Text>
        </ScrollView>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "#f3f4f6" },
  header: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#111827",
    marginBottom: 10,
  },
  sub: { fontSize: 14, color: "#4b5563", marginBottom: 20 },
  input: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 8,
    padding: 15,
    height: 120,
    textAlignVertical: "top",
    marginBottom: 20,
  },
  button: {
    backgroundColor: "#4f46e5",
    padding: 16,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
  responseBox: {
    marginTop: 30,
    padding: 20,
    backgroundColor: "#e0e7ff",
    borderRadius: 8,
  },
  responseLabel: { fontWeight: "bold", color: "#3730a3", marginBottom: 10 },
  responseText: { color: "#312e81", lineHeight: 22 },
});
