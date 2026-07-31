# Verificación de correo y recuperación de contraseña

## Tokens

- Se generan con entropía criptográfica.
- La base de datos conserva solamente SHA-256.
- Verificación de correo: 24 horas.
- Recuperación de contraseña: 30 minutos.
- Cada token puede utilizarse una sola vez.
- Solicitar uno nuevo invalida los anteriores del mismo propósito.

## Verificación

```text
POST /auth/verify-email/request   Requiere access token
POST /auth/verify-email/confirm   Recibe token de un solo uso
```

## Recuperación

```text
POST /auth/password/forgot
POST /auth/password/reset
```

La solicitud de recuperación siempre devuelve 202, exista o no el correo, para
evitar enumeración de cuentas.

Al cambiar la contraseña:

- se actualiza el hash Argon2;
- se revocan todas las sesiones;
- el token queda consumido;
- la contraseña anterior deja de funcionar.

## Entrega

Desarrollo utiliza `tmp/mailbox`, excluido de Git. Staging y producción requieren
SMTP y una URL pública; la configuración rechaza el modo local en esos ambientes.
Los tokens no deben aparecer en logs ni herramientas de analítica.

