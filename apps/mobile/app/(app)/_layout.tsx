import { Redirect, Tabs } from "expo-router";
import { Text } from "react-native";

import { colors } from "@/design-system/tokens";
import { useAuth } from "@/features/auth/AuthContext";

const icons: Record<string, string> = {
  index: "⌂",
  movements: "≡",
  health: "♥",
  budget: "◎",
  reports: "▥",
  profile: "○",
};

export default function AppLayout() {
  const { isLoading, user } = useAuth();
  if (!isLoading && !user) return <Redirect href="/(auth)/login" />;
  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: { minHeight: 68, paddingBottom: 8, paddingTop: 6 },
        tabBarIcon: ({ color }) => (
          <Text style={{ color, fontSize: 19 }}>{icons[route.name] ?? "·"}</Text>
        ),
      })}
    >
      <Tabs.Screen name="index" options={{ title: "Inicio" }} />
      <Tabs.Screen name="movements" options={{ title: "Movimientos" }} />
      <Tabs.Screen name="health" options={{ title: "Salud" }} />
      <Tabs.Screen name="debts" options={{ title: "Deudas", href: null }} />
      <Tabs.Screen name="planning" options={{ title: "Planificación", href: null }} />
      <Tabs.Screen name="budget" options={{ title: "Presupuesto" }} />
      <Tabs.Screen name="reports" options={{ title: "Reportes", href: null }} />
      <Tabs.Screen name="profile" options={{ title: "Perfil" }} />
    </Tabs>
  );
}
