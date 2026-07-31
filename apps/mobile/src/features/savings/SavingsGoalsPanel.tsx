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
    setFormError(null);
    setMode("goal");
  }

  function openEdit(goal: SavingsGoal) {
    setSelected(goal);
    setName(goal.name);
    setAmount(String(goal.target_amount_minor));
    setTargetDate(goal.target_date ?? "");
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
            onEdit={() => openEdit(item)}
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
        onAmount={setAmount}
        onArchive={confirmArchive}
        onClose={() => !saving && setMode(null)}
        onName={setName}
        onNote={setNote}
        onSave={mode === "contribution" ? addContribution : saveGoal}
        onTargetDate={setTargetDate}
      />
    </View>
  );
}

function GoalCard({
  goal,
  onContribute,
  onEdit,
}: {
  goal: SavingsGoal;
  onContribute(): void;
  onEdit(): void;
}) {
  const progress = Math.min(goal.progress_percent / 100, 1);
  return (
    <Pressable onPress={onEdit} style={styles.card}>
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
        </Text>
        <Pressable onPress={onContribute} style={styles.contributeButton}>
          <Text style={styles.contributeText}>Añadir aporte</Text>
        </Pressable>
      </View>
    </Pressable>
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
  onAmount,
  onArchive,
  onClose,
  onName,
  onNote,
  onSave,
  onTargetDate,
}: {
  amount: string;
  error: string | null;
  mode: "goal" | "contribution" | null;
  name: string;
  note: string;
  saving: boolean;
  selected: SavingsGoal | null;
  targetDate: string;
  onAmount(value: string): void;
  onArchive(): void;
  onClose(): void;
  onName(value: string): void;
  onNote(value: string): void;
  onSave(): void;
  onTargetDate(value: string): void;
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
