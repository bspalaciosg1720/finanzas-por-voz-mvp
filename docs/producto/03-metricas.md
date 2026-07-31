# Métricas del MVP

## Métrica principal

**Movimientos válidos registrados por usuario activo por semana.**

Un movimiento válido es confirmado, no duplicado y no eliminado durante las
siguientes 24 horas.

## Embudo de voz

```text
voice_started
→ voice_transcribed
→ interpretation_shown
→ interpretation_confirmed
→ transaction_created
```

Medir:

- finalización por etapa;
- tiempo entre etapas;
- abandono;
- correcciones;
- error técnico.

## Indicadores de calidad

| Métrica | Objetivo beta |
|---|---:|
| Exactitud de monto | ≥95% |
| Exactitud de tipo | ≥97% |
| Acierto de categoría top-1 | ≥80% |
| Confirmaciones sin edición | ≥70% |
| Mediana del flujo de voz | ≤5 s |
| Duplicados | <1% |
| Errores técnicos de dictado | <3% |

## Activación y retención

Usuario activado:

- crea su primer movimiento;
- registra al menos tres movimientos en siete días;
- consulta el dashboard al menos una vez.

Medir:

- activación en 24 horas;
- usuarios activos semanales;
- retención en semanas 1 y 4;
- movimientos semanales por usuario;
- porcentaje de movimientos creados por voz.

## Eventos mínimos de analítica

```text
account_created
onboarding_completed
voice_started
voice_cancelled
voice_transcribed
interpretation_shown
interpretation_field_corrected
interpretation_confirmed
transaction_created
transaction_updated
transaction_deleted
dashboard_viewed
budget_created
budget_threshold_reached
report_viewed
export_requested
```

Propiedades permitidas:

- duración;
- estado;
- origen de registro;
- nombre normalizado del campo corregido;
- categoría genérica;
- rango de monto, no el monto exacto.

No enviar a analítica:

- transcripción;
- descripción;
- monto exacto;
- correo;
- audio;
- token;
- identificadores bancarios.

