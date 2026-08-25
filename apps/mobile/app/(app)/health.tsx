import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
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
import type { ExtraIncomeAnalysis, FinancialAlerts, FinancialHealthSummary, FinancialPatterns, HealthHistory, IncomeProfile } from "@/features/financial-health/types";
import type { StrategyAnalysis } from "@/features/financial-health/strategies";
import { useAuth } from "@/features/auth/AuthContext";
import { formatMoney } from "@/features/transactions/format";
import { ApiError } from "@/services/api";
import { useRouter } from "expo-router";

const configurableStrategies: Record<string, string> = {
  zero_based: "zero_based_enabled",
  variable_income_budget: "variable_income_budget_enabled",
  extraordinary_income: "extraordinary_income_enabled",
  hybrid_debt: "hybrid_debt_enabled",
  cash_buffer: "cash_buffer_enabled",
  no_spend_days: "no_spend_days_enabled",
  purchase_wait: "purchase_wait_enabled",
  financial_leaks: "leak_detector_enabled",
  opportunity_cost: "opportunity_cost_enabled",
};

export default function FinancialHealthScreen() {
  const { authenticatedRequest } = useAuth();
  const [summary, setSummary] = useState<FinancialHealthSummary | null>(null);
  const [history, setHistory] = useState<HealthHistory | null>(null);
  const [patterns, setPatterns] = useState<FinancialPatterns | null>(null);
  const [alerts, setAlerts] = useState<FinancialAlerts | null>(null);
  const [incomeProfile, setIncomeProfile] = useState<IncomeProfile | null>(null);
  const [extraIncome, setExtraIncome] = useState<ExtraIncomeAnalysis | null>(null);
  const [strategyAnalysis, setStrategyAnalysis] = useState<StrategyAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (refresh = false) => {
    refresh ? setRefreshing(true) : setLoading(true);
    setError(null);
    try {
      const [nextSummary, nextHistory, nextPatterns, nextAlerts, nextIncomeProfile, nextExtraIncome, nextStrategyAnalysis] = await Promise.all([
        authenticatedRequest<FinancialHealthSummary>("/financial-health/summary"),
        authenticatedRequest<HealthHistory>("/financial-health/history"),
        authenticatedRequest<FinancialPatterns>("/financial-health/patterns"),
        authenticatedRequest<FinancialAlerts>("/financial-alerts"),
        authenticatedRequest<IncomeProfile>("/financial-health/income-profile"),
        authenticatedRequest<ExtraIncomeAnalysis>("/financial-health/extra-income"),
        authenticatedRequest<StrategyAnalysis>("/financial-strategies/analysis"),
      ]);
      setSummary(nextSummary);
      setHistory(nextHistory);
      setPatterns(nextPatterns);
      setAlerts(nextAlerts);
      setIncomeProfile(nextIncomeProfile);
      setExtraIncome(nextExtraIncome);
      setStrategyAnalysis(nextStrategyAnalysis);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "No pudimos calcular tu salud financiera.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [authenticatedRequest]);

  useEffect(() => { void load(); }, [load]);

  if (loading) return <SafeAreaView style={styles.safe}><View style={styles.center}><ActivityIndicator color={colors.primary} size="large" /></View></SafeAreaView>;

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        contentContainerStyle={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void load(true)} tintColor={colors.primary} />}
      >
        <Text style={styles.eyebrow}>TU MES FINANCIERO</Text>
        <Text style={styles.title}>Salud financiera</Text>
        {error ? <View style={styles.warning}><Text style={styles.warningText}>{error}</Text></View> : null}
        {summary ? <HealthContent summary={summary} history={history} patterns={patterns} alerts={alerts} incomeProfile={incomeProfile} extraIncome={extraIncome} strategyAnalysis={strategyAnalysis} onToggleStrategy={async (key, enabled) => { const field = configurableStrategies[key]; if (!field) return; await authenticatedRequest("/financial-strategies/config", { method: "PATCH", body: JSON.stringify({ [field]: enabled }) }); await load(true); }} onDismiss={async (key) => { setAlerts((current) => current ? { ...current, items: current.items.filter((item) => item.key !== key) } : current); await authenticatedRequest("/financial-alerts/dismiss", { method: "POST", body: JSON.stringify({ key }) }); }} /> : <Text style={styles.muted}>Desliza hacia abajo para intentar nuevamente.</Text>}
      </ScrollView>
    </SafeAreaView>
  );
}

