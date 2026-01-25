import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

type IoniconsName = React.ComponentProps<typeof Ionicons>["name"];

function TabBarIcon({
    name,
    color,
}: {
    name: IoniconsName;
    color: string;
    focused: boolean;
}) {
    return <Ionicons name={name} size={24} color={color} />;
}

export default function TabLayout() {
    return (
        <Tabs
            screenOptions={{
                tabBarActiveTintColor: "#3b82f6",
                tabBarInactiveTintColor: "#6b7280",
                tabBarStyle: {
                    backgroundColor: "#1f2937",
                    borderTopColor: "#374151",
                    paddingBottom: 20,
                    paddingTop: 10,
                    height: 80,
                },
                headerStyle: {
                    backgroundColor: "#1f2937",
                },
                headerTintColor: "#fff",
                headerTitleStyle: {
                    fontWeight: "600",
                },
            }}
        >
            <Tabs.Screen
                name="index"
                options={{
                    title: "Dashboard",
                    tabBarIcon: ({ color, focused }) => (
                        <TabBarIcon
                            name="home"
                            color={color}
                            focused={focused}
                        />
                    ),
                }}
            />
            <Tabs.Screen
                name="expenses"
                options={{
                    title: "Expenses",
                    tabBarIcon: ({ color, focused }) => (
                        <TabBarIcon
                            name="wallet"
                            color={color}
                            focused={focused}
                        />
                    ),
                }}
            />
            <Tabs.Screen
                name="settings"
                options={{
                    title: "Settings",
                    tabBarIcon: ({ color, focused }) => (
                        <TabBarIcon
                            name="settings"
                            color={color}
                            focused={focused}
                        />
                    ),
                }}
            />
        </Tabs>
    );
}
