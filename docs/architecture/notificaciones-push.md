# Notificaciones push

## Alcance implementado

- Alta explícita de dispositivos autenticados.
- Un token pertenece a un único usuario y puede actualizarse de forma
  idempotente.
- Listado sin revelar el token push.
- Revocación por el propietario.
- Adaptadores de entrega intercambiables: deshabilitado para entornos sin
  proveedor y falso para pruebas.
- Solicitud de permisos y registro desde la pantalla de perfil.

## Flujo

1. El usuario activa las notificaciones desde Perfil.
2. El móvil solicita permiso al sistema operativo.
3. Expo genera el token usando el `projectId` del proyecto.
4. La API guarda el token asociado al usuario y dispositivo.
5. Un proceso de entrega futuro consume alertas pendientes y utiliza el
   adaptador configurado.
6. El usuario puede revocar el dispositivo desde la aplicación.

## Controles de seguridad y privacidad

- La API nunca devuelve tokens push.
- Todos los endpoints requieren autenticación.
- El listado y la revocación están aislados por usuario.
- La activación requiere una acción explícita.
- El adaptador permanece deshabilitado por defecto.

## Requisitos antes de producción

- Configurar Expo/EAS y sus credenciales fuera del repositorio.
- Probar en dispositivos físicos iOS y Android con un build de desarrollo.
- Gestionar tokens inválidos o expirados a partir de los recibos del proveedor.
- Añadir un worker con reintentos limitados, trazabilidad y supresión de
  duplicados.
- Documentar retención, finalidad y revocación en la política de privacidad.
