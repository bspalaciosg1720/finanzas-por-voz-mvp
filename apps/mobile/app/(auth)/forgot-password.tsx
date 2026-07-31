import { Link } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { colors, spacing, typography } from "@/design-system/tokens";
import { AuthButton, AuthInput, FormError } from "@/features/auth/AuthControls";
import { AuthScaffold } from "@/features/auth/AuthScaffold";
import { apiRequest, ApiError } from "@/services/api";

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setError(null);
    setLoading(true);
    try {
      await apiRequest<void>("/auth/password/forgot", {
        method: "POST",
        body: JSON.stringify({ email: email.trim() }),
      });
      setSent(true);
    } catch (reason) {
      setError(
        reason instanceof ApiError ? reason.message : "No pudimos enviar la solicitud.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthScaffold
      title="Recupera tu cuenta"
      subtitle="Si el correo está registrado, recibirás un enlace válido durante 30 minutos."
      footer={
        <Text style={styles.footer}>
          <Link href="/(auth)/login" style={styles.link}>
            Volver al inicio de sesión
          </Link>
        </Text>
      }
    >
      {sent ? (
        <Text accessibilityLiveRegion="polite" style={styles.success}>
          Revisa tu correo y sigue las instrucciones.
        </Text>
      ) : (
        <>
          <AuthInput
            autoCapitalize="none"
            autoComplete="email"
            keyboardType="email-address"
            label="Correo"
            onChangeText={setEmail}
            value={email}
          />
          <FormError message={error} />
          <AuthButton label="Enviar enlace" loading={loading} onPress={submit} />
        </>
      )}
    </AuthScaffold>
  );
}

const styles = StyleSheet.create({
  success: {
    ...typography.body,
    backgroundColor: colors.primarySoft,
    borderRadius: 16,
    color: colors.primary,
    lineHeight: 24,
    padding: spacing.md,
  },
  footer: { marginTop: spacing.xl, textAlign: "center" },
  link: { color: colors.primary, fontWeight: "700" },
});

