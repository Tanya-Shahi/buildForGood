import React, { createContext, useState, ReactNode } from "react";

// Define the context shape for TypeScript
interface TelemetryContextType {
  riskScore: number;
  setRiskScore: (score: number) => void;
}

export const TelemetryContext = createContext<TelemetryContextType | null>(
  null,
);

export const TelemetryProvider = ({ children }: { children: ReactNode }) => {
  const [riskScore, setRiskScore] = useState<number>(0);

  return (
    <TelemetryContext.Provider value={{ riskScore, setRiskScore }}>
      {children}
    </TelemetryContext.Provider>
  );
};
