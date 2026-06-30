import React, { useContext } from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { ActivityIndicator, View } from "react-native";
import { AuthContext } from "../context/AuthContext";

import LoginScreen from "../screens/LoginScreen";
import RegisterScreen from "../screens/RegisterScreen"; // Imported real register route
import DashboardScreen from "../screens/DashboardScreen";
import AssistantScreen from "../screens/AssistantScreen";
import IncidentScreen from "../screens/IncidentScreen";

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  const { userToken, isLoading } = useContext(AuthContext);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center" }}>
        <ActivityIndicator size="large" color="#dc2626" />
      </View>
    );
  }

  return (
    <Stack.Navigator>
      {userToken == null ? (
        // Unauthenticated Stack
        <Stack.Group screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
        </Stack.Group>
      ) : (
        // Authenticated Stack
        <Stack.Group>
          <Stack.Screen
            name="Dashboard"
            component={DashboardScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Assistant"
            component={AssistantScreen}
            options={{ title: "Legal & Rights Intake" }}
          />
          <Stack.Screen
            name="Incident"
            component={IncidentScreen}
            options={{ title: "Report Incident" }}
          />
        </Stack.Group>
      )}
    </Stack.Navigator>
  );
}
