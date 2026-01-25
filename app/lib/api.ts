import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import Constants from "expo-constants";
import { getToken, useAuthStore } from "./auth";
import {
    CreateExpenseRequest,
    Expense,
    User,
    UserLoginResponse,
} from "./types";
import { Platform } from "react-native";

// Get the development machine's IP from Expo
const getBaseUrl = () => {
    if (__DEV__) {
        // For development - get the host from Expo's dev server
        const debuggerHost =
            Constants.expoConfig?.hostUri ??
            Constants.manifest2?.extra?.expoGo?.debuggerHost;
        const host = debuggerHost?.split(":")[0];

        if (Platform.OS === "android") {
            // Android emulator uses 10.0.2.2 to reach host machine
            return "http://10.0.2.2:9090";
        }

        if (Platform.OS === "web") {
            // Web can use localhost
            return "http://localhost:9090";
        }

        // iOS device/simulator - use the dev server's host IP
        if (host) {
            return `http://${host}:9090`;
        }

        // Fallback to localhost (works for simulator)
        return "http://localhost:9090";
    }
    // Production URL - update this when deploying
    return "https://api.finitum.app";
};

export const api = axios.create({
    baseURL: getBaseUrl(),
    headers: {
        "Content-Type": "application/json",
    },
    withCredentials: true,
});

// Request interceptor to add auth token
api.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
        const token = await getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error),
);

// Response interceptor for handling auth errors
api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        if (error.response?.status === 401) {
            // Clear auth on unauthorized
            await useAuthStore.getState().clearAuth();
        }
        return Promise.reject(error);
    },
);

// Auth API
export const authApi = {
    signup: async (
        username: string,
        email: string,
        password: string,
    ): Promise<User> => {
        const response = await api.post<User>("/signup", {
            username,
            email,
            password,
        });
        return response.data;
    },

    signin: async (
        usernameOrEmail: string,
        password: string,
    ): Promise<UserLoginResponse> => {
        // Check if input is email or username
        const isEmail = usernameOrEmail.includes("@");
        const payload = isEmail
            ? { email: usernameOrEmail, password }
            : { username: usernameOrEmail, password };

        const response = await api.post<UserLoginResponse>("/signin", payload);
        return response.data;
    },

    getMe: async (): Promise<User> => {
        const response = await api.get<User>("/me");
        return response.data;
    },

    getGoogleAuthUrl: (): string => {
        return `${getBaseUrl()}/google-authorize`;
    },
};

// Expenses API
export const expensesApi = {
    getAll: async (): Promise<Expense[]> => {
        const response = await api.get<Expense[]>("/expenses");
        return response.data;
    },

    create: async (expense: CreateExpenseRequest): Promise<Expense> => {
        const response = await api.post<Expense>("/expenses", expense);
        return response.data;
    },
};
