import { Link } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { colors, spacing, typography } from "@/design-system/tokens";
import { AuthButton, AuthInput, FormError } from "@/features/auth/AuthControls";
import { useAuth } from "@/features/auth/AuthContext";
import { AuthScaffold } from "@/features/auth/AuthScaffold";
import { ApiError } from "@/services/api";

export default function RegisterScreen() {
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (password.length < 10) {
      setError("La contraseña debe tener al menos 10 caracteres.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await register({
        full_name: name.trim(),
        email: email.trim(),
        password,
      });
    } catch (reason) {
      setError(
        reason instanceof ApiError ? reason.message : "No pudimos crear la cuenta.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthScaffold
      title="Crea tu cuenta"
      subtitle="Empieza a registrar tus finanzas sin formularios complicados."
      footer={
        <Text style={styles.footer}>
          ¿Ya tienes cuenta?{" "}
          <Link href="/(auth)/login" style={styles.link}>
            Iniciar sesión
          </Link>
        </Text>
      }
    >
      <AuthInput
        autoComplete="name"
        label="Nombre"
        onChangeText={setName}
        value={name}
      />
      <AuthInput
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        label="Correo"
        onChangeText={setEmail}
        value={email}
      />
      <AuthInput
        autoComplete="new-password"
        label="Contraseña"
        onChangeText={setPassword}
        secureTextEntry
        value={password}
      />
      <Text style={styles.help}>Mínimo 10 caracteres.</Text>
      <FormError message={error} />
      <AuthButton label="Crear cuenta" loading={loading} onPress={submit} />
    </AuthScaffold>
  );
}

const styles = StyleSheet.create({
  help: { color: colors.muted, fontSize: 12, marginTop: -spacing.sm },
  footer: {
    ...typography.body,
    color: colors.muted,
    marginTop: spacing.xl,
    textAlign: "center",
  },
  link: { color: colors.primary, fontWeight: "700" },
});

