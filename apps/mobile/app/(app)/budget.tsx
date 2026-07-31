import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  Pressable,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { colors, radius, spacing, typography } from "@/design-system/tokens";
import { useAuth } from "@/features/auth/AuthContext";
import type {
  Budget,
  BudgetAlert,
  BudgetStatus,
} from "@/features/budgets/types";
import { formatMoney, parseCopAmount } from "@/features/transactions/format";
import type { Category } from "@/features/transactions/types";
import { ApiError } from "@/services/api";
import { SavingsGoalsPanel } from "@/features/savings/SavingsGoalsPanel";

export default function BudgetScreen() {
  const { authenticatedRequest, user } = useAuth();
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Budget | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const [amount, setAmount] = useState("");
  const [threshold, setThreshold] = useState("80");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [section, setSection] = useState<"budgets" | "goals">("budgets");

  const load = useCallback(
    async (refresh = false) => {
      refresh ? setRefreshing(true) : setLoading(true);
      setError(null);
      try {
        const [budgetRows, categoryRows, alertRows] = await Promise.all([
          authenticatedRequest<Budget[]>("/budgets"),
          authenticatedRequest<Category[]>("/categories"),
          authenticatedRequest<BudgetAlert[]>("/budgets/alerts"),
        ]);
        setBudgets(budgetRows);
        setCategories(categoryRows);
        setAlerts(alertRows);
      } catch (reason) {
        setError(
          reason instanceof ApiError
            ? reason.message
            : "No pudimos cargar tus presupuestos.",
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

  const availableCategories = useMemo(
    () =>
      categories.filter(
        (category) =>
          (category.movement_scope === "expense" ||
            category.movement_scope === "both") &&
          (editing?.category_id === category.id ||
            !budgets.some((budget) => budget.category_id === category.id)),
      ),
    [budgets, categories, editing],
  );

  function openCreate() {
    setEditing(null);
    setCategoryId(null);
    setAmount("");
    setThreshold("80");
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(budget: Budget) {
    setEditing(budget);
    setCategoryId(budget.category_id);
    setAmount(String(budget.amount_minor));
    setThreshold(String(budget.alert_threshold_percent));
    setFormError(null);
    setFormOpen(true);
  }

  async function saveBudget() {
    const amountMinor = parseCopAmount(amount);
    const thresholdPercent = Number(threshold);
    if (!amountMinor) {
      setFormError("Ingresa un límite mensual mayor que cero.");
      return;
    }
    if (
      !Number.isInteger(thresholdPercent) ||
      thresholdPercent < 1 ||
      thresholdPercent > 100
    ) {
      setFormError("El umbral debe estar entre 1 y 100.");
      return;
    }
    if (!editing && !categoryId) {
      setFormError("Selecciona una categoría.");
      return;
    }

    setSaving(true);
    setFormError(null);
    try {
      if (editing) {
        await authenticatedRequest<void>(`/budgets/${editing.id}`, {
          method: "PATCH",
          body: JSON.stringify({
            amount_minor: amountMinor,
            alert_threshold_percent: thresholdPercent,
          }),
        });
      } else {
        await authenticatedRequest<{ id: string }>("/budgets", {
          method: "POST",
          body: JSON.stringify({
            category_id: categoryId,
            amount_minor: amountMinor,
            currency: user?.default_currency ?? "COP",
            alert_threshold_percent: thresholdPercent,
          }),
        });
      }
      setFormOpen(false);
      await load(true);
    } catch (reason) {
      setFormError(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos guardar el presupuesto.",
      );
    } finally {
      setSaving(false);
    }
  }

  function confirmDelete() {
    if (!editing) return;
    Alert.alert(
      "Eliminar presupuesto",
      `Se eliminará el límite de ${editing.category_name}. Tus movimientos no cambiarán.`,
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Eliminar",
          style: "destructive",
          onPress: () => void deleteBudget(editing.id),
        },
      ],
    );
  }

  async function deleteBudget(id: string) {
    setSaving(true);
    try {
      await authenticatedRequest<void>(`/budgets/${id}`, { method: "DELETE" });
      setFormOpen(false);
      await load(true);
    } catch (reason) {
      setFormError(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos eliminar el presupuesto.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function dismissAlert(alertId: string) {
    setAlerts((current) => current.filter((alert) => alert.id !== alertId));
    try {
      await authenticatedRequest<void>(`/budgets/alerts/${alertId}/read`, {
        method: "PATCH",
      });
    } catch {
      await load(true);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <View>
          <Text style={styles.eyebrow}>LÍMITES DEL MES</Text>
          <Text accessibilityRole="header" style={styles.title}>
            Presupuestos
          </Text>
        </View>
        {section === "budgets" ? <Pressable
          accessibilityLabel="Crear presupuesto"
          accessibilityRole="button"
          onPress={openCreate}
          style={styles.addButton}
        >
          <Text style={styles.addText}>＋</Text>
        </Pressable> : null}
      </View>

      <View style={styles.sectionSwitch}>
        {(
          [
            ["budgets", "Presupuestos"],
            ["goals", "Metas"],
          ] as const
        ).map(([value, label]) => (
          <Pressable
            key={value}
            onPress={() => setSection(value)}
            style={[
              styles.sectionOption,
              section === value && styles.sectionOptionActive,
            ]}
          >
            <Text
              style={[
                styles.sectionOptionText,
                section === value && styles.sectionOptionTextActive,
              ]}
            >
              {label}
            </Text>
          </Pressable>
        ))}
      </View>

      {section === "budgets" ? alerts.map((alert) => (
        <Pressable
          accessibilityHint="Marca la alerta como leída"
          key={alert.id}
          onPress={() => void dismissAlert(alert.id)}
          style={[
            styles.alertBanner,
            alert.level === "exceeded" && styles.alertBannerDanger,
          ]}
        >
          <View style={styles.flex}>
            <Text style={styles.alertTitle}>
              {alert.level === "exceeded"
                ? "Presupuesto excedido"
                : "Cerca del límite"}
            </Text>
            <Text style={styles.alertText}>
              Revisa tu presupuesto de {alert.category_name}.
            </Text>
          </View>
          <Text style={styles.alertClose}>×</Text>
        </Pressable>
      )) : null}

      {section === "goals" ? (
        <SavingsGoalsPanel />
      ) : loading ? (
        <Centered>
          <ActivityIndicator color={colors.primary} size="large" />
          <Text style={styles.muted}>Calculando tu progreso…</Text>
        </Centered>
      ) : error ? (
        <Centered>
          <Text style={styles.sectionTitle}>No pudimos cargar los presupuestos</Text>
          <Text style={styles.muted}>{error}</Text>
          <Pressable onPress={() => void load()} style={styles.secondaryButton}>
            <Text style={styles.secondaryText}>Reintentar</Text>
          </Pressable>
        </Centered>
      ) : (
        <FlatList
          contentContainerStyle={[
            styles.list,
            budgets.length === 0 && styles.emptyList,
          ]}
          data={budgets}
          keyExtractor={(budget) => budget.id}
          refreshControl={
            <RefreshControl
              onRefresh={() => void load(true)}
              refreshing={refreshing}
              tintColor={colors.primary}
            />
          }
          renderItem={({ item }) => (
            <BudgetCard budget={item} onPress={() => openEdit(item)} />
          )}
          ListEmptyComponent={
            <Centered>
              <View style={styles.emptyIcon}>
                <Text style={styles.emptyIconText}>◎</Text>
              </View>
              <Text style={styles.sectionTitle}>Define tu primer límite</Text>
              <Text style={styles.muted}>
                Elige una categoría y te avisaremos cuando llegues al umbral.
              </Text>
              <Pressable onPress={openCreate} style={styles.primaryButton}>
                <Text style={styles.primaryText}>Crear presupuesto</Text>
              </Pressable>
            </Centered>
          }
        />
      )}

      <BudgetForm
        amount={amount}
        categories={availableCategories}
        categoryId={categoryId}
        editing={editing}
        error={formError}
        saving={saving}
        threshold={threshold}
        visible={formOpen}
        onAmount={setAmount}
        onCategory={setCategoryId}
        onClose={() => !saving && setFormOpen(false)}
        onDelete={confirmDelete}
        onSave={() => void saveBudget()}
        onThreshold={setThreshold}
      />
    </SafeAreaView>
  );
}

function BudgetCard({
  budget,
  onPress,
}: {
  budget: Budget;
  onPress(): void;
}) {
  const progress = Math.min(budget.progress_percent / 100, 1);
  const tone = statusTone(budget.alert_status);
  return (
    <Pressable onPress={onPress} style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={styles.flex}>
          <Text style={styles.sectionTitle}>{budget.category_name}</Text>
          <Text style={styles.cardMeta}>
            {formatMoney(budget.spent_minor, budget.currency)} de{" "}
            {formatMoney(budget.amount_minor, budget.currency)}
          </Text>
        </View>
        <Text style={[styles.percent, { color: tone }]}>
          {budget.progress_percent.toLocaleString("es-CO")} %
        </Text>
      </View>
      <View style={styles.track}>
        <View style={[styles.progress, { backgroundColor: tone, flex: progress }]} />
        <View style={{ flex: 1 - progress }} />
      </View>
      <Text style={[styles.status, { color: tone }]}>
        {statusLabel(budget.alert_status, budget.alert_threshold_percent)}
      </Text>
    </Pressable>
  );
}

function BudgetForm({
  amount,
  categories,
  categoryId,
  editing,
  error,
  saving,
  threshold,
  visible,
  onAmount,
  onCategory,
  onClose,
  onDelete,
  onSave,
  onThreshold,
}: {
  amount: string;
  categories: Category[];
  categoryId: string | null;
  editing: Budget | null;
  error: string | null;
  saving: boolean;
  threshold: string;
  visible: boolean;
  onAmount(value: string): void;
  onCategory(value: string): void;
  onClose(): void;
  onDelete(): void;
  onSave(): void;
  onThreshold(value: string): void;
}) {
  return (
    <Modal animationType="slide" onRequestClose={onClose} transparent visible={visible}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>
              {editing ? "Editar presupuesto" : "Nuevo presupuesto"}
            </Text>
            <Pressable accessibilityLabel="Cerrar" onPress={onClose}>
              <Text style={styles.close}>×</Text>
            </Pressable>
          </View>
          <ScrollView keyboardShouldPersistTaps="handled">
            <Text style={styles.fieldLabel}>CATEGORÍA</Text>
            {editing ? (
              <Text style={styles.fixedCategory}>{editing.category_name}</Text>
            ) : (
              <View style={styles.categoryList}>
                {categories.map((category) => (
                  <Pressable
                    key={category.id}
                    onPress={() => onCategory(category.id)}
                    style={[
                      styles.category,
                      categoryId === category.id && styles.categoryActive,
                    ]}
                  >
                    <Text style={styles.categoryText}>{category.name}</Text>
                  </Pressable>
                ))}
              </View>
            )}
            <Text style={styles.fieldLabel}>LÍMITE MENSUAL</Text>
            <TextInput
              accessibilityLabel="Límite mensual"
              inputMode="numeric"
              onChangeText={onAmount}
              placeholder="800000"
              placeholderTextColor={colors.muted}
              style={styles.input}
              value={amount}
            />
            <Text style={styles.fieldLabel}>ALERTAR AL PORCENTAJE</Text>
            <TextInput
              accessibilityLabel="Porcentaje de alerta"
              inputMode="numeric"
              maxLength={3}
              onChangeText={onThreshold}
              style={styles.input}
              value={threshold}
            />
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Pressable
              disabled={saving}
              onPress={onSave}
              style={[styles.primaryButton, saving && styles.disabled]}
            >
              {saving ? (
                <ActivityIndicator color={colors.surface} />
              ) : (
                <Text style={styles.primaryText}>Guardar presupuesto</Text>
              )}
            </Pressable>
            {editing ? (
              <Pressable onPress={onDelete} style={styles.deleteButton}>
                <Text style={styles.deleteText}>Eliminar presupuesto</Text>
              </Pressable>
            ) : null}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return <View style={styles.center}>{children}</View>;
}

function statusTone(status: BudgetStatus): string {
  if (status === "exceeded") return colors.danger;
  if (status === "warning") return colors.olive;
  return colors.primary;
}

function statusLabel(status: BudgetStatus, threshold: number): string {
  if (status === "exceeded") return "Presupuesto excedido";
  if (status === "warning") return `Superaste el umbral del ${threshold} %`;
  return "Vas dentro del presupuesto";
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    padding: spacing.lg,
  },
  eyebrow: { ...typography.label, color: colors.olive },
  title: { ...typography.title, color: colors.ink, marginTop: spacing.xs },
  addButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.round,
    height: 48,
    justifyContent: "center",
    width: 48,
  },
  addText: { color: colors.surface, fontSize: 27 },
  sectionSwitch: {
    backgroundColor: colors.border,
    borderRadius: radius.sm,
    flexDirection: "row",
    marginBottom: spacing.md,
    marginHorizontal: spacing.md,
    padding: 3,
  },
  sectionOption: {
    alignItems: "center",
    borderRadius: 8,
    flex: 1,
    padding: spacing.sm,
  },
  sectionOptionActive: { backgroundColor: colors.surface },
  sectionOptionText: { ...typography.button, color: colors.muted },
  sectionOptionTextActive: { color: colors.primary },
  alertBanner: {
    alignItems: "center",
    backgroundColor: "#F1EBDD",
    borderRadius: radius.sm,
    flexDirection: "row",
    marginBottom: spacing.sm,
    marginHorizontal: spacing.md,
    padding: spacing.md,
  },
  alertBannerDanger: { backgroundColor: "#F5EAEA" },
  alertTitle: { ...typography.cardValue, color: colors.ink, fontSize: 14 },
  alertText: { ...typography.caption, color: colors.muted, marginTop: spacing.xs },
  alertClose: { color: colors.muted, fontSize: 24, marginLeft: spacing.sm },
  list: { padding: spacing.md, paddingBottom: 100 },
  emptyList: { flexGrow: 1, justifyContent: "center" },
  center: {
    alignItems: "center",
    gap: spacing.md,
    justifyContent: "center",
    padding: spacing.xl,
  },
  muted: { ...typography.body, color: colors.muted, textAlign: "center" },
  sectionTitle: { ...typography.cardValue, color: colors.ink },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    marginBottom: spacing.sm,
    padding: spacing.md,
  },
  cardHeader: { alignItems: "center", flexDirection: "row" },
  flex: { flex: 1 },
  cardMeta: { ...typography.caption, color: colors.muted, marginTop: spacing.xs },
  percent: { ...typography.cardValue },
  track: {
    backgroundColor: colors.background,
    borderRadius: radius.round,
    flexDirection: "row",
    height: 10,
    marginTop: spacing.md,
    overflow: "hidden",
  },
  progress: { borderRadius: radius.round },
  status: { ...typography.caption, fontWeight: "700", marginTop: spacing.sm },
  emptyIcon: {
    alignItems: "center",
    backgroundColor: colors.primarySoft,
    borderRadius: radius.round,
    height: 64,
    justifyContent: "center",
    width: 64,
  },
  emptyIconText: { color: colors.primary, fontSize: 28 },
  primaryButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.sm,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: 50,
    paddingHorizontal: spacing.lg,
  },
  primaryText: { ...typography.button, color: colors.surface },
  secondaryButton: {
    borderColor: colors.primary,
    borderRadius: radius.sm,
    borderWidth: 1,
    paddingHorizontal: spacing.lg,
    paddingVertical: 12,
  },
  secondaryText: { ...typography.button, color: colors.primary },
  backdrop: {
    backgroundColor: "rgba(32, 38, 36, 0.4)",
    flex: 1,
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: colors.background,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    maxHeight: "90%",
    padding: spacing.lg,
  },
  sheetHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  sheetTitle: { ...typography.title, color: colors.ink, fontSize: 24 },
  close: { color: colors.muted, fontSize: 32 },
  fieldLabel: {
    ...typography.label,
    color: colors.muted,
    marginBottom: spacing.sm,
    marginTop: spacing.lg,
  },
  input: {
    ...typography.body,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    color: colors.ink,
    padding: spacing.md,
  },
  categoryList: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  category: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.round,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  categoryActive: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
  },
  categoryText: { ...typography.caption, color: colors.ink },
  fixedCategory: { ...typography.body, color: colors.ink },
  error: {
    ...typography.caption,
    color: colors.danger,
    marginTop: spacing.md,
    textAlign: "center",
  },
  disabled: { opacity: 0.55 },
  deleteButton: { alignItems: "center", padding: spacing.md },
  deleteText: { ...typography.button, color: colors.danger },
});
