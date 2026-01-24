import { View, Text, ScrollView, Dimensions, RefreshControl } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { expensesApi } from "../../lib/api";
import { SafeAreaView } from "react-native-safe-area-context";
import { PieChart, LineChart } from "react-native-chart-kit";
import { CATEGORY_LABELS, ExpenseCategory } from "../../lib/types";
import { useMemo, useState } from "react";

const screenWidth = Dimensions.get("window").width;

const CHART_COLORS = [
  "#3b82f6", // blue
  "#10b981", // emerald
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#84cc16", // lime
];

export default function DashboardScreen() {
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

  // Calculate totals by category
  const categoryTotals = useMemo(() => {
    const totals: Record<string, number> = {};
    expenses.forEach((expense) => {
      const category = expense.category || "GENERAL";
      totals[category] = (totals[category] || 0) + expense.amount;
    });
    return totals;
  }, [expenses]);

  // Pie chart data - top 5 categories
  const pieData = useMemo(() => {
    const sorted = Object.entries(categoryTotals)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);

    return sorted.map(([category, amount], index) => ({
      name: CATEGORY_LABELS[category as ExpenseCategory] || category,
      amount,
      color: CHART_COLORS[index % CHART_COLORS.length],
      legendFontColor: "#9ca3af",
      legendFontSize: 12,
    }));
  }, [categoryTotals]);

  // Monthly spending data for line chart
  const monthlyData = useMemo(() => {
    const monthlyTotals: Record<string, number> = {};
    const now = new Date();

    // Initialize last 6 months
    for (let i = 5; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
      monthlyTotals[key] = 0;
    }

    expenses.forEach((expense) => {
      const date = new Date(expense.date);
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
      if (monthlyTotals.hasOwnProperty(key)) {
        monthlyTotals[key] += expense.amount;
      }
    });

    const labels = Object.keys(monthlyTotals).map((key) => {
      const [, month] = key.split("-");
      const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      return monthNames[parseInt(month) - 1];
    });

    return {
      labels,
      datasets: [
        {
          data: Object.values(monthlyTotals),
          strokeWidth: 2,
        },
      ],
    };
  }, [expenses]);

  // Total spending
  const totalSpending = useMemo(() => {
    return expenses.reduce((sum, expense) => sum + expense.amount, 0);
  }, [expenses]);

  // This month's spending
  const thisMonthSpending = useMemo(() => {
    const now = new Date();
    return expenses
      .filter((expense) => {
        const date = new Date(expense.date);
        return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
      })
      .reduce((sum, expense) => sum + expense.amount, 0);
  }, [expenses]);

  if (error) {
    return (
      <SafeAreaView className="flex-1 bg-gray-900 items-center justify-center">
        <Text className="text-red-500 text-lg">Error loading expenses</Text>
        <Text className="text-gray-400 mt-2">{(error as Error).message}</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-gray-900" edges={["left", "right"]}>
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 20 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3b82f6" />
        }
      >
        {/* Summary Cards */}
        <View className="flex-row px-4 pt-4 gap-4">
          <View className="flex-1 bg-gray-800 rounded-xl p-4">
            <Text className="text-gray-400 text-sm">Total Spent</Text>
            <Text className="text-white text-2xl font-bold mt-1">
              ${totalSpending.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </Text>
          </View>
          <View className="flex-1 bg-gray-800 rounded-xl p-4">
            <Text className="text-gray-400 text-sm">This Month</Text>
            <Text className="text-blue-500 text-2xl font-bold mt-1">
              ${thisMonthSpending.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </Text>
          </View>
        </View>

        {/* Monthly Spending Chart */}
        <View className="mt-6 px-4">
          <Text className="text-white text-lg font-semibold mb-3">Monthly Spending</Text>
          <View className="bg-gray-800 rounded-xl p-4">
            {expenses.length > 0 ? (
              <LineChart
                data={monthlyData}
                width={screenWidth - 64}
                height={200}
                chartConfig={{
                  backgroundColor: "#1f2937",
                  backgroundGradientFrom: "#1f2937",
                  backgroundGradientTo: "#1f2937",
                  decimalPlaces: 0,
                  color: (opacity = 1) => `rgba(59, 130, 246, ${opacity})`,
                  labelColor: (opacity = 1) => `rgba(156, 163, 175, ${opacity})`,
                  style: {
                    borderRadius: 16,
                  },
                  propsForDots: {
                    r: "4",
                    strokeWidth: "2",
                    stroke: "#3b82f6",
                  },
                }}
                bezier
                style={{
                  borderRadius: 12,
                }}
              />
            ) : (
              <View className="h-[200px] items-center justify-center">
                <Text className="text-gray-500">No expense data yet</Text>
              </View>
            )}
          </View>
        </View>

        {/* Spending by Category */}
        <View className="mt-6 px-4">
          <Text className="text-white text-lg font-semibold mb-3">Spending by Category</Text>
          <View className="bg-gray-800 rounded-xl p-4">
            {pieData.length > 0 ? (
              <PieChart
                data={pieData}
                width={screenWidth - 64}
                height={200}
                chartConfig={{
                  color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
                }}
                accessor="amount"
                backgroundColor="transparent"
                paddingLeft="15"
                absolute
              />
            ) : (
              <View className="h-[200px] items-center justify-center">
                <Text className="text-gray-500">No expense data yet</Text>
              </View>
            )}
          </View>
        </View>

        {/* Recent Transactions */}
        <View className="mt-6 px-4">
          <Text className="text-white text-lg font-semibold mb-3">Recent Transactions</Text>
          <View className="bg-gray-800 rounded-xl">
            {expenses.length > 0 ? (
              expenses.slice(0, 5).map((expense, index) => (
                <View
                  key={expense.id}
                  className={`flex-row justify-between items-center p-4 ${
                    index < Math.min(expenses.length - 1, 4) ? "border-b border-gray-700" : ""
                  }`}
                >
                  <View className="flex-1">
                    <Text className="text-white font-medium">{expense.commerce}</Text>
                    <Text className="text-gray-400 text-sm">
                      {CATEGORY_LABELS[expense.category] || expense.category}
                    </Text>
                  </View>
                  <Text className="text-red-400 font-semibold">
                    -${expense.amount.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}
                  </Text>
                </View>
              ))
            ) : (
              <View className="p-8 items-center">
                <Text className="text-gray-500">No transactions yet</Text>
              </View>
            )}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
