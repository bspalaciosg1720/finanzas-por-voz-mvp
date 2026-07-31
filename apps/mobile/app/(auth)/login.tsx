import { Link } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { colors, spacing, typography } from "@/design-system/tokens";
import { AuthButton, AuthInput, FormError } from "@/features/auth/AuthControls";
import { useAuth } from "@/features/auth/AuthContext";
import { AuthScaffold } from "@/features/auth/AuthScaffold";
import { ApiError } from "@/services/api";

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setError(null);
    setLoading(true);
    try {
      await login(email.trim(), password);
    } catch (reason) {
      setError(
        reason instanceof ApiError ? reason.message : "No pudimos iniciar sesión.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthScaffold
      title="Bienvenido de nuevo"
      subtitle="Ingresa para consultar y registrar tus movimientos."
      footer={
        <Text style={styles.footer}>
          ¿No tienes cuenta?{" "}
          <Link href="/(auth)/register" style={styles.link}>
            Crear cuenta
          </Link>
        </Text>
      }
    >
      <AuthInput
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        label="Correo"
        onChangeText={setEmail}
        value={email}
      />
      <AuthInput
        autoComplete="password"
        label="Contraseña"
        onChangeText={setPassword}
        secureTextEntry
        value={password}
      />
      <Link href="/(auth)/forgot-password" style={styles.forgot}>
        Olvidé mi contraseña
      </Link>
      <FormError message={error} />
      <AuthButton label="Iniciar sesión" loading={loading} onPress={submit} />
    </AuthScaffold>
  );
}

const styles = StyleSheet.create({
  forgot: { color: colors.primary, fontWeight: "700", textAlign: "right" },
  footer: {
    ...typography.body,
    color: colors.muted,
    marginTop: spacing.xl,
    textAlign: "center",
  },
  link: { color: colors.primary, fontWeight: "700" },
});

