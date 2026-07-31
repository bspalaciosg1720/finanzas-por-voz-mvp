import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";

import { AuthButton, AuthInput, FormError } from "@/features/auth/AuthControls";
import { AuthScaffold } from "@/features/auth/AuthScaffold";
import { apiRequest, ApiError } from "@/services/api";

export default function ResetPasswordScreen() {
  const params = useLocalSearchParams<{ token?: string }>();
  const token = Array.isArray(params.token) ? params.token[0] : params.token;
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState<string | null>(
    token ? null : "El enlace no contiene un token válido.",
  );
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!token) return;
    if (password.length < 10) {
      setError("La contraseña debe tener al menos 10 caracteres.");
      return;
    }
    if (password !== confirmation) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await apiRequest<void>("/auth/password/reset", {
        method: "POST",
        body: JSON.stringify({ token, new_password: password }),
      });
      router.replace("/(auth)/login");
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos actualizar la contraseña.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthScaffold
      title="Nueva contraseña"
      subtitle="El cambio cerrará todas las sesiones abiertas."
    >
      <AuthInput
        autoComplete="new-password"
        label="Nueva contraseña"
        onChangeText={setPassword}
        secureTextEntry
        value={password}
      />
      <AuthInput
        autoComplete="new-password"
        label="Confirmar contraseña"
        onChangeText={setConfirmation}
        secureTextEntry
        value={confirmation}
      />
      <FormError message={error} />
      <AuthButton label="Cambiar contraseña" loading={loading} onPress={submit} />
    </AuthScaffold>
  );
}

