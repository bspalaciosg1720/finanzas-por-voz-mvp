import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { colors, radius, spacing, typography } from "@/design-system/tokens";
import { useAuth } from "@/features/auth/AuthContext";
import type { SavingsGoal } from "@/features/savings/types";
import { formatMoney, parseCopAmount } from "@/features/transactions/format";
import { ApiError } from "@/services/api";

export function SavingsGoalsPanel() {
  const { authenticatedRequest, user } = useAuth();
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SavingsGoal | null>(null);
  const [mode, setMode] = useState<"goal" | "contribution" | null>(null);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [goalType, setGoalType] = useState<"general" | "sinking_fund">("general");
  const [plannedMonthly, setPlannedMonthly] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const load = useCallback(
    async (refresh = false) => {
      refresh ? setRefreshing(true) : setLoading(true);
      setError(null);
      try {
        setGoals(await authenticatedRequest<SavingsGoal[]>("/savings-goals"));
      } catch (reason) {
        setError(
          reason instanceof ApiError
            ? reason.message
            : "No pudimos cargar tus metas.",
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

  function openCreate() {
    setSelected(null);
    setName("");
    setAmount("");
    setTargetDate("");
    setGoalType("general");
    setPlannedMonthly("");
    setFormError(null);
    setMode("goal");
  }

  function openEdit(goal: SavingsGoal) {
    setSelected(goal);
    setName(goal.name);
    setAmount(String(goal.target_amount_minor));
    setTargetDate(goal.target_date ?? "");
    setGoalType(goal.goal_type);
    setPlannedMonthly(goal.planned_monthly_minor ? String(goal.planned_monthly_minor) : "");
    setFormError(null);
    setMode("goal");
  }

  function openContribution(goal: SavingsGoal) {
    setSelected(goal);
    setAmount("");
    setNote("");
    setFormError(null);
    setMode("contribution");
  }

  async function saveGoal() {
    const target = parseCopAmount(amount);
    const monthly = plannedMonthly ? parseCopAmount(plannedMonthly) : null;
    if (!target || name.trim().length < 2) {
      setFormError("Escribe un nombre y un monto objetivo válido.");
      return;
    }
    if (targetDate && !/^\d{4}-\d{2}-\d{2}$/.test(targetDate)) {
      setFormError("Usa el formato de fecha AAAA-MM-DD.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      if (selected) {
        await authenticatedRequest<void>(`/savings-goals/${selected.id}`, {
          method: "PATCH",
          body: JSON.stringify({
            name: name.trim(),
            target_amount_minor: target,
            target_date: targetDate || null,
            planned_monthly_minor: monthly,
          }),
        });
      } else {
        await authenticatedRequest<{ id: string }>("/savings-goals", {
          method: "POST",
          body: JSON.stringify({
            name: name.trim(),
            target_amount_minor: target,
            currency: user?.default_currency ?? "COP",
            target_date: targetDate || null,
            goal_type: goalType,
            planned_monthly_minor: monthly,
          }),
        });
      }
      setMode(null);
      await load(true);
    } catch (reason) {
      setFormError(
        reason instanceof ApiError ? reason.message : "No pudimos guardar la meta.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function addContribution() {
    const contribution = parseCopAmount(amount);
    if (!selected || !contribution) {
      setFormError("Ingresa un aporte mayor que cero.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await authenticatedRequest(
        `/savings-goals/${selected.id}/contributions`,
        {
          method: "POST",
          body: JSON.stringify({
            amount_minor: contribution,
            contributed_at: new Date().toISOString(),
            note: note.trim(),
          }),
        },
      );
      setMode(null);
      await load(true);
    } catch (reason) {
      setFormError(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos registrar el aporte.",
      );
    } finally {
      setSaving(false);
    }
  }

  function confirmArchive() {
    if (!selected) return;
    Alert.alert(
      "Archivar meta",
      "La meta y sus aportes dejarán de aparecer.",
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Archivar",
          style: "destructive",
          onPress: () => void archiveGoal(selected.id),
        },
      ],
    );
  }

  async function archiveGoal(id: string) {
    setSaving(true);
    try {
      await authenticatedRequest<void>(`/savings-goals/${id}`, {
        method: "DELETE",
      });
      setMode(null);
      await load(true);
    } catch (reason) {
      setFormError(
        reason instanceof ApiError ? reason.message : "No pudimos archivar la meta.",
      );
    } finally {
      setSaving(false);
    }
  }

  function confirmDeleteContribution(goal: SavingsGoal, contributionId: string) {
    Alert.alert(
      "Eliminar aporte",
      "La meta y el movimiento de caja se recalcularán.",
      [
        { text: "Cancelar", style: "cancel" },
        { text: "Eliminar", style: "destructive", onPress: () => void deleteContribution(goal.id, contributionId) },
      ],
    );
  }

  async function deleteContribution(goalId: string, contributionId: string) {
    try {
      await authenticatedRequest(`/savings-goals/${goalId}/contributions/${contributionId}`, { method: "DELETE" });
      await load(true);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "No pudimos eliminar el aporte.");
    }
  }

  async function enablePayFirst(goal: SavingsGoal) {
    try {
      await authenticatedRequest("/financial-strategies/config", { method: "PATCH", body: JSON.stringify({ pay_first_enabled: true, pay_first_goal_id: goal.id }) });
      Alert.alert("Págate primero activado", `Los próximos ingresos separarán el ahorro seguro hacia ${goal.name}.`);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "No pudimos activar la estrategia.");
    }
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} size="large" />
        <Text style={styles.muted}>Cargando metas…</Text>
      </View>
    );
  }
  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.title}>No pudimos cargar tus metas</Text>
        <Text style={styles.muted}>{error}</Text>
        <Action label="Reintentar" onPress={() => void load()} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.panelHeader}>
        <Text style={styles.helper}>Ahorra poco a poco para lo importante.</Text>
        <Pressable
          accessibilityLabel="Crear meta de ahorro"
          onPress={openCreate}
          style={styles.addButton}
        >
          <Text style={styles.addText}>＋</Text>
        </Pressable>
      </View>
      <FlatList
        contentContainerStyle={[
          styles.list,
          goals.length === 0 && styles.emptyList,
        ]}
        data={goals}
        keyExtractor={(goal) => goal.id}
        refreshControl={
          <RefreshControl
            onRefresh={() => void load(true)}
            refreshing={refreshing}
            tintColor={colors.primary}
          />
        }
        renderItem={({ item }) => (
          <GoalCard
            goal={item}
            onContribute={() => openContribution(item)}
            onDeleteContribution={(contributionId) => confirmDeleteContribution(item, contributionId)}
            onEdit={() => openEdit(item)}
            onPayFirst={() => void enablePayFirst(item)}
          />
        )}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.title}>Crea tu primera meta</Text>
            <Text style={styles.muted}>
              Viaje, computador, moto o cualquier objetivo personal.
            </Text>
            <Action label="Crear meta" onPress={openCreate} />
          </View>
        }
      />
      <GoalModal
        amount={amount}
        error={formError}
        mode={mode}
        name={name}
        note={note}
        saving={saving}
        selected={selected}
        targetDate={targetDate}
        goalType={goalType}
        plannedMonthly={plannedMonthly}
        onAmount={setAmount}
        onArchive={confirmArchive}
        onClose={() => !saving && setMode(null)}
        onName={setName}
        onNote={setNote}
        onSave={mode === "contribution" ? addContribution : saveGoal}
        onTargetDate={setTargetDate}
        onGoalType={setGoalType}
        onPlannedMonthly={setPlannedMonthly}
      />
    </View>
  );
}

