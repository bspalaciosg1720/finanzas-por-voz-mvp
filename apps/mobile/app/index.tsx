import { Redirect } from "expo-router";
import { ActivityIndicator, View } from "react-native";

import { colors } from "@/design-system/tokens";
import { useAuth } from "@/features/auth/AuthContext";

export default function IndexRoute() {
  const { isLoading, user } = useAuth();
  if (isLoading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  return <Redirect href={user ? "/(app)" : "/(auth)/login"} />;
}

