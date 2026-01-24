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
  ScrollView,
} from "react-native";
import { Link, useRouter } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { authApi } from "../../lib/api";
import { SafeAreaView } from "react-native-safe-area-context";

export default function SignupScreen() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const router = useRouter();

  const signupMutation = useMutation({
    mutationFn: () => authApi.signup(username, email, password),
    onSuccess: () => {
      Alert.alert("Success", "Account created! Please sign in.", [
        { text: "OK", onPress: () => router.replace("/(auth)/login") },
      ]);
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || "Signup failed. Please try again.";
      Alert.alert("Error", message);
    },
  });

  const handleSignup = () => {
    if (
      !username.trim() ||
      !email.trim() ||
      !password.trim() ||
      !confirmPassword.trim()
    ) {
      Alert.alert("Error", "Please fill in all fields");
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert("Error", "Passwords do not match");
      return;
    }

    if (password.length < 8) {
      Alert.alert("Error", "Password must be at least 8 characters");
      return;
    }

    signupMutation.mutate();
  };

  return (
    <SafeAreaView className="flex-1 bg-gray-900">
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        className="flex-1"
      >
        <ScrollView
          contentContainerStyle={{ flexGrow: 1 }}
          keyboardShouldPersistTaps="handled"
        >
          <View className="flex-1 justify-center px-6 py-8">
            <View className="mb-8">
              <Text className="text-4xl font-bold text-white mb-2">
                Create Account
              </Text>
              <Text className="text-gray-400 text-lg">
                Join Finitum to start tracking
              </Text>
            </View>

            <View className="space-y-4">
              <View>
                <Text className="text-gray-300 mb-2 text-sm">Username</Text>
                <TextInput
                  className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500"
                  placeholder="Choose a username"
                  placeholderTextColor="#6b7280"
                  value={username}
                  onChangeText={setUsername}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              <View className="mt-4">
                <Text className="text-gray-300 mb-2 text-sm">Email</Text>
                <TextInput
                  className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500"
                  placeholder="Enter your email"
                  placeholderTextColor="#6b7280"
                  value={email}
                  onChangeText={setEmail}
                  autoCapitalize="none"
                  autoCorrect={false}
                  keyboardType="email-address"
                />
              </View>

              <View className="mt-4">
                <Text className="text-gray-300 mb-2 text-sm">Password</Text>
                <TextInput
                  className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500"
                  placeholder="Create a password (min. 8 characters)"
                  placeholderTextColor="#6b7280"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                />
              </View>

              <View className="mt-4">
                <Text className="text-gray-300 mb-2 text-sm">
                  Confirm Password
                </Text>
                <TextInput
                  className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:border-blue-500"
                  placeholder="Confirm your password"
                  placeholderTextColor="#6b7280"
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  secureTextEntry
                />
              </View>

              <TouchableOpacity
                className={`mt-6 py-4 rounded-lg ${
                  signupMutation.isPending ? "bg-blue-400" : "bg-blue-600"
                }`}
                onPress={handleSignup}
                disabled={signupMutation.isPending}
              >
                {signupMutation.isPending ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text className="text-white text-center font-semibold text-lg">
                    Create Account
                  </Text>
                )}
              </TouchableOpacity>
            </View>

            <View className="mt-8 flex-row justify-center">
              <Text className="text-gray-400">Already have an account? </Text>
              <Link href="/(auth)/login" asChild>
                <TouchableOpacity>
                  <Text className="text-blue-500 font-semibold">Sign In</Text>
                </TouchableOpacity>
              </Link>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