function GoalCard({
  goal,
  onContribute,
  onDeleteContribution,
  onEdit,
  onPayFirst,
}: {
  goal: SavingsGoal;
  onContribute(): void;
  onDeleteContribution(contributionId: string): void;
  onEdit(): void;
  onPayFirst(): void;
}) {
  const progress = Math.min(goal.progress_percent / 100, 1);
  return (
    <View style={styles.card}>
      <Pressable onPress={onEdit}>
      <View style={styles.cardHeader}>
        <View style={styles.flex}>
          <Text style={styles.title}>{goal.name}</Text>
          <Text style={styles.meta}>
            {formatMoney(goal.saved_amount_minor, goal.currency)} de{" "}
            {formatMoney(goal.target_amount_minor, goal.currency)}
          </Text>
        </View>
        <Text style={styles.percent}>
          {goal.progress_percent.toLocaleString("es-CO")} %
        </Text>
      </View>
      <View style={styles.track}>
        <View style={[styles.progress, { flex: progress }]} />
        <View style={{ flex: 1 - progress }} />
      </View>
      <View style={styles.cardFooter}>
        <Text style={styles.meta}>
          {goal.status === "completed"
            ? "Meta completada"
            : goal.target_date
              ? `Objetivo: ${goal.target_date}`
              : "Sin fecha límite"}
          {goal.goal_type === "sinking_fund" && goal.planned_monthly_minor ? ` · ${formatMoney(goal.planned_monthly_minor, goal.currency)}/mes` : ""}
        </Text>
        <Pressable onPress={onContribute} style={styles.contributeButton}>
          <Text style={styles.contributeText}>Añadir aporte</Text>
        </Pressable>
      </View>
      <Pressable onPress={onPayFirst} style={styles.contributeButton}><Text style={styles.contributeText}>Usar para Págate primero</Text></Pressable>
      </Pressable>
      {goal.contributions.slice(0, 3).map((contribution) => (
        <View key={contribution.id} style={styles.contributionRow}>
          <Text style={styles.meta}>{formatMoney(contribution.amount_minor, goal.currency)} · {new Date(contribution.contributed_at).toLocaleDateString("es-CO")}</Text>
          <Pressable onPress={() => onDeleteContribution(contribution.id)}>
            <Text style={styles.deleteContribution}>Eliminar</Text>
          </Pressable>
        </View>
      ))}
    </View>
  );
}