function HealthContent({ summary, history, patterns, alerts, incomeProfile, extraIncome, strategyAnalysis, onDismiss, onToggleStrategy }: { summary: FinancialHealthSummary; history: HealthHistory | null; patterns: FinancialPatterns | null; alerts: FinancialAlerts | null; incomeProfile: IncomeProfile | null; extraIncome: ExtraIncomeAnalysis | null; strategyAnalysis: StrategyAnalysis | null; onDismiss: (key: string) => Promise<void>; onToggleStrategy: (key: string, enabled: boolean) => Promise<void> }) {
  const router = useRouter();
  return <>
    <View style={styles.scoreCard}>
      <Text style={styles.score}>{summary.score ?? "—"}<Text style={styles.scoreMax}> / 100</Text></Text>
      <Text style={styles.scoreStatus}>{summary.status}</Text>
      <Text style={styles.confidence}>Confianza {summary.confidence}</Text>
    </View>

    {alerts?.items.length ? <><Text style={styles.sectionTitle}>Alertas importantes</Text>{alerts.items.map((item) => <View key={item.key} style={[styles.alertCard, item.tone === "positive" && styles.positiveCard]}><View style={styles.between}><Text style={styles.cardTitle}>{item.title}</Text><Pressable accessibilityLabel="Descartar alerta" onPress={() => void onDismiss(item.key)}><Text style={styles.alertClose}>×</Text></Pressable></View><Text style={styles.muted}>{item.detail}</Text></View>)}</> : null}

    <View style={styles.row}>
      <Metric label="DISPONIBLE" value={formatMoney(summary.available_cash_minor, summary.currency)} danger={summary.available_cash_minor < 0} />
      <Metric label="AHORRO" value={formatMoney(summary.savings_minor, summary.currency)} />
    </View>

    {incomeProfile?.conservative_income_minor !== null && incomeProfile?.conservative_income_minor !== undefined ? <View style={styles.card}><View style={styles.between}><Text style={styles.cardTitle}>Ingreso {incomeProfile.classification === "variable" ? "variable" : "estable"}</Text><Text style={styles.points}>Variación {incomeProfile.variability_percent} %</Text></View><Text style={styles.muted}>Base conservadora: {formatMoney(incomeProfile.conservative_income_minor, incomeProfile.currency)}</Text><Text style={styles.reference}>{incomeProfile.explanation} Periodo: {incomeProfile.monthly_incomes[0]?.period} a {incomeProfile.monthly_incomes.at(-1)?.period}.</Text></View> : null}

    {extraIncome?.detected ? <View style={styles.card}><Text style={styles.cardTitle}>Posible ingreso extraordinario</Text><Text style={styles.muted}>{formatMoney(extraIncome.extra_income_minor, extraIncome.currency)} · propuesta sin aplicar</Text>{extraIncome.allocations.map((item) => <View key={item.destination} style={styles.historyRow}><Text style={styles.muted}>{item.label}</Text><Text style={styles.points}>{formatMoney(item.amount_minor, extraIncome.currency)}</Text></View>)}<Text style={styles.reference}>{extraIncome.explanation}</Text></View> : null}

    {strategyAnalysis ? <><Text style={styles.sectionTitle}>Estrategias para tu etapa</Text><View style={styles.card}><Text style={styles.cardTitle}>Etapa: {strategyAnalysis.financial_level}</Text><Text style={styles.muted}>Recibido: {formatMoney(strategyAnalysis.received_income_minor, strategyAnalysis.currency)} · base para planificar: {formatMoney(strategyAnalysis.planning_income_minor, strategyAnalysis.currency)}</Text></View>{strategyAnalysis.strategies.filter((item) => item.recommended).slice(0, 4).map((item) => <View key={item.key} style={styles.card}><View style={styles.between}><Text style={styles.cardTitle}>{item.title}</Text><Text style={styles.points}>{item.enabled ? "Activa" : "Opcional"}</Text></View><Text style={styles.muted}>Por qué: {item.reason}</Text><Text style={styles.muted}>Beneficio: {item.benefit}</Text>{item.impact_minor !== null ? <Text style={styles.reference}>Impacto estimado: {formatMoney(item.impact_minor, strategyAnalysis.currency)}{item.impact_percent !== null ? ` · ${item.impact_percent} %` : ""}</Text> : null}{configurableStrategies[item.key] ? <Pressable onPress={() => void onToggleStrategy(item.key, !item.enabled)}><Text style={styles.debtLink}>{item.enabled ? "Desactivar" : "Activar estrategia"}</Text></Pressable> : null}</View>)}</> : null}

    <View style={styles.debtCard}>
      <View><Text style={styles.label}>DEUDA PENDIENTE</Text><Text style={styles.debtValue}>{formatMoney(summary.total_debt_minor, summary.currency)}</Text></View>
      <Text onPress={() => router.push("/(app)/debts")} style={styles.debtLink}>Administrar →</Text>
    </View>
    <View style={styles.debtCard}>
      <View><Text style={styles.label}>FONDO DE EMERGENCIA</Text><Text style={styles.debtValue}>{formatMoney(summary.emergency_fund_minor, summary.currency)} · {summary.emergency_fund_months ?? "—"} meses</Text></View>
      <Text onPress={() => router.push("/(app)/planning")} style={styles.debtLink}>Planificar →</Text>
    </View>

    <Text style={styles.sectionTitle}>Distribución del ingreso</Text>
    <View style={styles.card}>
      <Distribution label="Necesidades" value={summary.essential_percent} reference="Referencia: 50 %" />
      <Distribution label="Variables" value={summary.variable_percent} reference="Referencia: 30 %" />
      <Distribution label="Ahorro" value={summary.savings_percent} reference="Referencia: 20 %" />
    </View>

    <Text style={styles.sectionTitle}>¿Por qué obtuviste este resultado?</Text>
    {summary.components.map((component) => <View key={component.key} style={styles.card}>
      <View style={styles.between}><Text style={styles.cardTitle}>{component.label}</Text><Text style={styles.points}>{component.score} / {component.maximum}</Text></View>
      <Text style={styles.muted}>{component.explanation}</Text>
    </View>)}

    <Text style={styles.sectionTitle}>Tus próximos pasos</Text>
    {summary.recommendations.map((item, index) => <View key={`${item.priority}-${item.title}`} style={styles.card}>
      <Text style={styles.actionNumber}>{index + 1}</Text><Text style={styles.cardTitle}>{item.title}</Text>
      <Text style={styles.muted}>{item.detail}</Text>
    </View>)}

    {history?.items.length ? <><Text style={styles.sectionTitle}>Tu progreso</Text><View style={styles.card}><Text style={styles.cardTitle}>{history.trend === "improving" ? "Tendencia positiva" : history.trend === "declining" ? "Tendencia a revisar" : "Tendencia estable"}</Text>{history.items.map((item) => <View key={item.period} style={styles.historyRow}><Text style={styles.muted}>{item.period}</Text><Text style={styles.points}>{item.score} / 100{item.change === null ? "" : ` · ${item.change >= 0 ? "+" : ""}${item.change}`}</Text></View>)}</View></> : null}

    {patterns?.patterns.length ? <><Text style={styles.sectionTitle}>Patrones detectados</Text>{patterns.patterns.map((pattern) => <View key={pattern.key} style={styles.card}><Text style={styles.cardTitle}>{pattern.title}</Text><Text style={styles.muted}>{pattern.detail}</Text><Text style={styles.reference}>Periodo analizado: {pattern.start_period} a {pattern.end_period}</Text></View>)}</> : null}

    <View style={styles.note}><Text style={styles.noteTitle}>Ten en cuenta</Text>{summary.limitations.map((item) => <Text key={item} style={styles.noteText}>• {item}</Text>)}</View>
    <AssistantPanel />
  </>;
}

