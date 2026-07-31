# Requisitos para finalizar y lanzar el MVP

Este documento separa el desarrollo local de las dependencias que requieren
credenciales, infraestructura, dispositivos o participantes externos.

## Obligatorios para completar el producto

### 1. Speech-to-Text

- Elegir OpenAI Audio/Whisper o reconocimiento del sistema.
- Configurar la clave únicamente como secreto del backend; nunca en Expo.
- Habilitar facturación y límites de consumo.
- Definir modelo, idioma, duración y tamaño máximo del audio.
- Aprobar la política de privacidad y eliminación del audio.

Esto bloquea la transcripción automática, pero no el parser ni la confirmación.

### 2. Infraestructura de staging

- Instancia PostgreSQL administrada.
- URL HTTPS para la API.
- Gestor de secretos para JWT, SMTP y Speech-to-Text.
- Dominio de staging.
- Ejecución real de migraciones, backup y restauración.

Docker no está instalado localmente. El SQL y CI están preparados, pero falta
una ejecución real contra PostgreSQL.

### 3. Repositorio y CI remoto

- Repositorio GitHub del producto y permiso para publicar la rama.
- Secretos y variables del workflow.
- Protección de la rama principal y revisión obligatoria.

El workflow existe, pero falta demostrar una ejecución remota.

### 4. Pruebas en dispositivos

- Al menos un Android físico y un iPhone físico.
- Cuenta Expo/EAS o entorno nativo equivalente para builds internos.
- Pruebas de micrófono, permisos, interrupciones, red y accesibilidad.

### 5. Validación con usuarios

- Cinco pruebas moderadas y ocho entrevistas pendientes de Fase 0.
- Consentimientos y reclutamiento.
- Medición de tiempo, correcciones, abandono y confianza.
- Dataset anonimizado de frases espontáneas.

El riesgo se aceptó para avanzar, pero esta evidencia continúa siendo
obligatoria antes de un lanzamiento público.

### 6. Privacidad y operación

- Política de privacidad y términos.
- Canal para eliminación de cuenta y datos.
- Plazos de conservación de logs, transcripciones y backups.
- Revisión legal del país de lanzamiento.
- Monitoreo, alertas y procedimiento de incidentes.

## Necesarios para distribución pública

- Cuentas de Apple Developer y Google Play Console.
- Certificados y perfiles de firma.
- Política de privacidad publicada.
- Fichas de tienda, capturas, iconos y clasificación de contenido.
- Credenciales APNs/FCM o proyecto Expo para notificaciones.

## Opcionales para el MVP

- Inicio con Google y Apple.
- Integración bancaria y escaneo de facturas.
- Múltiples monedas simultáneas.
- Aplicación web.
- Modo familiar o empresarial.

## Información que no debe enviarse por chat

- Claves API, secretos JWT o contraseñas.
- Credenciales SMTP o de base de datos.
- Certificados de firma.

Estos valores deben configurarse directamente en un gestor de secretos o en un
archivo local ignorado por Git.
