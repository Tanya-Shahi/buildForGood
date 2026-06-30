import React, { useState, useContext } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import apiClient from '../../api/client';
import { AuthContext } from '../../context/AuthContext'; // Import the context

export default function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Access the global state setter
  const { setUserToken } = useContext(AuthContext); 

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Missing Info', 'Please enter your email and password.');
      return;
    }

    setIsLoading(true);
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', email.toLowerCase().trim());
      formData.append('password', password);

      const response = await apiClient.post('/auth/login', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;

      // 1. Persist to storage
      await SecureStore.setItemAsync('userToken', access_token);
      
      // 2. Update global context so the whole app knows the user is logged in
      setUserToken(access_token);
      
      // Note: navigation.replace is no longer strictly needed if you set up 
      // conditional rendering based on userToken in AppNavigator.tsx, 
      // but keeping it here for immediate redirection is fine for now.
      navigation.replace('Dashboard'); 
      
    } catch (error: any) {
      console.error(error);
      Alert.alert(
        'Login Failed', 
        error.response?.data?.detail || 'Invalid credentials or server error.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.formContainer}>
        <Text style={styles.title}>Welcome Back</Text>
        <Text style={styles.subtitle}>Sign in to access the safety network platform</Text>

        <TextInput
          style={styles.input}
          placeholder="Email address"
          placeholderTextColor="#9ca3af"
          keyboardType="email-address"
          autoCapitalize="none"
          value={email}
          onChangeText={setEmail}
        />

        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#9ca3af"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        <TouchableOpacity 
          style={styles.button} 
          onPress={handleLogin}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.buttonText}>Log In</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
  },
  formContainer: {
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#4b5563',
    marginBottom: 32,
  },
  input: {
    backgroundColor: '#ffffff',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#d1d5db',
    marginBottom: 16,
    fontSize: 16,
    color: '#000000',
  },
  button: {
    backgroundColor: '#2563eb',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});