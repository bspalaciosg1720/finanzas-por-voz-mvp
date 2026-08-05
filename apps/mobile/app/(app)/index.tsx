import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { colors, radius, spacing, typography } from "@/design-system/tokens";
import type { DashboardSummary } from "@/features/dashboard/types";
import { useAuth } from "@/features/auth/AuthContext";
import {
  formatMoney,
  formatMovementDate,
} from "@/features/transactions/format";
import type { TransactionSuggestion } from "@/features/transactions/types";
import { ApiError } from "@/services/api";
import { VoiceCaptureModal } from "@/features/voice/VoiceCaptureModal";

export default function HomeScreen() {
  const { authenticatedRequest, user } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<TransactionSuggestion[]>([]);
  const [suggestionBusy, setSuggestionBusy] = useState<string | null>(null);

  const load = useCallback(
    async (refresh = false) => {
      refresh ? setRefreshing(true) : setLoading(true);
      setError(null);
      try {
        const [nextSummary, nextSuggestions] = await Promise.all([
          authenticatedRequest<DashboardSummary>("/dashboard/summary"),
          authenticatedRequest<TransactionSuggestion[]>(
            "/transaction-suggestions",
          ),
        ]);
        setSummary(nextSummary);
        setSuggestions(nextSuggestions);
      } catch (reason) {
        setError(
          reason instanceof ApiError
            ? reason.message
            : "No pudimos conectar con el servidor.",
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest],
  );

  useEffect(() => {
    void load();
  }, [load]);

  async function resolveSuggestion(
    suggestion: TransactionSuggestion,
    action: "confirm" | "discard",
  ) {
    setSuggestionBusy(suggestion.id);
    setError(null);
    try {
      await authenticatedRequest(
        `/transaction-suggestions/${suggestion.id}/${action}`,
        {
          method: "POST",
          body: action === "confirm" ? JSON.stringify({}) : undefined,
        },
      );
      setSuggestions((current) =>
        current.filter((item) => item.id !== suggestion.id),
      );
      if (action === "confirm") {
        setSummary(
          await authenticatedRequest<DashboardSummary>("/dashboard/summary"),
        );
      }
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos procesar este movimiento.",
      );
    } finally {
      setSuggestionBusy(null);
    }
  }

  const today = useMemo(
    () =>
      new Intl.DateTimeFormat("es-CO", {
        weekday: "long",
        day: "numeric",
        month: "long",
      })
        .format(new Date())
        .toLocaleUpperCase("es"),
    [],
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} size="large" />
          <Text style={styles.muted}>Preparando tu resumen…</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!summary) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.center}>
          <Text style={styles.sectionTitle}>No pudimos cargar tu resumen</Text>
          <Text style={styles.muted}>{error}</Text>
          <Pressable onPress={() => void load()} style={styles.retryButton}>
            <Text style={styles.retryText}>Reintentar</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  const comparison = comparisonMessage(summary);
  const maxExpense = Math.max(
    summary.expense_minor,
    summary.previous_expense_minor,
    1,
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl
            onRefresh={() => void load(true)}
            refreshing={refreshing}
            tintColor={colors.primary}
          />
        }
      >
        <Text style={styles.eyebrow}>{today}</Text>
        <Text style={styles.title}>
          Hola, {user?.full_name.split(" ")[0] ?? "bienvenido"}
        </Text>

        {error ? (
          <View style={styles.warning}>
            <Text style={styles.warningText}>
              No fue posible actualizar. Mostramos el último resumen cargado.
            </Text>
          </View>
        ) : null}

        <View style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>Saldo actual</Text>
          <Text style={styles.balance}>
            {formatMoney(summary.balance_minor, summary.currency)}
          </Text>
          <Text style={styles.balanceMeta}>{comparison}</Text>
        </View>

        {suggestions.length ? (
          <View style={styles.suggestionSection}>
            <Text style={styles.sectionTitle}>Movimientos detectados</Text>
            <Text style={styles.mutedLeft}>
              Confirma los avisos que recibimos de tus entidades financieras.
            </Text>
            {suggestions.map((suggestion) => (
              <View key={suggestion.id} style={styles.suggestionCard}>
                <Text style={styles.suggestionQuestion}>
                  ¿Quieres registrar este{" "}
                  {suggestion.type === "income" ? "ingreso" : "gasto"}?
                </Text>
                <View style={styles.suggestionSummary}>
                  <View style={styles.flex}>
                    <Text style={styles.recentTitle}>
                      {suggestion.description || "Movimiento detectado"}
                    </Text>
                    <Text style={styles.mutedLeft}>
                      {suggestion.sender_domain} ·{" "}
                      {formatMovementDate(suggestion.occurred_at)}
                    </Text>
                  </View>
                  <Text
                    style={[
                      styles.suggestionAmount,
                      suggestion.type === "income" && styles.incomeText,
                    ]}
                  >
                    {formatMoney(
                      suggestion.amount_minor,
                      suggestion.currency,
                    )}
                  </Text>
                </View>
                <View style={styles.suggestionActions}>
                  <Pressable
                    disabled={suggestionBusy === suggestion.id}
                    onPress={() =>
                      void resolveSuggestion(suggestion, "discard")
                    }
                    style={styles.discardButton}
                  >
                    <Text style={styles.discardText}>Descartar</Text>
                  </Pressable>
                  <Pressable
                    disabled={suggestionBusy === suggestion.id}
                    onPress={() =>
                      void resolveSuggestion(suggestion, "confirm")
                    }
                    style={styles.confirmButton}
                  >
                    {suggestionBusy === suggestion.id ? (
                      <ActivityIndicator color={colors.surface} />
                    ) : (
                      <Text style={styles.confirmText}>Registrar</Text>
                    )}
                  </Pressable>
                </View>
              </View>
            ))}
          </View>
        ) : null}

        <View style={styles.summary}>
          <MetricCard
            label="INGRESOS DEL MES"
            value={formatMoney(summary.income_minor, summary.currency)}
            tone="income"
          />
          <MetricCard
            label="GASTOS DEL MES"
            value={formatMoney(summary.expense_minor, summary.currency)}
            tone="expense"
          />
        </View>

        <View style={styles.card}>
          <Text style={styles.cardLabel}>COMPARACIÓN DE GASTOS</Text>
          <ExpenseBar
            label="Mes actual"
            value={summary.expense_minor}
            maximum={maxExpense}
          />
          <ExpenseBar
            label="Mes anterior"
            value={summary.previous_expense_minor}
            maximum={maxExpense}
            previous
          />
        </View>

        <View style={styles.card}>
          <Text style={styles.cardLabel}>MAYOR CATEGORÍA DE GASTO</Text>
          {summary.top_expense_category ? (
            <View style={styles.topCategory}>
              <View style={styles.categoryIcon}>
                <Text style={styles.categoryIconText}>◎</Text>
              </View>
              <View style={styles.flex}>
                <Text style={styles.sectionTitle}>
                  {summary.top_expense_category.name}
                </Text>
                <Text style={styles.mutedLeft}>Durante el mes actual</Text>
              </View>
              <Text style={styles.topAmount}>
                {formatMoney(
                  summary.top_expense_category.amount_minor,
                  summary.currency,
                )}
              </Text>
            </View>
          ) : (
            <Text style={styles.mutedLeft}>Aún no hay gastos este mes.</Text>
          )}
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Movimientos recientes</Text>
        </View>
        <View style={styles.card}>
          {summary.recent_transactions.length ? (
            summary.recent_transactions.map((movement, index) => (
              <View
                key={movement.id}
                style={[
                  styles.recentRow,
                  index > 0 && styles.recentRowBorder,
                ]}
              >
                <View style={styles.flex}>
                  <Text numberOfLines={1} style={styles.recentTitle}>
                    {movement.description || "Sin descripción"}
                  </Text>
                  <Text style={styles.mutedLeft}>
                    {formatMovementDate(movement.occurred_at)}
                  </Text>
                </View>
                <Text
                  style={[
                    styles.recentAmount,
                    movement.type === "income" && styles.incomeText,
                  ]}
                >
                  {movement.type === "income" ? "+" : "−"}
                  {formatMoney(movement.amount_minor, movement.currency)}
                </Text>
              </View>
            ))
          ) : (
            <Text style={styles.mutedLeft}>
              Registra un movimiento para comenzar tu resumen.
            </Text>
          )}
        </View>

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Registrar movimiento por voz"
          onPress={() => setVoiceOpen(true)}
          style={({ pressed }) => [styles.voiceButton, pressed && styles.pressed]}
        >
          <Text style={styles.voiceIcon}>●</Text>
          <Text style={styles.voiceText}>Registrar por voz</Text>
        </Pressable>
      </ScrollView>
      <VoiceCaptureModal
        onClose={() => setVoiceOpen(false)}
        visible={voiceOpen}
      />
    </SafeAreaView>
  );
}

