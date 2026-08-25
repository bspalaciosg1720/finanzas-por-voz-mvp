import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Modal,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from "react-native";
import Constants from "expo-constants";
import * as Notifications from "expo-notifications";

import { colors, radius, spacing, typography } from "@/design-system/tokens";
import { useAuth } from "@/features/auth/AuthContext";
import { ApiError } from "@/services/api";
import type { TransactionInbox } from "@/features/transactions/types";

type PushDevice = {
  id: string;
  platform: string;
  device_name: string;
  is_active: boolean;
};

type ReminderPreferences = {
  daily_expense_enabled: boolean;
  weekly_income_enabled: boolean;
  budget_alerts_enabled: boolean;
  local_hour: number;
  local_minute: number;
  timezone: string;
};

export default function ProfileScreen() {
  const { authenticatedRequest, deleteAccount, logout, user } = useAuth();
  const [devices, setDevices] = useState<PushDevice[]>([]);
  const [pushBusy, setPushBusy] = useState(false);
  const [pushMessage, setPushMessage] = useState<string | null>(null);
  const [reminders, setReminders] = useState<ReminderPreferences | null>(null);
  const [reminderBusy, setReminderBusy] = useState(false);
  const [reminderMessage, setReminderMessage] = useState<string | null>(null);
  const [transactionInbox, setTransactionInbox] =
    useState<TransactionInbox | null>(null);
  const [deleteVisible, setDeleteVisible] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteMessage, setDeleteMessage] = useState<string | null>(null);

  const loadDevices = useCallback(async () => {
    try {
      setDevices(await authenticatedRequest<PushDevice[]>("/push-devices"));
    } catch {
      setDevices([]);
    }
  }, [authenticatedRequest]);

  useEffect(() => {
    void loadDevices();
    void authenticatedRequest<ReminderPreferences>("/reminders/preferences")
      .then(setReminders)
      .catch(() => setReminderMessage("No pudimos cargar tus recordatorios."));
    void authenticatedRequest<TransactionInbox>(
      "/transaction-suggestions/inbox",
    )
      .then(setTransactionInbox)
      .catch(() => setTransactionInbox(null));
  }, [authenticatedRequest, loadDevices]);

  async function setReminder(
    field:
      | "daily_expense_enabled"
      | "weekly_income_enabled"
      | "budget_alerts_enabled",
    enabled: boolean,
  ) {
    if (!reminders) return;
    const next = { ...reminders, [field]: enabled };
    setReminders(next);
    setReminderBusy(true);
    setReminderMessage(null);
    try {
      const { timezone: _timezone, ...payload } = next;
      setReminders(
        await authenticatedRequest<ReminderPreferences>(
          "/reminders/preferences",
          { method: "PUT", body: JSON.stringify(payload) },
        ),
      );
      setReminderMessage("Preferencias guardadas.");
    } catch (reason) {
      setReminders(reminders);
      setReminderMessage(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos guardar tus preferencias.",
      );
    } finally {
      setReminderBusy(false);
    }
  }

  async function enableNotifications() {
    setPushBusy(true);
    setPushMessage(null);
    try {
      if (Platform.OS !== "ios" && Platform.OS !== "android") {
        setPushMessage("Las notificaciones push se habilitan desde iOS o Android.");
        return;
      }
      if (Platform.OS === "android") {
        await Notifications.setNotificationChannelAsync("budgets", {
          name: "Presupuestos",
          importance: Notifications.AndroidImportance.DEFAULT,
        });
      }
      const current = await Notifications.getPermissionsAsync();
      const permission = current.granted
        ? current
        : await Notifications.requestPermissionsAsync();
      if (!permission.granted) {
        setPushMessage("El permiso de notificaciones no fue concedido.");
        return;
      }
      const projectId =
        Constants.expoConfig?.extra?.eas?.projectId ??
        Constants.easConfig?.projectId;
      if (!projectId) {
        setPushMessage(
          "Falta vincular el proyecto EAS. La aplicación está preparada para registrarlo.",
        );
        return;
      }
      const token = (
        await Notifications.getExpoPushTokenAsync({ projectId })
      ).data;
      const device = await authenticatedRequest<PushDevice>("/push-devices", {
        method: "POST",
        body: JSON.stringify({
          token,
          platform: Platform.OS,
          device_name: `${Platform.OS === "ios" ? "iPhone" : "Android"} personal`,
        }),
      });
      setDevices([device]);
      setPushMessage("Notificaciones activadas en este dispositivo.");
    } catch (reason) {
      setPushMessage(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos activar las notificaciones.",
      );
    } finally {
      setPushBusy(false);
    }
  }

  async function disableNotifications() {
    setPushBusy(true);
    setPushMessage(null);
    try {
      await Promise.all(
        devices.map((device) =>
          authenticatedRequest<void>(`/push-devices/${device.id}`, {
            method: "DELETE",
          }),
        ),
      );
      setDevices([]);
      setPushMessage("Notificaciones desactivadas para tu cuenta.");
    } catch (reason) {
      setPushMessage(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos desactivar las notificaciones.",
      );
    } finally {
      setPushBusy(false);
    }
  }

  async function confirmAccountDeletion() {
    if (!deletePassword) {
      setDeleteMessage("Escribe tu contraseña para confirmar.");
      return;
    }
    setDeleteBusy(true);
    setDeleteMessage(null);
    try {
      await deleteAccount(deletePassword);
      setDeleteVisible(false);
      setDeletePassword("");
    } catch (reason) {
      setDeleteMessage(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos eliminar la cuenta.",
      );
    } finally {
      setDeleteBusy(false);
    }
  }

  function requestAccountDeletion() {
    Alert.alert(
      "¿Eliminar tu cuenta?",
      "Se borrarán permanentemente tu perfil y todos tus datos financieros.",
      [
        { text: "Cancelar", style: "cancel" },
        { text: "Continuar", style: "destructive", onPress: () => setDeleteVisible(true) },
      ],
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Perfil
        </Text>
        <View style={styles.card}>
          <Text style={styles.name}>{user?.full_name}</Text>
          <Text style={styles.email}>{user?.email}</Text>
        </View>
        <View style={styles.card}>
          <Text style={styles.settingTitle}>Movimientos desde tu correo</Text>
          <Text style={styles.settingDescription}>
            Reenvía a esta dirección los avisos de compras, transferencias o
            consignaciones que llegan desde tu entidad financiera.
          </Text>
          <Text selectable style={styles.inboxAddress}>
            {transactionInbox?.address ?? "Preparando tu dirección…"}
          </Text>
          <Text style={styles.message}>
            Solo extraemos los datos del movimiento. Siempre podrás confirmarlo
            o descartarlo antes de registrarlo.
          </Text>
        </View>
        <View style={styles.card}>
          <Text style={styles.settingTitle}>Recordatorios financieros</Text>
          <Text style={styles.settingDescription}>
            Se evalúan a las {reminders?.local_hour ?? 20}:00 en tu zona horaria.
          </Text>
          <ReminderToggle
            disabled={reminderBusy || !reminders}
            label="No registré gastos hoy"
            onChange={(enabled) =>
              void setReminder("daily_expense_enabled", enabled)
            }
            value={reminders?.daily_expense_enabled ?? false}
          />
          <ReminderToggle
            disabled={reminderBusy || !reminders}
            label="No registré ingresos esta semana"
            onChange={(enabled) =>
              void setReminder("weekly_income_enabled", enabled)
            }
            value={reminders?.weekly_income_enabled ?? false}
          />
          <ReminderToggle
            disabled={reminderBusy || !reminders}
            label="Alertas de límites de presupuesto"
            onChange={(enabled) =>
              void setReminder("budget_alerts_enabled", enabled)
            }
            value={reminders?.budget_alerts_enabled ?? false}
          />
          {reminderMessage ? (
            <Text style={styles.message}>{reminderMessage}</Text>
          ) : null}
        </View>
        <View style={styles.card}>
          <Text style={styles.settingTitle}>Alertas de presupuesto</Text>
          <Text style={styles.settingDescription}>
            Recibe un aviso cuando alcances el umbral o excedas un presupuesto.
          </Text>
          {pushMessage ? <Text style={styles.message}>{pushMessage}</Text> : null}
          {pushBusy ? (
            <ActivityIndicator color={colors.primary} style={styles.pushAction} />
          ) : (
            <Pressable
              accessibilityRole="button"
              onPress={
                devices.length
                  ? () => void disableNotifications()
                  : () => void enableNotifications()
              }
              style={styles.pushAction}
            >
              <Text style={styles.pushActionText}>
                {devices.length ? "Desactivar alertas" : "Activar alertas"}
              </Text>
            </Pressable>
          )}
        </View>
        <Pressable accessibilityRole="button" onPress={logout} style={styles.logout}>
          <Text style={styles.logoutText}>Cerrar sesión</Text>
        </Pressable>
        <Pressable
          accessibilityHint="Elimina permanentemente tu cuenta y datos financieros"
          accessibilityRole="button"
          onPress={requestAccountDeletion}
          style={styles.deleteAction}
        >
          <Text style={styles.deleteActionText}>Eliminar mi cuenta</Text>
        </Pressable>
      </ScrollView>
      <Modal
        animationType="fade"
        onRequestClose={() => setDeleteVisible(false)}
        transparent
        visible={deleteVisible}
      >
        <View style={styles.modalBackdrop}>
          <View accessibilityViewIsModal style={styles.modalCard}>
            <Text accessibilityRole="header" style={styles.settingTitle}>
              Confirmar eliminación
            </Text>
            <Text style={styles.settingDescription}>
              Esta acción es permanente. Se eliminarán movimientos, presupuestos,
              deudas, metas y configuraciones. Escribe tu contraseña para continuar.
            </Text>
            <TextInput
              accessibilityLabel="Contraseña para eliminar la cuenta"
              autoCapitalize="none"
              autoComplete="current-password"
              onChangeText={setDeletePassword}
              placeholder="Contraseña"
              secureTextEntry
              style={styles.passwordInput}
              value={deletePassword}
            />
            {deleteMessage ? <Text style={styles.deleteError}>{deleteMessage}</Text> : null}
            <View style={styles.modalActions}>
              <Pressable
                accessibilityRole="button"
                disabled={deleteBusy}
                onPress={() => {
                  setDeleteVisible(false);
                  setDeletePassword("");
                  setDeleteMessage(null);
                }}
                style={styles.cancelAction}
              >
                <Text style={styles.cancelActionText}>Cancelar</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                disabled={deleteBusy}
                onPress={() => void confirmAccountDeletion()}
                style={styles.confirmDeleteAction}
              >
                {deleteBusy ? (
                  <ActivityIndicator color={colors.surface} />
                ) : (
                  <Text style={styles.confirmDeleteText}>Eliminar definitivamente</Text>
                )}
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function ReminderToggle({
  disabled,
  label,
  onChange,
  value,
}: {
  disabled: boolean;
  label: string;
  onChange: (value: boolean) => void;
  value: boolean;
}) {
  return (
    <View style={styles.reminderRow}>
      <Text style={styles.reminderLabel}>{label}</Text>
      <Switch
        disabled={disabled}
        onValueChange={onChange}
        thumbColor={colors.surface}
        trackColor={{ false: colors.border, true: colors.primary }}
        value={value}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  container: { padding: spacing.lg, paddingBottom: 110 },
  title: { ...typography.title, color: colors.ink },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    marginTop: spacing.xl,
    padding: spacing.lg,
  },
  name: { ...typography.cardValue, color: colors.ink },
  email: { ...typography.body, color: colors.muted, marginTop: spacing.xs },
  settingTitle: { ...typography.cardValue, color: colors.ink },
  settingDescription: {
    ...typography.body,
    color: colors.muted,
    marginTop: spacing.sm,
  },
  inboxAddress: {
    ...typography.body,
    backgroundColor: colors.background,
    borderRadius: radius.sm,
    color: colors.primary,
    fontWeight: "700",
    marginTop: spacing.md,
    padding: spacing.md,
  },
  message: {
    ...typography.caption,
    color: colors.muted,
    marginTop: spacing.md,
  },
  pushAction: {
    alignItems: "center",
    borderColor: colors.primary,
    borderRadius: radius.sm,
    borderWidth: 1,
    justifyContent: "center",
    marginTop: spacing.md,
    minHeight: 46,
  },
  pushActionText: { ...typography.button, color: colors.primary },
  reminderRow: {
    alignItems: "center",
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 56,
  },
  reminderLabel: { ...typography.body, color: colors.ink, flex: 1 },
  logout: {
    alignItems: "center",
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: 52,
  },
  logoutText: { ...typography.button, color: colors.danger },
  deleteAction: { alignItems: "center", marginTop: spacing.lg, padding: spacing.md },
  deleteActionText: { ...typography.body, color: colors.danger, textDecorationLine: "underline" },
  modalBackdrop: {
    alignItems: "center",
    backgroundColor: "rgba(15, 23, 42, 0.55)",
    flex: 1,
    justifyContent: "center",
    padding: spacing.lg,
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.xl,
    width: "100%",
  },
  passwordInput: {
    ...typography.body,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    color: colors.ink,
    marginTop: spacing.lg,
    minHeight: 50,
    paddingHorizontal: spacing.md,
  },
  deleteError: { ...typography.caption, color: colors.danger, marginTop: spacing.sm },
  modalActions: { gap: spacing.sm, marginTop: spacing.lg },
  cancelAction: { alignItems: "center", minHeight: 46, justifyContent: "center" },
  cancelActionText: { ...typography.button, color: colors.ink },
  confirmDeleteAction: {
    alignItems: "center",
    backgroundColor: colors.danger,
    borderRadius: radius.sm,
    justifyContent: "center",
    minHeight: 50,
  },
  confirmDeleteText: { ...typography.button, color: colors.surface },
});
