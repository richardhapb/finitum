import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import { create } from "zustand";
import { User } from "./types";

const ACCESS_TOKEN_KEY = "access_token";
const USER_KEY = "user_data";

// Storage abstraction - SecureStore for native, localStorage for web
const storage = {
    getItem: async (key: string): Promise<string | null> => {
        if (Platform.OS === "web") {
            return localStorage.getItem(key);
        }
        return SecureStore.getItemAsync(key);
    },
    setItem: async (key: string, value: string): Promise<void> => {
        if (Platform.OS === "web") {
            localStorage.setItem(key, value);
            return;
        }
        return SecureStore.setItemAsync(key, value);
    },
    removeItem: async (key: string): Promise<void> => {
        if (Platform.OS === "web") {
            localStorage.removeItem(key);
            return;
        }
        return SecureStore.deleteItemAsync(key);
    },
};

interface AuthState {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    setAuth: (user: User, token: string) => Promise<void>;
    setUser: (user: User) => Promise<void>;
    clearAuth: () => Promise<void>;
    loadAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,

    setAuth: async (user: User, token: string) => {
        await storage.setItem(ACCESS_TOKEN_KEY, token);
        await storage.setItem(USER_KEY, JSON.stringify(user));
        set({ user, token, isAuthenticated: true, isLoading: false });
    },

    setUser: async (user: User) => {
        await storage.setItem(USER_KEY, JSON.stringify(user));
        set({ user });
    },

    clearAuth: async () => {
        await storage.removeItem(ACCESS_TOKEN_KEY);
        await storage.removeItem(USER_KEY);
        set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
        });
    },

    loadAuth: async () => {
        try {
            const token = await storage.getItem(ACCESS_TOKEN_KEY);
            const userJson = await storage.getItem(USER_KEY);

            if (token) {
                const user = userJson ? JSON.parse(userJson) : null;
                set({ token, user, isAuthenticated: true, isLoading: false });
            } else {
                set({ isLoading: false });
            }
        } catch (error) {
            console.error("Error loading auth:", error);
            set({ isLoading: false });
        }
    },
}));

export const getToken = async (): Promise<string | null> => {
    return storage.getItem(ACCESS_TOKEN_KEY);
};
