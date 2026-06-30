import React, { createContext, useState, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';

export const AuthContext = createContext<any>(null);

export const AuthProvider = ({ children }: any) => {
  const [userToken, setUserToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on app startup
    const bootstrapAsync = async () => {
      const token = await SecureStore.getItemAsync('userToken');
      setUserToken(token);
      setIsLoading(false);
    };
    bootstrapAsync();
  }, []);

  return (
    <AuthContext.Provider value={{ userToken, setUserToken, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};