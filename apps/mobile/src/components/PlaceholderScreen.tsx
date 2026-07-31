import { SafeAreaView, StyleSheet, Text, View } from "react-native";

import { colors, spacing, typography } from "@/design-system/tokens";

export function PlaceholderScreen({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          {title}
        </Text>
        <Text style={styles.description}>{description}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  container: { flex: 1, padding: spacing.lg },
  title: { ...typography.title, color: colors.ink },
  description: {
    ...typography.body,
    color: colors.muted,
    lineHeight: 24,
    marginTop: spacing.sm,
  },
});