function comparisonMessage(summary: DashboardSummary): string {
  const change = summary.expense_change_percent;
  if (change === null) return "Sin gastos comparables en el mes anterior";
  if (change === 0) return "Mismo nivel de gastos que el mes anterior";
  const direction = change > 0 ? "más" : "menos";
  return `${Math.abs(change).toLocaleString("es-CO")} % ${direction} gasto que el mes anterior`;
}

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "income" | "expense";
}) {
  return (
    <View style={styles.summaryCard}>
      <Text style={styles.cardLabel}>{label}</Text>
      <Text style={[styles.cardValue, tone === "expense" && styles.expenseText]}>
        {value}
      </Text>
    </View>
  );
}

function ExpenseBar({
  label,
  value,
  maximum,
  previous = false,
}: {
  label: string;
  value: number;
  maximum: number;
  previous?: boolean;
}) {
  return (
    <View style={styles.barGroup}>
      <View style={styles.barHeader}>
        <Text style={styles.mutedLeft}>{label}</Text>
        <Text style={styles.barValue}>{value.toLocaleString("es-CO")}</Text>
      </View>
      <View style={styles.barTrack}>
        <View
          style={[
            styles.bar,
            previous && styles.previousBar,
            { flex: value / maximum },
          ]}
        />
        <View style={{ flex: 1 - value / maximum }} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  container: { padding: spacing.lg, paddingBottom: 110 },
  center: {
    alignItems: "center",
    flex: 1,
    gap: spacing.md,
    justifyContent: "center",
    padding: spacing.xl,
  },
  eyebrow: { ...typography.label, color: colors.muted },
  title: { ...typography.title, color: colors.ink, marginTop: spacing.xs },
  balanceCard: {
    backgroundColor: colors.primary,
    borderRadius: radius.lg,
    marginTop: spacing.xl,
    padding: spacing.lg,
  },
  balanceLabel: { ...typography.body, color: colors.onPrimaryMuted },
  balance: {
    ...typography.amount,
    color: colors.surface,
    marginVertical: spacing.sm,
  },
  balanceMeta: { ...typography.caption, color: colors.surface },
  suggestionSection: { marginTop: spacing.lg },
  suggestionCard: {
    backgroundColor: colors.surface,
    borderColor: colors.primary,
    borderRadius: radius.md,
    borderWidth: 1,
    marginTop: spacing.sm,
    padding: spacing.md,
  },
  suggestionQuestion: {
    ...typography.body,
    color: colors.ink,
    fontWeight: "700",
  },
  suggestionSummary: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  suggestionAmount: {
    ...typography.cardValue,
    color: colors.danger,
  },
  suggestionActions: {
    flexDirection: "row",
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  discardButton: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    flex: 1,
    justifyContent: "center",
    minHeight: 44,
  },
  discardText: { ...typography.button, color: colors.muted },
  confirmButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.sm,
    flex: 1,
    justifyContent: "center",
    minHeight: 44,
  },
  confirmText: { ...typography.button, color: colors.surface },
  summary: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.sm },
  summaryCard: {
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
  cardLabel: { ...typography.label, color: colors.muted },
  cardValue: {
    ...typography.cardValue,
    color: colors.primary,
    marginTop: spacing.sm,
  },
  expenseText: { color: colors.danger },
  incomeText: { color: colors.primary },
  barGroup: { marginTop: spacing.md },
  barHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.xs,
  },
  barTrack: {
    backgroundColor: colors.background,
    borderRadius: radius.round,
    flexDirection: "row",
    height: 9,
    overflow: "hidden",
  },
  bar: { backgroundColor: colors.primary, borderRadius: radius.round },
  previousBar: { backgroundColor: colors.olive },
  barValue: { ...typography.caption, color: colors.ink, fontWeight: "700" },
  topCategory: { alignItems: "center", flexDirection: "row", marginTop: spacing.md },
  categoryIcon: {
    alignItems: "center",
    backgroundColor: colors.primarySoft,
    borderRadius: radius.round,
    height: 42,
    justifyContent: "center",
    marginRight: spacing.md,
    width: 42,
  },
  categoryIconText: { color: colors.primary, fontSize: 20 },
  flex: { flex: 1 },
  sectionHeader: { marginTop: spacing.lg },
  sectionTitle: { ...typography.cardValue, color: colors.ink },
  muted: { ...typography.body, color: colors.muted, textAlign: "center" },
  mutedLeft: { ...typography.caption, color: colors.muted, marginTop: spacing.xs },
  topAmount: { ...typography.cardValue, color: colors.ink },
  recentRow: { alignItems: "center", flexDirection: "row", paddingVertical: spacing.sm },
  recentRowBorder: { borderColor: colors.border, borderTopWidth: 1 },
  recentTitle: { ...typography.body, color: colors.ink, fontWeight: "600" },
  recentAmount: { color: colors.danger, fontSize: 13, fontWeight: "700" },
  warning: {
    backgroundColor: "#F1EBDD",
    borderRadius: radius.sm,
    marginTop: spacing.md,
    padding: spacing.sm,
  },
  warningText: { ...typography.caption, color: colors.ink, textAlign: "center" },
  retryButton: {
    borderColor: colors.primary,
    borderRadius: radius.sm,
    borderWidth: 1,
    paddingHorizontal: spacing.lg,
    paddingVertical: 12,
  },
  retryText: { ...typography.button, color: colors.primary },
  voiceButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    flexDirection: "row",
    gap: spacing.sm,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: 52,
  },
  pressed: { opacity: 0.85 },
  voiceIcon: { color: colors.surface, fontSize: 14 },
  voiceText: { ...typography.button, color: colors.surface },
});
