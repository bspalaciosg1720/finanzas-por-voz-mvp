import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { colors, radius, spacing, typography } from "@/design-system/tokens";
import type {
  ReportPeriod,
  ReportSummary,
} from "@/features/reports/types";
import { formatMoney } from "@/features/transactions/format";
import { useAuth } from "@/features/auth/AuthContext";
import { ApiError } from "@/services/api";

const periods: Array<{ value: ReportPeriod; label: string }> = [
  { value: "daily", label: "Día" },
  { value: "weekly", label: "Semana" },
  { value: "monthly", label: "Mes" },
  { value: "annual", label: "Año" },
];

export default function ReportsScreen() {
  const { authenticatedRequest } = useAuth();
  const [period, setPeriod] = useState<ReportPeriod>("monthly");
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setReport(
        await authenticatedRequest<ReportSummary>(
          `/reports/summary?period=${period}`,
        ),
      );
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos cargar el reporte.",
      );
    } finally {
      setLoading(false);
    }
  }, [authenticatedRequest, period]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.eyebrow}>ANÁLISIS FINANCIERO</Text>
        <Text style={styles.title}>Reportes</Text>
        <View style={styles.selector}>
          {periods.map((option) => (
            <Pressable
              key={option.value}
              accessibilityRole="button"
              onPress={() => setPeriod(option.value)}
              style={[
                styles.period,
                period === option.value && styles.periodActive,
              ]}
            >
              <Text
                style={[
                  styles.periodText,
                  period === option.value && styles.periodTextActive,
                ]}
              >
                {option.label}
              </Text>
            </Pressable>
          ))}
        </View>

        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator color={colors.primary} />
            <Text style={styles.muted}>Calculando tu reporte…</Text>
          </View>
        ) : error || !report ? (
          <View style={styles.center}>
            <Text style={styles.muted}>{error}</Text>
            <Pressable onPress={() => void load()} style={styles.retry}>
              <Text style={styles.retryText}>Reintentar</Text>
            </Pressable>
          </View>
        ) : (
          <>
            <Text style={styles.range}>
              {report.start_date} — {report.end_date}
            </Text>
            <View style={styles.balanceCard}>
              <Text style={styles.balanceLabel}>Balance del periodo</Text>
              <Text style={styles.balance}>
                {formatMoney(report.balance_minor, report.currency)}
              </Text>
              <Text style={styles.balanceLabel}>
                {comparison(report.expense_change_percent)}
              </Text>
            </View>
            <View style={styles.row}>
              <Metric
                label="INGRESOS"
                value={formatMoney(report.income_minor, report.currency)}
              />
              <Metric
                expense
                label="GASTOS"
                value={formatMoney(report.expense_minor, report.currency)}
              />
            </View>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>GASTOS POR CATEGORÍA</Text>
              {report.categories.length ? (
                report.categories.map((category) => (
                  <View key={category.category_id ?? category.name} style={styles.category}>
                    <View style={styles.categoryHeader}>
                      <Text style={styles.categoryName}>{category.name}</Text>
                      <Text style={styles.categoryAmount}>
                        {formatMoney(category.amount_minor, report.currency)}
                      </Text>
                    </View>
                    <View style={styles.track}>
                      <View
                        style={[styles.fill, { width: `${category.percentage}%` }]}
                      />
                    </View>
                    <Text style={styles.percent}>{category.percentage} %</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.muted}>No hay gastos en este periodo.</Text>
              )}
            </View>
            <Text style={styles.footnote}>
              {report.transaction_count} movimientos incluidos
            </Text>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function comparison(change: number | null): string {
  if (change === null) return "Sin periodo anterior comparable";
  if (change === 0) return "Mismo gasto que el periodo anterior";
  return `${Math.abs(change).toLocaleString("es-CO")} % ${
    change > 0 ? "más" : "menos"
  } gasto que el periodo anterior`;
}

function Metric({
  label,
  value,
  expense = false,
}: {
  label: string;
  value: string;
  expense?: boolean;
}) {
  return (
    <View style={styles.metric}>
      <Text style={styles.cardTitle}>{label}</Text>
      <Text style={[styles.metricValue, expense && styles.expense]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { backgroundColor: colors.background, flex: 1 },
  container: { padding: spacing.lg, paddingBottom: 110 },
  eyebrow: { ...typography.label, color: colors.muted },
  title: { ...typography.title, color: colors.ink, marginTop: spacing.xs },
  selector: { flexDirection: "row", gap: spacing.xs, marginTop: spacing.lg },
  period: { borderRadius: radius.round, flex: 1, paddingVertical: 10 },
  periodActive: { backgroundColor: colors.primary },
  periodText: { ...typography.caption, color: colors.muted, textAlign: "center" },
  periodTextActive: { color: colors.surface, fontWeight: "700" },
  center: { alignItems: "center", gap: spacing.md, paddingVertical: 64 },
  muted: { ...typography.body, color: colors.muted, textAlign: "center" },
  range: { ...typography.caption, color: colors.muted, marginTop: spacing.lg },
  balanceCard: {
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    marginTop: spacing.sm,
    padding: spacing.lg,
  },
  balanceLabel: { ...typography.caption, color: colors.onPrimaryMuted },
  balance: { ...typography.amount, color: colors.surface, marginVertical: spacing.sm },
  row: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.sm },
  metric: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    flex: 1,
    padding: spacing.md,
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    marginTop: spacing.sm,
    padding: spacing.md,
  },
  cardTitle: { ...typography.label, color: colors.muted },
  metricValue: { ...typography.cardValue, color: colors.primary, marginTop: spacing.sm },
  expense: { color: colors.danger },
  category: { marginTop: spacing.md },
  categoryHeader: { flexDirection: "row", justifyContent: "space-between" },
  categoryName: { ...typography.body, color: colors.ink, fontWeight: "600" },
  categoryAmount: { ...typography.caption, color: colors.ink, fontWeight: "700" },
  track: {
    backgroundColor: colors.background,
    borderRadius: radius.round,
    height: 8,
    marginTop: spacing.sm,
    overflow: "hidden",
  },
  fill: { backgroundColor: colors.olive, borderRadius: radius.round, height: 8 },
  percent: { ...typography.caption, color: colors.muted, marginTop: spacing.xs },
  footnote: { ...typography.caption, color: colors.muted, marginTop: spacing.md },
  retry: { borderColor: colors.primary, borderRadius: radius.sm, borderWidth: 1, padding: 12 },
  retryText: { ...typography.button, color: colors.primary },
});
