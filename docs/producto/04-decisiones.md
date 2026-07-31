# Registro de decisiones de producto

Las decisiones marcadas como **provisionales** pueden cambiar después de las
entrevistas. Las decisiones **técnicas** reducen errores independientemente de la
preferencia del usuario.

| ID | Decisión | Estado | Razón | Evidencia pendiente |
|---|---|---|---|---|
| D001 | Iniciar con Colombia, español y COP | Provisional | Reduce variaciones regionales | Demanda del segmento |
| D002 | Confirmar antes de guardar por voz | Provisional | Protege contra errores financieros | Preferencia y fatiga |
| D003 | Mantener registro manual | Confirmada | Voz no es apropiada en todo contexto | Ninguna |
| D004 | Usar monolito modular | Técnica | Menor complejidad inicial | Carga real |
| D005 | Almacenar dinero como enteros | Técnica | Evita errores de punto flotante | Exponente por moneda |
| D006 | Eliminar audio tras procesarlo | Provisional | Minimiza riesgo de privacidad | Necesidad de soporte |
| D007 | Alertar al 80% y 100% | Provisional | Permite actuar antes del límite | Utilidad percibida |
| D008 | CSV como primera exportación | Provisional | Menor costo y formato interoperable | Demanda PDF/Excel |
| D009 | Micrófono visible en Inicio y Movimientos | Provisional | Acceso en un toque | Descubribilidad |
| D010 | No usar microservicios en el MVP | Técnica | Evita operación distribuida prematura | Ninguna |
| D011 | Solicitar permiso al primer uso | Confirmada | Mejora contexto y comprensión | Ninguna |
| D012 | No enviar datos financieros a analítica | Confirmada | Privacidad y minimización | Ninguna |

## Decisiones que requieren evidencia antes de Fase 1

1. Confirmación siempre visible o solamente ante baja confianza.
2. Necesidad de saldo inicial.
3. Posición y forma del botón de voz.
4. Categorías predeterminadas finales.
5. Horarios y frecuencia de recordatorios.

## Formato para nuevas decisiones

```text
ID:
Fecha:
Decisión:
Estado:
Contexto:
Opciones consideradas:
Razón:
Evidencia:
Consecuencias:
Responsable:
Fecha de revisión:
```

