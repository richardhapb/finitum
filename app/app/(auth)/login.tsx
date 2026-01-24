import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from "react-native";
import { Link } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { authApi } from "../../lib/api";
import { useAuthStore } from "../../lib/auth";
import { SafeAreaView } from "react-native-safe-area-context";

export default function LoginScreen() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const { setAuth } = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: () => authApi.signin(identifier, password),
    onSuccess: async (data) => {
      await setAuth(data.user, data.access_token);
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || "Login failed. Please try again.";
      Alert.alert("Error", message);
    },
  });

  const handleLogin = () => {
    if (!identifier.trim() || !password.trim()) {
      Alert.alert("Error", "Please fill in all fields");
      return;
    }
    loginMutation.mutate();
  };

  return (
    <SafeAreaView className="flex-1 bg-gray-900">
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        className="flex-1"
      >
        <View className="flex-1 justify-center px-6">
          <View className="mb-10">
            <Text className="text-4xl font-bold text-white mb-2">Finitum</Text>
            <Text className="text-gray-400 text-lg">
              Track your expenses with ease
            </Text>
          </View>

          <View className="space-y-4">
            <View>
              <Text className="text-gray-300 mb-2 text-sm">
                Email or Username
              </Text>
              <TextInput
                className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500"
                placeholder="Enter email or username"
                placeholderTextColor="#6b7280"
                value={identifier}
                onChangeText={setIdentifier}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
              />
            </View>

            <View className="mt-4">
              <Text className="text-gray-300 mb-2 text-sm">Password</Text>
              <TextInput
                className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500"
                placeholder="Enter password"
                placeholderTextColor="#6b7280"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
            </View>

            <TouchableOpacity
              className={`mt-6 py-4 rounded-lg ${
                loginMutation.isPending ? "bg-blue-400" : "bg-blue-600"
              }`}
              onPress={handleLogin}
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text className="text-white text-center font-semibold text-lg">
                  Sign In
                </Text>
              )}
            </TouchableOpacity>
          </View>

          <View className="mt-8 flex-row justify-center">
            <Text className="text-gray-400">Don't have an account? </Text>
            <Link href="/(auth)/signup" asChild>
              <TouchableOpacity>
                <Text className="text-blue-500 font-semibold">Sign Up</Text>
              </TouchableOpacity>
            </Link>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