function AssistantPanel() {
  const { authenticatedRequest } = useAuth();
  const [question, setQuestion] = useState("¿Cómo voy este mes?");
  const [answer, setAnswer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function ask() {
    if (question.trim().length < 3) return;
    setBusy(true);
    try {
      const result = await authenticatedRequest<{ answer: string; source: string; disclaimer: string }>("/financial-assistant/explain", { method: "POST", body: JSON.stringify({ question: question.trim() }) });
      setAnswer(`${result.answer}\n\n${result.disclaimer}`);
    } catch { setAnswer("No pudimos generar la explicación en este momento."); }
    finally { setBusy(false); }
  }
  return <View style={styles.assistant}><Text style={styles.noteTitle}>Asistente explicativo</Text><Text style={styles.noteText}>Explica cálculos existentes; no calcula ni modifica tus finanzas.</Text><TextInput value={question} onChangeText={setQuestion} style={styles.assistantInput} /><Pressable disabled={busy} onPress={() => void ask()} style={styles.assistantButton}><Text style={styles.assistantButtonText}>{busy ? "Explicando…" : "Preguntar"}</Text></Pressable>{answer ? <Text style={styles.assistantAnswer}>{answer}</Text> : null}</View>;
}

function Metric({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return <View style={styles.metric}><Text style={styles.label}>{label}</Text><Text style={[styles.metricValue, danger && styles.danger]}>{value}</Text></View>;
}

function Distribution({ label, value, reference }: { label: string; value: number | null; reference: string }) {
  const width = `${Math.min(value ?? 0, 100)}%` as `${number}%`;
  return <View style={styles.distribution}><View style={styles.between}><Text style={styles.cardTitle}>{label}</Text><Text style={styles.points}>{value === null ? "—" : `${value} %`}</Text></View><View style={styles.track}><View style={[styles.fill, { width }]} /></View><Text style={styles.reference}>{reference}, no es una regla rígida.</Text></View>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background }, container: { padding: spacing.lg, paddingBottom: 110 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" }, eyebrow: { ...typography.label, color: colors.muted },
  title: { ...typography.title, color: colors.ink, marginTop: spacing.xs }, scoreCard: { backgroundColor: colors.primary, borderRadius: radius.lg, padding: spacing.lg, marginTop: spacing.xl },
  score: { ...typography.amount, color: colors.surface }, scoreMax: { fontSize: 18, color: colors.onPrimaryMuted }, scoreStatus: { ...typography.cardValue, color: colors.surface, marginTop: spacing.sm },
  confidence: { ...typography.caption, color: colors.onPrimaryMuted, marginTop: spacing.xs, textTransform: "capitalize" }, row: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.sm },
  metric: { flex: 1, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md, padding: spacing.md }, label: { ...typography.label, color: colors.muted },
  metricValue: { ...typography.cardValue, color: colors.primary, marginTop: spacing.sm }, danger: { color: colors.danger }, sectionTitle: { ...typography.cardValue, color: colors.ink, marginTop: spacing.xl, marginBottom: spacing.sm },
  card: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm }, cardTitle: { ...typography.body, color: colors.ink, fontWeight: "700" },
  between: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" }, points: { ...typography.caption, color: colors.primary, fontWeight: "700" }, muted: { ...typography.body, color: colors.muted, marginTop: spacing.sm, lineHeight: 22 },
  distribution: { marginBottom: spacing.md }, track: { height: 8, backgroundColor: colors.background, borderRadius: radius.round, overflow: "hidden", marginTop: spacing.sm }, fill: { height: 8, backgroundColor: colors.olive, borderRadius: radius.round },
  reference: { ...typography.caption, color: colors.muted, marginTop: spacing.xs }, actionNumber: { ...typography.label, color: colors.primary, marginBottom: spacing.xs }, note: { backgroundColor: colors.primarySoft, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.md },
  noteTitle: { ...typography.cardValue, color: colors.ink }, noteText: { ...typography.caption, color: colors.muted, marginTop: spacing.sm, lineHeight: 18 }, warning: { backgroundColor: colors.primarySoft, borderRadius: radius.sm, padding: spacing.md, marginTop: spacing.md }, warningText: { ...typography.body, color: colors.danger },
  debtCard: { backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.sm, flexDirection: "row", alignItems: "center", justifyContent: "space-between" }, debtValue: { ...typography.cardValue, color: colors.ink, marginTop: spacing.xs }, debtLink: { ...typography.button, color: colors.primary },
  assistant: { backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.lg }, assistantInput: { borderWidth: 1, borderColor: colors.border, borderRadius: radius.sm, minHeight: 46, paddingHorizontal: spacing.md, marginTop: spacing.md, ...typography.body, color: colors.ink }, assistantButton: { backgroundColor: colors.primary, borderRadius: radius.sm, minHeight: 46, alignItems: "center", justifyContent: "center", marginTop: spacing.sm }, assistantButtonText: { ...typography.button, color: colors.surface }, assistantAnswer: { ...typography.body, color: colors.ink, lineHeight: 22, marginTop: spacing.md },
  historyRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderTopWidth: 1, borderTopColor: colors.border, marginTop: spacing.sm, paddingTop: spacing.sm },
  alertCard: { backgroundColor: colors.primarySoft, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm }, positiveCard: { backgroundColor: "#EAF2E7" }, alertClose: { color: colors.muted, fontSize: 24, marginLeft: spacing.sm },
});
