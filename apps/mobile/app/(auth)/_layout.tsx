import { Redirect, Stack } from "expo-router";

import { useAuth } from "@/features/auth/AuthContext";

export default function AuthLayout() {
  const { isLoading, user } = useAuth();
  if (!isLoading && user) return <Redirect href="/(app)" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}