function GoalModal({
  amount,
  error,
  mode,
  name,
  note,
  saving,
  selected,
  targetDate,
  goalType,
  plannedMonthly,
  onAmount,
  onArchive,
  onClose,
  onName,
  onNote,
  onSave,
  onTargetDate,
  onGoalType,
  onPlannedMonthly,
}: {
  amount: string;
  error: string | null;
  mode: "goal" | "contribution" | null;
  name: string;
  note: string;
  saving: boolean;
  selected: SavingsGoal | null;
  targetDate: string;
  goalType: "general" | "sinking_fund";
  plannedMonthly: string;
  onAmount(value: string): void;
  onArchive(): void;
  onClose(): void;
  onName(value: string): void;
  onNote(value: string): void;
  onSave(): void;
  onTargetDate(value: string): void;
  onGoalType(value: "general" | "sinking_fund"): void;
  onPlannedMonthly(value: string): void;
}) {
  const contribution = mode === "contribution";
  return (
    <Modal animationType="slide" onRequestClose={onClose} transparent visible={mode !== null}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {contribution
                ? `Aportar a ${selected?.name ?? ""}`
                : selected
                  ? "Editar meta"
                  : "Nueva meta"}
            </Text>
            <Pressable onPress={onClose}>
              <Text style={styles.close}>×</Text>
            </Pressable>
          </View>
          {!contribution ? (
            <>
              <Field label="NOMBRE" onChange={onName} value={name} />
              <Field label="FECHA OBJETIVO (OPCIONAL)" onChange={onTargetDate} value={targetDate} />
              <View style={styles.typeRow}><Pressable onPress={() => onGoalType("general")} style={[styles.typeChoice, goalType === "general" && styles.typeChoiceActive]}><Text style={styles.meta}>Meta</Text></Pressable><Pressable onPress={() => onGoalType("sinking_fund")} style={[styles.typeChoice, goalType === "sinking_fund" && styles.typeChoiceActive]}><Text style={styles.meta}>Gasto futuro</Text></Pressable></View>
              {goalType === "sinking_fund" ? <Field inputMode="numeric" label="APORTE MENSUAL PLANEADO" onChange={onPlannedMonthly} value={plannedMonthly} /> : null}
            </>
          ) : null}
          <Field
            inputMode="numeric"
            label={contribution ? "MONTO DEL APORTE" : "MONTO OBJETIVO"}
            onChange={onAmount}
            value={amount}
          />
          {contribution ? (
            <Field label="NOTA (OPCIONAL)" onChange={onNote} value={note} />
          ) : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}
          {saving ? (
            <ActivityIndicator color={colors.primary} style={styles.action} />
          ) : (
            <Action
              label={contribution ? "Registrar aporte" : "Guardar meta"}
              onPress={onSave}
            />
          )}
          {selected && !contribution ? (
            <Pressable onPress={onArchive} style={styles.archive}>
              <Text style={styles.archiveText}>Archivar meta</Text>
            </Pressable>
          ) : null}
        </View>
      </View>
    </Modal>
  );
}

