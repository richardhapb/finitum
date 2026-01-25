import "../global.css";
import { useEffect } from "react";
import { Stack, useRouter, useSegments } from "expo-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { StatusBar } from "expo-status-bar";
import { useAuthStore } from "../lib/auth";
import { View, ActivityIndicator } from "react-native";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            retry: 1,
        },
    },
});

function AuthProvider({ children }: { children: React.ReactNode }) {
    const { isLoading, isAuthenticated, loadAuth } = useAuthStore();
    const segments = useSegments();
    const router = useRouter();

    useEffect(() => {
        loadAuth();
    }, []);

    useEffect(() => {
        if (isLoading) return;

        const inAuthGroup = segments[0] === "(auth)";

        if (!isAuthenticated && !inAuthGroup) {
            // Not signed in, redirect to login
            router.replace("/(auth)/login");
        } else if (isAuthenticated && inAuthGroup) {
            // Signed in but on auth screen, redirect to home
            router.replace("/(tabs)");
        }
    }, [isLoading, isAuthenticated, segments]);

    if (isLoading) {
        return (
            <View className="flex-1 items-center justify-center bg-gray-900">
                <ActivityIndicator size="large" color="#3b82f6" />
            </View>
        );
    }

    return <>{children}</>;
}

export default function RootLayout() {
    return (
        <GestureHandlerRootView style={{ flex: 1 }}>
            <SafeAreaProvider>
                <QueryClientProvider client={queryClient}>
                    <AuthProvider>
                        <StatusBar style="light" />
                        <Stack
                            screenOptions={{
                                headerShown: false,
                                contentStyle: { backgroundColor: "#111827" },
                            }}
                        >
                            <Stack.Screen name="(auth)" />
                            <Stack.Screen name="(tabs)" />
                            <Stack.Screen
                                name="add-expense"
                                options={{
                                    presentation: "modal",
                                    headerShown: true,
                                    headerTitle: "Add Expense",
                                    headerStyle: { backgroundColor: "#1f2937" },
                                    headerTintColor: "#fff",
                                }}
                            />
                        </Stack>
                    </AuthProvider>
                </QueryClientProvider>
            </SafeAreaProvider>
        </GestureHandlerRootView>
    );
}
