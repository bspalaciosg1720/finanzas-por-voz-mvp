import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

import { colors } from "@/design-system/tokens";
import { AuthProvider } from "@/features/auth/AuthContext";

export default function RootLayout() {
  return (
    <AuthProvider>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          contentStyle: { backgroundColor: colors.background },
          headerShown: false,
        }}
      />
    </AuthProvider>
  );
}
