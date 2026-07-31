# Mapa del recorrido financiero

Este mapa es una hipótesis de diseño. Debe corregirse con evidencia de entrevistas.

## Recorrido actual

| Etapa | Situación | Acción habitual | Pensamiento | Fricción | Oportunidad |
|---|---|---|---|---|---|
| Movimiento | Paga o recibe dinero | Guarda recibo, revisa el banco o confía en su memoria | “Luego lo anoto” | Tiene prisa o está con otras personas | Captura inmediata y discreta |
| Recordatorio | Horas o días después | Intenta recordar el monto y la categoría | “¿Cuánto fue exactamente?” | Información incompleta | Borradores y recordatorios oportunos |
| Registro | Abre app, nota o tabla | Completa varios campos | “Esto toma demasiado” | Formularios, categorías y fechas | Voz, valores predeterminados y confirmación compacta |
| Revisión | Fin de semana o mes | Suma movimientos y busca faltantes | “Estos números no cuadran” | Duplicados y movimientos ausentes | Resumen transparente y edición rápida |
| Decisión | Observa que gastó demasiado | Intenta reducir una categoría | “Ya es tarde para corregirlo” | Información retrospectiva | Alertas antes de superar el límite |

## Recorrido propuesto

| Etapa | Acción del usuario | Respuesta del producto | Tiempo objetivo | Estado emocional |
|---|---|---|---:|---|
| Acceso | Abre la aplicación | Muestra saldo y micrófono | <1 s | Orientado |
| Captura | Pulsa y habla | Transcribe parcialmente | 1–3 s | En control |
| Interpretación | Termina la frase | Extrae movimiento y señala dudas | <1,5 s | Informado |
| Confirmación | Revisa y confirma | Guarda una única vez | <1 s | Seguro |
| Consecuencia | Continúa con su actividad | Actualiza saldo y presupuesto | Inmediato | Tranquilo |
| Prevención | Se acerca a un límite | Envía alerta clara y configurable | Oportuna | Capaz de actuar |

## Momento crítico

La confirmación es el punto de mayor riesgo:

- si muestra demasiados campos, elimina el ahorro de tiempo;
- si oculta campos, reduce la confianza;
- si guarda automáticamente, un error de monto puede ser grave;
- si siempre pregunta demasiado, la voz se siente más lenta que un formulario.

La primera versión mostrará monto, tipo, categoría, fecha y descripción en una sola
vista. Cada campo será editable en un toque.

## Modos de registro según contexto

| Contexto | Método recomendado | Razón |
|---|---|---|
| Casa o lugar privado | Voz | Menor esfuerzo |
| Calle tranquila | Voz o texto | Depende de ruido y privacidad |
| Transporte público | Texto rápido | Evita exponer montos |
| Reunión o trabajo | Manual compacto | Discreción |
| Sin conexión | Manual o borrador | No depender del proveedor |
| Movimiento complejo | Formulario | Mayor control |

## Preguntas para validar

- ¿El registro ocurre inmediatamente o se acumula?
- ¿La confirmación siempre visible genera seguridad o cansancio?
- ¿Qué información revisa primero el usuario?
- ¿La descripción aporta valor o puede ser opcional?
- ¿Qué contexto hace que la voz resulte socialmente incómoda?

