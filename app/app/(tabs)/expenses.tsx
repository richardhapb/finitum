import { useState, useMemo } from "react";
import {
    View,
    Text,
    FlatList,
    TouchableOpacity,
    TextInput,
    RefreshControl,
    Modal,
    ScrollView,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { expensesApi } from "../../lib/api";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import {
    Expense,
    CATEGORY_LABELS,
    ExpenseCategory,
    ALL_CATEGORIES,
} from "../../lib/types";

export default function ExpensesScreen() {
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedCategory, setSelectedCategory] =
        useState<ExpenseCategory | null>(null);
    const [showCategoryFilter, setShowCategoryFilter] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    const {
        data: expenses = [],
        refetch,
        error,
    } = useQuery({
        queryKey: ["expenses"],
        queryFn: expensesApi.getAll,
    });

    const onRefresh = async () => {
        setRefreshing(true);
        await refetch();
        setRefreshing(false);
    };

    // Filter expenses
    const filteredExpenses = useMemo(() => {
        let filtered = expenses;

        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(
                (expense) =>
                    expense.commerce.toLowerCase().includes(query) ||
                    (expense.description &&
                        expense.description.toLowerCase().includes(query)),
            );
        }

        if (selectedCategory) {
            filtered = filtered.filter(
                (expense) => expense.category === selectedCategory,
            );
        }

        // Sort by date descending
        return [...filtered].sort(
            (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
        );
    }, [expenses, searchQuery, selectedCategory]);

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    const renderExpenseItem = ({ item }: { item: Expense }) => (
        <View className="bg-gray-800 mx-4 mb-3 rounded-xl p-4">
            <View className="flex-row justify-between items-start">
                <View className="flex-1 mr-4">
                    <Text className="text-white font-semibold text-base">
                        {item.commerce}
                    </Text>
                    <View className="flex-row items-center mt-1">
                        <View className="bg-gray-700 rounded-full px-2 py-1">
                            <Text className="text-gray-300 text-xs">
                                {CATEGORY_LABELS[item.category] ||
                                    item.category}
                            </Text>
                        </View>
                        <Text className="text-gray-500 text-xs ml-2">
                            {formatDate(item.date)}
                        </Text>
                    </View>
                    {item.description && (
                        <Text
                            className="text-gray-400 text-sm mt-2"
                            numberOfLines={2}
                        >
                            {item.description}
                        </Text>
                    )}
                </View>
                <Text className="text-red-400 font-bold text-lg">
                    -$
                    {item.amount.toLocaleString("en-US", {
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 2,
                    })}
                </Text>
            </View>
        </View>
    );

    if (error) {
        return (
            <SafeAreaView className="flex-1 bg-gray-900 items-center justify-center">
                <Text className="text-red-500 text-lg">
                    Error loading expenses
                </Text>
                <Text className="text-gray-400 mt-2">
                    {(error as Error).message}
                </Text>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView className="flex-1 bg-gray-900" edges={["left", "right"]}>
            {/* Search and Filter */}
            <View className="px-4 pt-4 pb-2">
                <View className="flex-row gap-2">
                    <View className="flex-1 flex-row items-center bg-gray-800 rounded-lg px-3">
                        <Ionicons name="search" size={20} color="#6b7280" />
                        <TextInput
                            className="flex-1 text-white py-3 px-2"
                            placeholder="Search expenses..."
                            placeholderTextColor="#6b7280"
                            value={searchQuery}
                            onChangeText={setSearchQuery}
                        />
                        {searchQuery.length > 0 && (
                            <TouchableOpacity
                                onPress={() => setSearchQuery("")}
                            >
                                <Ionicons
                                    name="close-circle"
                                    size={20}
                                    color="#6b7280"
                                />
                            </TouchableOpacity>
                        )}
                    </View>
                    <TouchableOpacity
                        className={`px-4 rounded-lg justify-center ${
                            selectedCategory ? "bg-blue-600" : "bg-gray-800"
                        }`}
                        onPress={() => setShowCategoryFilter(true)}
                    >
                        <Ionicons
                            name="filter"
                            size={20}
                            color={selectedCategory ? "#fff" : "#6b7280"}
                        />
                    </TouchableOpacity>
                </View>

                {selectedCategory && (
                    <View className="flex-row items-center mt-2">
                        <Text className="text-gray-400 text-sm">
                            Filtered by:{" "}
                        </Text>
                        <TouchableOpacity
                            className="flex-row items-center bg-blue-600 rounded-full px-3 py-1"
                            onPress={() => setSelectedCategory(null)}
                        >
                            <Text className="text-white text-sm mr-1">
                                {CATEGORY_LABELS[selectedCategory]}
                            </Text>
                            <Ionicons name="close" size={14} color="#fff" />
                        </TouchableOpacity>
                    </View>
                )}
            </View>

            {/* Expenses List */}
            <FlatList
                data={filteredExpenses}
                renderItem={renderExpenseItem}
                keyExtractor={(item) => item.id.toString()}
                contentContainerStyle={{ paddingTop: 8, paddingBottom: 100 }}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={onRefresh}
                        tintColor="#3b82f6"
                    />
                }
                ListEmptyComponent={
                    <View className="flex-1 items-center justify-center py-20">
                        <Ionicons
                            name="wallet-outline"
                            size={64}
                            color="#4b5563"
                        />
                        <Text className="text-gray-500 text-lg mt-4">
                            {searchQuery || selectedCategory
                                ? "No matching expenses"
                                : "No expenses yet"}
                        </Text>
                    </View>
                }
            />

            {/* Floating Add Button */}
            <TouchableOpacity
                className="absolute bottom-6 right-6 bg-blue-600 w-14 h-14 rounded-full items-center justify-center shadow-lg"
                onPress={() => router.push("/add-expense")}
                style={{
                    shadowColor: "#3b82f6",
                    shadowOffset: { width: 0, height: 4 },
                    shadowOpacity: 0.3,
                    shadowRadius: 8,
                    elevation: 8,
                }}
            >
                <Ionicons name="add" size={28} color="#fff" />
            </TouchableOpacity>

            {/* Category Filter Modal */}
            <Modal
                visible={showCategoryFilter}
                transparent
                animationType="slide"
                onRequestClose={() => setShowCategoryFilter(false)}
            >
                <TouchableOpacity
                    className="flex-1 bg-black/50"
                    activeOpacity={1}
                    onPress={() => setShowCategoryFilter(false)}
                >
                    <View className="flex-1 justify-end">
                        <TouchableOpacity activeOpacity={1}>
                            <View className="bg-gray-800 rounded-t-3xl max-h-[70%]">
                                <View className="flex-row justify-between items-center p-4 border-b border-gray-700">
                                    <Text className="text-white text-lg font-semibold">
                                        Filter by Category
                                    </Text>
                                    <TouchableOpacity
                                        onPress={() =>
                                            setShowCategoryFilter(false)
                                        }
                                    >
                                        <Ionicons
                                            name="close"
                                            size={24}
                                            color="#9ca3af"
                                        />
                                    </TouchableOpacity>
                                </View>
                                <ScrollView className="p-4">
                                    <TouchableOpacity
                                        className={`p-4 rounded-lg mb-2 ${
                                            selectedCategory === null
                                                ? "bg-blue-600"
                                                : "bg-gray-700"
                                        }`}
                                        onPress={() => {
                                            setSelectedCategory(null);
                                            setShowCategoryFilter(false);
                                        }}
                                    >
                                        <Text className="text-white font-medium">
                                            All Categories
                                        </Text>
                                    </TouchableOpacity>
                                    {ALL_CATEGORIES.map((category) => (
                                        <TouchableOpacity
                                            key={category}
                                            className={`p-4 rounded-lg mb-2 ${
                                                selectedCategory === category
                                                    ? "bg-blue-600"
                                                    : "bg-gray-700"
                                            }`}
                                            onPress={() => {
                                                setSelectedCategory(category);
                                                setShowCategoryFilter(false);
                                            }}
                                        >
                                            <Text className="text-white font-medium">
                                                {CATEGORY_LABELS[category]}
                                            </Text>
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
