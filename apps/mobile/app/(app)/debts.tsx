import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator, Alert, Modal, Pressable, RefreshControl, SafeAreaView,
  ScrollView, StyleSheet, Text, TextInput, View,
} from "react-native";
import { useRouter } from "expo-router";

import { colors, radius, spacing, typography } from "@/design-system/tokens";
import type { Debt, PayoffPlan } from "@/features/debts/types";
import { useAuth } from "@/features/auth/AuthContext";
import { createIdempotencyKey, formatMoney, parseCopAmount } from "@/features/transactions/format";
import { ApiError } from "@/services/api";

export default function DebtsScreen() {
  const router = useRouter();
  const { authenticatedRequest, user } = useAuth();
  const [debts, setDebts] = useState<Debt[]>([]);
  const [plan, setPlan] = useState<PayoffPlan | null>(null);
  const [strategy, setStrategy] = useState<"snowball" | "avalanche">("snowball");
  const [extra, setExtra] = useState("0");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"debt" | "payment" | null>(null);
  const [selected, setSelected] = useState<Debt | null>(null);
  const [name, setName] = useState("");
  const [balance, setBalance] = useState("");
  const [minimum, setMinimum] = useState("");
  const [rate, setRate] = useState("");
  const [day, setDay] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const load = useCallback(async (refresh = false) => {
    refresh ? setRefreshing(true) : setLoading(true);
    setError(null);
    try { setDebts(await authenticatedRequest<Debt[]>("/debts")); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "No pudimos cargar tus deudas."); }
    finally { setLoading(false); setRefreshing(false); }
  }, [authenticatedRequest]);
  useEffect(() => { void load(); }, [load]);

  function openDebt() { setSelected(null); setName(""); setBalance(""); setMinimum(""); setRate(""); setDay(""); setFormError(null); setMode("debt"); }
  function openPayment(debt: Debt) { setSelected(debt); setBalance(""); setFormError(null); setMode("payment"); }

  async function saveDebt() {
    const amount = parseCopAmount(balance); const minimumAmount = parseCopAmount(minimum);
    const ratePercent = rate.trim() ? Number(rate.replace(",", ".")) : null;
    const paymentDay = day.trim() ? Number(day) : null;
    if (!amount || !minimumAmount || name.trim().length < 2) { setFormError("Escribe nombre, saldo y pago mínimo válidos."); return; }
    if (ratePercent !== null && (!Number.isFinite(ratePercent) || ratePercent < 0 || ratePercent > 1000)) { setFormError("La tasa anual debe estar entre 0 y 1000 %."); return; }
    if (paymentDay !== null && (!Number.isInteger(paymentDay) || paymentDay < 1 || paymentDay > 31)) { setFormError("El día de pago debe estar entre 1 y 31."); return; }
    setSaving(true); setFormError(null);
    try {
      await authenticatedRequest("/debts", { method: "POST", body: JSON.stringify({
        name: name.trim(), debt_type: "other", initial_balance_minor: amount,
        minimum_payment_minor: minimumAmount, currency: user?.default_currency ?? "COP",
        annual_interest_rate_bps: ratePercent === null ? null : Math.round(ratePercent * 100), payment_day: paymentDay,
      }) });
      setMode(null); await load(true);
    } catch (reason) { setFormError(reason instanceof ApiError ? reason.message : "No pudimos guardar la deuda."); }
    finally { setSaving(false); }
  }

  async function savePayment() {
    const amount = parseCopAmount(balance);
    if (!selected || !amount) { setFormError("Ingresa un pago mayor que cero."); return; }
    setSaving(true); setFormError(null);
    try {
      await authenticatedRequest(`/debts/${selected.id}/payments`, { method: "POST", headers: { "Idempotency-Key": createIdempotencyKey() }, body: JSON.stringify({ amount_minor: amount, payment_type: "extra", paid_at: new Date().toISOString(), note: "" }) });
      setMode(null); setPlan(null); await load(true);
    } catch (reason) { setFormError(reason instanceof ApiError ? reason.message : "No pudimos registrar el pago."); }
    finally { setSaving(false); }
  }

  function confirmDeletePayment(debt: Debt, paymentId: string) {
    Alert.alert("Eliminar pago", "El saldo de la deuda aumentará nuevamente y el movimiento vinculado será anulado.", [
      { text: "Cancelar", style: "cancel" },
      { text: "Eliminar", style: "destructive", onPress: () => void deletePayment(debt.id, paymentId) },
    ]);
  }
  async function deletePayment(debtId: string, paymentId: string) {
    try { await authenticatedRequest(`/debts/${debtId}/payments/${paymentId}`, { method: "DELETE" }); setPlan(null); await load(true); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "No pudimos eliminar el pago."); }
  }

  async function calculatePlan(nextStrategy = strategy) {
    const extraAmount = parseCopAmount(extra) ?? 0; setError(null);
    try { setPlan(await authenticatedRequest<PayoffPlan>(`/debts/payoff-plan?strategy=${nextStrategy}&extra_payment_minor=${extraAmount}`)); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "No pudimos calcular el plan."); }
  }

  if (loading) return <SafeAreaView style={styles.safe}><View style={styles.center}><ActivityIndicator color={colors.primary} size="large" /></View></SafeAreaView>;
  return <SafeAreaView style={styles.safe}>
    <View style={styles.header}><Pressable onPress={() => router.back()}><Text style={styles.back}>‹ Salud</Text></Pressable><Pressable onPress={openDebt} style={styles.add}><Text style={styles.addText}>＋</Text></Pressable></View>
    <ScrollView contentContainerStyle={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void load(true)} tintColor={colors.primary} />}>
      <Text style={styles.eyebrow}>PLAN DETERMINÍSTICO</Text><Text style={styles.title}>Tus deudas</Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {debts.length ? debts.map((debt) => <View key={debt.id} style={styles.card}>
        <View style={styles.between}><Text style={styles.cardTitle}>{debt.name}</Text><Text style={debt.status === "paid" ? styles.paid : styles.amount}>{formatMoney(debt.current_balance_minor, debt.currency)}</Text></View>
        <Text style={styles.muted}>Pago mínimo {formatMoney(debt.minimum_payment_minor, debt.currency)}{debt.payment_day ? ` · vence el día ${debt.payment_day}` : ""}</Text>
        <View style={styles.track}><View style={[styles.fill, { width: `${Math.min(debt.progress_percent, 100)}%` as `${number}%` }]} /></View>
        <View style={styles.between}><Text style={styles.caption}>{debt.progress_percent} % pagado</Text>{debt.status === "active" ? <Pressable onPress={() => openPayment(debt)}><Text style={styles.link}>Registrar pago</Text></Pressable> : <Text style={styles.paid}>Pagada</Text>}</View>
        {debt.payments.slice(0, 3).map((payment) => <View key={payment.id} style={styles.paymentRow}><Text style={styles.caption}>{new Date(payment.paid_at).toLocaleDateString("es-CO")} · {formatMoney(payment.amount_minor, debt.currency)}</Text><Pressable onPress={() => confirmDeletePayment(debt, payment.id)}><Text style={styles.deleteLink}>Eliminar</Text></Pressable></View>)}
      </View>) : <View style={styles.empty}><Text style={styles.cardTitle}>Aún no registras deudas</Text><Text style={styles.muted}>Agrégalas para organizar pagos y comparar estrategias.</Text></View>}

      {debts.some((item) => item.status === "active") ? <View style={styles.planCard}>
        <Text style={styles.cardTitle}>Estrategia de pago</Text><View style={styles.switchRow}>{([ ["snowball", "Bola de nieve"], ["avalanche", "Avalancha"] ] as const).map(([value, label]) => <Pressable key={value} onPress={() => { setStrategy(value); void calculatePlan(value); }} style={[styles.option, strategy === value && styles.optionActive]}><Text style={[styles.optionText, strategy === value && styles.optionTextActive]}>{label}</Text></Pressable>)}</View>
        <Text style={styles.label}>ABONO ADICIONAL MENSUAL</Text><TextInput keyboardType="number-pad" value={extra} onChangeText={setExtra} style={styles.input} placeholder="0" />
        <Pressable onPress={() => void calculatePlan()} style={styles.primary}><Text style={styles.primaryText}>Calcular plan</Text></Pressable>
        {plan ? <View style={styles.planResult}><Text style={styles.muted}>Total mensual: {formatMoney(plan.total_monthly_payment_minor, plan.currency)}</Text><Text style={styles.muted}>{plan.estimated_months === null ? "No se puede estimar el plazo aún" : `Plazo estimado: ${plan.estimated_months} meses`}</Text>{plan.steps.map((step) => <Text key={step.debt_id} style={styles.step}>{step.order}. {step.name}</Text>)}{plan.limitations.map((item) => <Text key={item} style={styles.warning}>• {item}</Text>)}</View> : null}
      </View> : null}
    </ScrollView>
    <Modal transparent animationType="slide" visible={mode !== null} onRequestClose={() => setMode(null)}><View style={styles.overlay}><View style={styles.modal}>
      <Text style={styles.modalTitle}>{mode === "payment" ? `Pago a ${selected?.name}` : "Nueva deuda"}</Text>
      {mode === "debt" ? <><Field label="Nombre" value={name} onChange={setName} placeholder="Tarjeta principal" /><Field label="Saldo actual" value={balance} onChange={setBalance} numeric /><Field label="Pago mínimo mensual" value={minimum} onChange={setMinimum} numeric /><Field label="Tasa efectiva anual % (opcional)" value={rate} onChange={setRate} numeric /><Field label="Día de pago (opcional)" value={day} onChange={setDay} numeric /></> : <Field label="Valor del pago" value={balance} onChange={setBalance} numeric />}
      {formError ? <Text style={styles.error}>{formError}</Text> : null}<View style={styles.actions}><Pressable onPress={() => setMode(null)} style={styles.secondary}><Text style={styles.secondaryText}>Cancelar</Text></Pressable><Pressable disabled={saving} onPress={() => void (mode === "debt" ? saveDebt() : savePayment())} style={styles.primaryAction}><Text style={styles.primaryText}>{saving ? "Guardando…" : "Guardar"}</Text></Pressable></View>
    </View></View></Modal>
  </SafeAreaView>;
}

