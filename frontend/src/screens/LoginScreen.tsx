import React, { useState, useContext } from "react";
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  Alert,
  SafeAreaView,
  ActivityIndicator,
} from "react-native";
import * as SecureStore from "expo-secure-store";
import apiClient from "../api/client";
import { AuthContext } from "../context/AuthContext";

export default function LoginScreen({ navigation }: any) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { setUserToken } = useContext(AuthContext);

  const handleLogin = async () => {
    if (!username || !password)
      return Alert.alert("Error", "Please enter username and password.");

    setIsLoading(true);
    try {
      // PROD FIX 2.7: Strict application/x-www-form-urlencoded for FastAPI
      const formData = new URLSearchParams();
      formData.append("username", username.trim());
      formData.append("password", password);

      const response = await apiClient.post(
        "/auth/login",
        formData.toString(),
        {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        },
      );

      await SecureStore.setItemAsync("userToken", response.data.access_token);
      setUserToken(response.data.access_token); // Automatically redirects via AppNavigator
    } catch (error: any) {
      Alert.alert(
        "Login Failed",
        error.response?.data?.detail || "Invalid credentials or network error.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>AWAAZ</Text>
        <TextInput
          style={styles.input}
          placeholder="Username"
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        <TouchableOpacity
          style={styles.button}
          onPress={handleLogin}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Sign In</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => navigation.navigate("Register")}
          style={{ marginTop: 20 }}
        >
          <Text style={styles.link}>Don't have an account? Register here</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f3f4f6" },
  content: { flex: 1, justifyContent: "center", padding: 25 },
  title: {
    fontSize: 40,
    fontWeight: "900",
    textAlign: "center",
    marginBottom: 40,
    letterSpacing: 2,
  },
  input: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    padding: 16,
    borderRadius: 10,
    marginBottom: 16,
  },
  button: {
    backgroundColor: "#dc2626",
    padding: 18,
    borderRadius: 10,
    alignItems: "center",
  },
  buttonText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
  link: { color: "#2563eb", textAlign: "center", fontWeight: "600" },
});
