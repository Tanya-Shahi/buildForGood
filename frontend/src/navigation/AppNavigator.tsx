import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import LoginScreen from '../screens/Auth/LoginScreen';
import DashboardScreen from '../screens/DashboardScreen'; // Import your new component here
import AssistantScreen from '../screens/AssistantScreen';
import IncidentScreen from '../screens/IncidentScreen';
const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  return (
    <Stack.Navigator initialRouteName="Login">
      <Stack.Screen 
        name="Login" 
        component={LoginScreen} 
        options={{ headerShown: false }} 
      />
      <Stack.Screen 
        name="Dashboard" 
        component={DashboardScreen} 
        options={{ headerShown: false }} 
      />
      <Stack.Screen name="Assistant" component={AssistantScreen} />
      <Stack.Screen name="Incident" component={IncidentScreen} options={{ title: 'Report Incident' }} />
    </Stack.Navigator>
  );
}