# Contrato de interpretación por voz

## Separación de responsabilidades

La transcripción y la interpretación son operaciones distintas. El primer
incremento recibe texto ya transcrito en:

`POST /api/v1/voice/interpretations`

La respuesta propone tipo, monto, moneda, categoría, descripción, fecha,
confianza por campo y una lista de ambigüedades.

La operación no persiste movimientos. `requires_confirmation` es siempre
verdadero, de acuerdo con ADR-002.

## Comportamiento seguro

- Si no existe una señal clara de ingreso o gasto, el tipo queda vacío.
- Si aparecen dos montos numéricos, el monto queda vacío.
- Si la categoría no está disponible para el usuario, no se asigna.
- Las fechas relativas se resuelven en la zona horaria del usuario.
- La confirmación posterior usará la API idempotente de movimientos.

## Confianza

Los valores actuales son heurísticos y sirven para ordenar la experiencia de
confirmación. No representan probabilidades calibradas. Solo podrán calibrarse
después de medir frases espontáneas y errores reales de Speech-to-Text.

## Privacidad

La captura móvil usa `expo-audio`, solicita el permiso en contexto, desactiva la
grabación en segundo plano y limita cada intento a 15 segundos. El archivo queda
en caché, no puede superar 5 MB y se elimina explícitamente al cancelar, cerrar
o volver a grabar.

## Evaluación reproducible

Las 150 frases sintéticas de Fase 0 se ejecutan dentro de la suite de la API. La
prueba comprueba tipo, monto y las categorías compatibles con el catálogo del
MVP. Esta cobertura detecta regresiones deterministas, pero no sustituye audio
real ni frases espontáneas.

La grabación todavía no sale del dispositivo. El adaptador de transcripción
deberá eliminarla también después de éxito o error y aplicar un límite de tamaño
antes de cualquier carga.

Mientras no exista un proveedor configurado, la aplicación ofrece una
transcripción editable como mecanismo de desarrollo y accesibilidad. Esta ruta
usa el mismo contrato de interpretación, presenta las ambigüedades, permite
corregir tipo, monto, categoría y descripción, y solo entonces crea el
movimiento con idempotencia. No se presenta como transcripción automática.

## Adaptador de transcripción

`POST /api/v1/voice/transcriptions` recibe audio autenticado mediante multipart.
Solo admite M4A, MP4, MP3, WAV o WebM, rechaza archivos vacíos y aplica un máximo
de 5 MB también en el servidor.

El servicio depende de una interfaz `AudioTranscriber`:

- `DisabledTranscriber` devuelve un error 503 uniforme;
- `FakeTranscriber` es determinista y solo se inyecta desde pruebas;
- el proveedor real se añadirá sin modificar el endpoint ni la aplicación.

El contenido se mantiene en memoria durante la llamada, se limpia en `finally`
y `UploadFile` se cierra tanto en éxito como en error. El móvil elimina además
su archivo local después de cualquier intento y conserva la alternativa de
transcripción editable.

## Métricas sin contenido financiero

Cada interpretación genera un identificador técnico. Al completar o abandonar
el flujo, la aplicación informa:

- resultado `completed` o `abandoned`;
- duración en milisegundos;
- cantidad de ambigüedades;
- nombres de campos corregidos.

La tabla no posee columnas para audio, transcripción, monto o descripción. La
finalización es idempotente, está aislada por usuario y un fallo de telemetría
nunca bloquea ni reintenta la creación del movimiento.
