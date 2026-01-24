import { useEffect } from "react";
import { View, Text, TouchableOpacity, Alert, Linking } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../lib/auth";
import { authApi } from "../../lib/api";

export default function SettingsScreen() {
  const { user, setUser, clearAuth } = useAuthStore();

  // Fetch fresh user data including google credentials status
  const { data: userData } = useQuery({
    queryKey: ["me"],
    queryFn: authApi.getMe,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Update stored user when fresh data arrives
  useEffect(() => {
    if (userData) {
      setUser(userData);
    }
  }, [userData]);

  const displayUser = userData || user;

  const handleLogout = () => {
    Alert.alert("Logout", "Are you sure you want to sign out?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Sign Out",
        style: "destructive",
        onPress: async () => {
          await clearAuth();
        },
      },
    ]);
  };

  const handleLinkGoogle = async () => {
    try {
      const url = authApi.getGoogleAuthUrl();
      const canOpen = await Linking.canOpenURL(url);
      if (canOpen) {
        await Linking.openURL(url);
      } else {
        Alert.alert("Error", "Cannot open browser for Google authentication");
      }
    } catch (error) {
      Alert.alert("Error", "Failed to start Google authentication");
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-gray-900" edges={["left", "right"]}>
      <View className="flex-1 px-4 pt-4">
        {/* User Info Card */}
        <View className="bg-gray-800 rounded-xl p-4 mb-6">
          <View className="flex-row items-center">
            <View className="w-16 h-16 bg-blue-600 rounded-full items-center justify-center">
              <Text className="text-white text-2xl font-bold">
                {displayUser?.username?.charAt(0).toUpperCase() || "U"}
              </Text>
            </View>
            <View className="ml-4 flex-1">
              <Text className="text-white text-xl font-semibold">
                {displayUser?.username || "User"}
              </Text>
              <Text className="text-gray-400">{displayUser?.email || "No email"}</Text>
            </View>
          </View>
        </View>

        {/* Settings Options */}
        <View className="bg-gray-800 rounded-xl overflow-hidden">
          {/* Link Google Account - only show if not linked */}
          {!displayUser?.has_google_credentials && (
            <TouchableOpacity
              className="flex-row items-center p-4 border-b border-gray-700"
              onPress={handleLinkGoogle}
            >
              <View className="w-10 h-10 bg-gray-700 rounded-lg items-center justify-center">
                <Ionicons name="logo-google" size={20} color="#4285F4" />
              </View>
              <View className="ml-3 flex-1">
                <Text className="text-white font-medium">Link Google Account</Text>
                <Text className="text-gray-400 text-sm">Connect for email expense tracking</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#6b7280" />
            </TouchableOpacity>
          )}

          {/* Google Connected indicator */}
          {displayUser?.has_google_credentials && (
            <View className="flex-row items-center p-4 border-b border-gray-700">
              <View className="w-10 h-10 bg-green-900/30 rounded-lg items-center justify-center">
                <Ionicons name="logo-google" size={20} color="#22c55e" />
              </View>
              <View className="ml-3 flex-1">
                <Text className="text-white font-medium">Google Connected</Text>
                <Text className="text-gray-400 text-sm">Email expense tracking enabled</Text>
              </View>
              <Ionicons name="checkmark-circle" size={20} color="#22c55e" />
            </View>
          )}

          {/* App Info */}
          <View className="flex-row items-center p-4 border-b border-gray-700">
            <View className="w-10 h-10 bg-gray-700 rounded-lg items-center justify-center">
              <Ionicons name="information-circle" size={20} color="#9ca3af" />
            </View>
            <View className="ml-3 flex-1">
              <Text className="text-white font-medium">App Version</Text>
              <Text className="text-gray-400 text-sm">1.0.0</Text>
            </View>
          </View>

          {/* Logout */}
          <TouchableOpacity className="flex-row items-center p-4" onPress={handleLogout}>
            <View className="w-10 h-10 bg-red-900/30 rounded-lg items-center justify-center">
              <Ionicons name="log-out" size={20} color="#ef4444" />
            </View>
            <View className="ml-3 flex-1">
              <Text className="text-red-500 font-medium">Sign Out</Text>
              <Text className="text-gray-400 text-sm">Log out of your account</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Footer */}
        <View className="flex-1 justify-end pb-8">
          <Text className="text-gray-600 text-center text-sm">
            Finitum - Personal Finance Tracker
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}
