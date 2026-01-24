import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
} from "react-native";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { expensesApi } from "../lib/api";
import {
  CreateExpenseRequest,
  ExpenseCategory,
  CATEGORY_LABELS,
  Currency,
  ALL_CATEGORIES,
  CURRENCIES,
} from "../lib/types";

export default function AddExpenseScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [commerce, setCommerce] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState<ExpenseCategory>("general");
  const [currency, setCurrency] = useState<Currency>("clp");
  const [description, setDescription] = useState("");
  const [showCategoryPicker, setShowCategoryPicker] = useState(false);

  const createMutation = useMutation({
    mutationFn: (expense: CreateExpenseRequest) => expensesApi.create(expense),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      router.back();
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || "Failed to create expense. Please try again.";
      Alert.alert("Error", message);
    },
  });

  const handleSubmit = () => {
    if (!commerce.trim()) {
      Alert.alert("Error", "Please enter a merchant name");
      return;
    }

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      Alert.alert("Error", "Please enter a valid amount");
      return;
    }

    const expense: CreateExpenseRequest = {
      commerce: commerce.trim(),
      amount: parsedAmount,
      currency,
      category,
      description: description.trim() || undefined,
    };

    createMutation.mutate(expense);
  };

  return (
    <SafeAreaView className="flex-1 bg-gray-900" edges={["left", "right", "bottom"]}>
      <ScrollView className="flex-1 px-4 pt-4" keyboardShouldPersistTaps="handled">
        {/* Commerce/Merchant */}
        <View className="mb-4">
          <Text className="text-gray-300 mb-2 text-sm font-medium">Merchant</Text>
          <TextInput
            className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700"
            placeholder="Where did you spend?"
            placeholderTextColor="#6b7280"
            value={commerce}
            onChangeText={setCommerce}
          />
        </View>

        {/* Amount and Currency */}
        <View className="mb-4">
          <Text className="text-gray-300 mb-2 text-sm font-medium">Amount</Text>
          <View className="flex-row gap-2">
            <TextInput
              className="flex-1 bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 text-lg"
              placeholder="0.00"
              placeholderTextColor="#6b7280"
              value={amount}
              onChangeText={setAmount}
              keyboardType="decimal-pad"
            />
            <View className="flex-row bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
              {CURRENCIES.map((c) => (
                <TouchableOpacity
                  key={c}
                  className={`px-4 py-3 ${currency === c ? "bg-blue-600" : ""}`}
                  onPress={() => setCurrency(c)}
                >
                  <Text className={`font-medium ${currency === c ? "text-white" : "text-gray-400"}`}>
                    {c.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        {/* Category */}
        <View className="mb-4">
          <Text className="text-gray-300 mb-2 text-sm font-medium">Category</Text>
          <TouchableOpacity
            className="bg-gray-800 px-4 py-3 rounded-lg border border-gray-700 flex-row justify-between items-center"
            onPress={() => setShowCategoryPicker(true)}
          >
            <Text className="text-white">{CATEGORY_LABELS[category]}</Text>
            <Ionicons name="chevron-down" size={20} color="#9ca3af" />
          </TouchableOpacity>
        </View>

        {/* Description */}
        <View className="mb-6">
          <Text className="text-gray-300 mb-2 text-sm font-medium">Description (optional)</Text>
          <TextInput
            className="bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700"
            placeholder="Add a note..."
            placeholderTextColor="#6b7280"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={3}
            textAlignVertical="top"
            style={{ minHeight: 80 }}
          />
        </View>

        {/* Submit Button */}
        <TouchableOpacity
          className={`py-4 rounded-lg ${createMutation.isPending ? "bg-blue-400" : "bg-blue-600"}`}
          onPress={handleSubmit}
          disabled={createMutation.isPending}
        >
          {createMutation.isPending ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text className="text-white text-center font-semibold text-lg">Add Expense</Text>
          )}
        </TouchableOpacity>
      </ScrollView>

      {/* Category Picker Modal */}
      <Modal
        visible={showCategoryPicker}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCategoryPicker(false)}
      >
        <TouchableOpacity
          className="flex-1 bg-black/50"
          activeOpacity={1}
          onPress={() => setShowCategoryPicker(false)}
        >
          <View className="flex-1 justify-end">
            <TouchableOpacity activeOpacity={1}>
              <View className="bg-gray-800 rounded-t-3xl max-h-[70%]">
                <View className="flex-row justify-between items-center p-4 border-b border-gray-700">
                  <Text className="text-white text-lg font-semibold">Select Category</Text>
                  <TouchableOpacity onPress={() => setShowCategoryPicker(false)}>
                    <Ionicons name="close" size={24} color="#9ca3af" />
                  </TouchableOpacity>
                </View>
                <ScrollView className="p-4">
                  {ALL_CATEGORIES.map((cat) => (
                    <TouchableOpacity
                      key={cat}
                      className={`p-4 rounded-lg mb-2 ${
                        category === cat ? "bg-blue-600" : "bg-gray-700"
                      }`}
                      onPress={() => {
                        setCategory(cat);
                        setShowCategoryPicker(false);
                      }}
                    >
                      <Text className="text-white font-medium">{CATEGORY_LABELS[cat]}</Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </SafeAreaView>
  );
}