function Field({
  inputMode,
  label,
  onChange,
  value,
}: {
  inputMode?: "numeric";
  label: string;
  onChange(value: string): void;
  value: string;
}) {
  return (
    <>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        inputMode={inputMode}
        onChangeText={onChange}
        placeholderTextColor={colors.muted}
        style={styles.input}
        value={value}
      />
    </>
  );
}

function Action({ label, onPress }: { label: string; onPress(): void }) {
  return (
    <Pressable onPress={onPress} style={styles.action}>
      <Text style={styles.actionText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  panelHeader: {
    alignItems: "center",
    flexDirection: "row",
    paddingHorizontal: spacing.md,
  },
  helper: { ...typography.caption, color: colors.muted, flex: 1 },
  addButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.round,
    height: 42,
    justifyContent: "center",
    width: 42,
  },
  addText: { color: colors.surface, fontSize: 24 },
  list: { padding: spacing.md, paddingBottom: 100 },
  emptyList: { flexGrow: 1, justifyContent: "center" },
  center: { alignItems: "center", gap: spacing.md, padding: spacing.xl },
  muted: { ...typography.body, color: colors.muted, textAlign: "center" },
  title: { ...typography.cardValue, color: colors.ink },
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
  meta: { ...typography.caption, color: colors.muted, marginTop: spacing.xs },
  percent: { ...typography.cardValue, color: colors.primary },
  track: {
    backgroundColor: colors.background,
    borderRadius: radius.round,
    flexDirection: "row",
    height: 10,
    marginTop: spacing.md,
    overflow: "hidden",
  },
  progress: { backgroundColor: colors.primary, borderRadius: radius.round },
  cardFooter: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.sm,
  },
  contributeButton: { padding: spacing.sm },
  contributeText: { ...typography.caption, color: colors.primary, fontWeight: "700" },
  contributionRow: {
    alignItems: "center",
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
  },
  deleteContribution: { ...typography.caption, color: colors.danger, fontWeight: "700" },
  backdrop: {
    backgroundColor: "rgba(32, 38, 36, 0.4)",
    flex: 1,
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: colors.background,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    padding: spacing.lg,
  },
  modalHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  modalTitle: { ...typography.title, color: colors.ink, fontSize: 22 },
  close: { color: colors.muted, fontSize: 32 },
  fieldLabel: {
    ...typography.label,
    color: colors.muted,
    marginBottom: spacing.xs,
    marginTop: spacing.md,
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
  typeRow: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.md },
  typeChoice: { flex: 1, alignItems: "center", borderColor: colors.border, borderWidth: 1, borderRadius: radius.sm, padding: spacing.sm },
  typeChoiceActive: { backgroundColor: colors.primarySoft, borderColor: colors.primary },
  action: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.sm,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: 50,
    paddingHorizontal: spacing.lg,
  },
  actionText: { ...typography.button, color: colors.surface },
  error: { ...typography.caption, color: colors.danger, marginTop: spacing.md },
  archive: { alignItems: "center", padding: spacing.md },
  archiveText: { ...typography.button, color: colors.danger },
});
