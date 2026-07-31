import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";

import { AuthButton, FormError } from "@/features/auth/AuthControls";
import { AuthScaffold } from "@/features/auth/AuthScaffold";
import { apiRequest, ApiError } from "@/services/api";

export default function VerifyEmailScreen() {
  const params = useLocalSearchParams<{ token?: string }>();
  const token = Array.isArray(params.token) ? params.token[0] : params.token;
  const [loading, setLoading] = useState(true);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setError("El enlace no contiene un token válido.");
      setLoading(false);
      return;
    }
    apiRequest<void>("/auth/verify-email/confirm", {
      method: "POST",
      body: JSON.stringify({ token }),
    })
      .then(() => setVerified(true))
      .catch((reason) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "No pudimos verificar el correo.",
        ),
      )
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <AuthScaffold
      title={verified ? "Correo verificado" : "Verificando correo"}
      subtitle={
        verified
          ? "Tu cuenta ya está preparada."
          : "Estamos comprobando que el enlace sea válido."
      }
    >
      <FormError message={error} />
      {!loading && (
        <AuthButton
          label={verified ? "Continuar" : "Volver al inicio"}
          onPress={() => router.replace("/")}
        />
      )}
    </AuthScaffold>
  );
}