function Field({ label, value, onChange, placeholder, numeric = false }: { label: string; value: string; onChange: (text: string) => void; placeholder?: string; numeric?: boolean }) { return <View style={styles.field}><Text style={styles.label}>{label.toUpperCase()}</Text><TextInput style={styles.input} value={value} onChangeText={onChange} placeholder={placeholder} keyboardType={numeric ? "decimal-pad" : "default"} /></View>; }

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background }, center: { flex: 1, alignItems: "center", justifyContent: "center" }, header: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, flexDirection: "row", alignItems: "center", justifyContent: "space-between" }, back: { ...typography.body, color: colors.primary }, add: { backgroundColor: colors.primary, width: 42, height: 42, borderRadius: radius.round, alignItems: "center", justifyContent: "center" }, addText: { fontSize: 25, color: colors.surface }, container: { padding: spacing.lg, paddingBottom: 80 }, eyebrow: { ...typography.label, color: colors.muted }, title: { ...typography.title, color: colors.ink, marginTop: spacing.xs, marginBottom: spacing.lg }, card: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm }, between: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm }, cardTitle: { ...typography.cardValue, color: colors.ink }, amount: { ...typography.cardValue, color: colors.primary }, paid: { ...typography.caption, color: colors.olive, fontWeight: "700" }, muted: { ...typography.body, color: colors.muted, marginTop: spacing.sm }, caption: { ...typography.caption, color: colors.muted, marginTop: spacing.sm }, track: { height: 7, backgroundColor: colors.background, borderRadius: radius.round, marginTop: spacing.md, overflow: "hidden" }, fill: { height: 7, backgroundColor: colors.olive }, link: { ...typography.caption, color: colors.primary, fontWeight: "700", marginTop: spacing.sm }, empty: { backgroundColor: colors.surface, borderRadius: radius.md, padding: spacing.lg }, planCard: { backgroundColor: colors.primarySoft, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.lg }, switchRow: { flexDirection: "row", gap: spacing.sm, marginVertical: spacing.md }, option: { flex: 1, padding: spacing.sm, borderRadius: radius.sm, borderWidth: 1, borderColor: colors.primary, alignItems: "center" }, optionActive: { backgroundColor: colors.primary }, optionText: { ...typography.caption, color: colors.primary, fontWeight: "700" }, optionTextActive: { color: colors.surface }, label: { ...typography.label, color: colors.muted }, input: { borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface, borderRadius: radius.sm, minHeight: 46, paddingHorizontal: spacing.md, marginTop: spacing.xs, ...typography.body, color: colors.ink }, primary: { backgroundColor: colors.primary, borderRadius: radius.sm, minHeight: 46, alignItems: "center", justifyContent: "center", marginTop: spacing.md }, primaryText: { ...typography.button, color: colors.surface }, planResult: { marginTop: spacing.sm }, step: { ...typography.body, color: colors.ink, marginTop: spacing.sm }, warning: { ...typography.caption, color: colors.danger, marginTop: spacing.sm }, error: { ...typography.body, color: colors.danger, marginVertical: spacing.sm }, overlay: { flex: 1, justifyContent: "flex-end", backgroundColor: "rgba(0,0,0,0.35)" }, modal: { backgroundColor: colors.surface, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg, paddingBottom: spacing.xl }, modalTitle: { ...typography.title, color: colors.ink, fontSize: 23 }, field: { marginTop: spacing.md }, actions: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.lg }, secondary: { flex: 1, minHeight: 46, borderWidth: 1, borderColor: colors.border, borderRadius: radius.sm, alignItems: "center", justifyContent: "center" }, secondaryText: { ...typography.button, color: colors.muted }, primaryAction: { flex: 1, minHeight: 46, backgroundColor: colors.primary, borderRadius: radius.sm, alignItems: "center", justifyContent: "center" },
  paymentRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", borderTopWidth: 1, borderTopColor: colors.border, marginTop: spacing.sm }, deleteLink: { ...typography.caption, color: colors.danger, fontWeight: "700", marginTop: spacing.sm },
});
