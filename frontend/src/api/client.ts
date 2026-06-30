import axios from "axios";
import * as SecureStore from "expo-secure-store";

// 🚀 LIVE RAILWAY BACKEND
// Notice: HTTPS, no port number, exact /api/v1 path
const BASE_URL = "https://buildforgood-production.up.railway.app/api/v1";

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Log all requests and responses for debugging
apiClient.interceptors.request.use(async (config) => {
  try {
    const token = await SecureStore.getItemAsync("userToken");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`; // JWT injected here automatically!
    }
  } catch (error) {
    console.error("SecureStore token fetch failed", error);
  }
  console.log("📤 Request:", config.method?.toUpperCase(), config.url);
  return config;
});

export default apiClient;
