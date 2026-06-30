import { useEffect, useState, useRef } from "react";
import * as Location from "expo-location";
import { Accelerometer } from "expo-sensors";
import apiClient from "../api/client";

export const useLocationTracker = () => {
  const [isMotionAnomaly, setIsMotionAnomaly] = useState(false);
  const anomalyTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // --------------------------------------------------------
    // 1. DYNAMIC MOTION ANOMALY (Accelerometer)
    // --------------------------------------------------------
    Accelerometer.setUpdateInterval(500); // Check the hardware every half-second

    const accelSubscription = Accelerometer.addListener(({ x, y, z }) => {
      // Calculate total G-Force (1.0 is resting gravity)
      const gForce = Math.sqrt(x * x + y * y + z * z);

      // If G-Force spikes over 2.8, the user is running, falling, or struggling
      if (gForce > 2.8) {
        console.log("🚨 MOTION ANOMALY DETECTED! G-Force:", gForce);
        setIsMotionAnomaly(true);

        // Keep the anomaly flag active for 10 seconds before resetting
        if (anomalyTimeout.current) clearTimeout(anomalyTimeout.current);
        anomalyTimeout.current = setTimeout(() => {
          setIsMotionAnomaly(false);
        }, 10000);
      }
    });

    // --------------------------------------------------------
    // 2. LIVE GPS TRACKING & SYNC
    // --------------------------------------------------------
    let locationSubscription: Location.LocationSubscription | null = null;

    const startTracking = async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") return;

      // Watch the user's location continuously
      locationSubscription = await Location.watchPositionAsync(
        {
          accuracy: Location.Accuracy.Balanced,
          timeInterval: 5000, // Fire every 5 seconds
          distanceInterval: 5, // Or every 5 meters moved
        },
        async (location) => {
          try {
            // 3. SEND DYNAMIC PAYLOAD TO BACKEND
            await apiClient.post("/sensors/sync", {
              // Real data!
              motion_anomaly: isMotionAnomaly,

              // Still placeholders for the hackathon MVP
              route_deviation: false,
              audio_scream: false,
            });
            console.log(
              "📡 Telemetry Synced. Anomaly status:",
              isMotionAnomaly,
            );
          } catch (err) {
            console.log("Telemetry sync failed", err);
          }
        },
      );
    };

    startTracking();

    // Cleanup listeners when the component unmounts
    return () => {
      accelSubscription.remove();
      if (locationSubscription) locationSubscription.remove();
      if (anomalyTimeout.current) clearTimeout(anomalyTimeout.current);
    };
  }, [isMotionAnomaly]);
};
