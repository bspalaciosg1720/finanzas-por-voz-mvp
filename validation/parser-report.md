# Informe de validación del parser

Línea base determinista evaluada contra el dataset sintético de Fase 0.
No representa precisión en audio real ni lenguaje espontáneo.

## Resultados

| Campo | Precisión | Umbral MVP | Estado |
|---|---:|---:|---|
| Monto | 100.00% | 95% | Cumple |
| Tipo | 100.00% | 97% | Cumple |
| Categoría | 100.00% | 80% | Cumple |
| Fecha relativa | 100.00% | Por definir | Informativo |
| Frase completa | 100.00% | Por definir | Informativo |

- Frases evaluadas: 150.
- Frases completamente correctas: 150.
- Frases con algún error: 0.

## Errores de muestra

| ID | Campos | Esperado | Obtenido |
|---|---|---|---|

## Interpretación

- Esta prueba evalúa texto limpio; Speech-to-Text debe medirse por separado.
- El dataset sintético puede favorecer las reglas que lo generaron.
- La siguiente evaluación debe utilizar frases reales no vistas por el parser.
- Los casos ambiguos deben producir confirmación, no una predicción forzada.
