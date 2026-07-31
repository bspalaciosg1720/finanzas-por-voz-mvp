# Hipótesis y experimentos

## Matriz priorizada

| ID | Hipótesis | Riesgo | Experimento | Señal de validación |
|---|---|---:|---|---|
| H1 | La voz reduce el esfuerzo percibido | Alto | Prototipo comparando voz y formulario | 70% prefiere voz para movimientos simples |
| H2 | El usuario confía si puede confirmar | Alto | Cinco tareas con datos interpretados | 80% entiende qué se guardará sin ayuda |
| H3 | El flujo puede completarse en <5 s | Alto | Prueba cronometrada con prototipo | Mediana ≤5 s desde fin del dictado |
| H4 | El monto puede extraerse con precisión | Alto | Dataset de 150 frases colombianas | Exactitud ≥95% |
| H5 | La categoría automática ahorra tiempo | Medio | Comparar sugerencia contra elección real | Acierto top-1 ≥80% |
| H6 | Existe uso en contextos cotidianos | Alto | Diario de siete días | ≥60% registra en el momento o <10 min |
| H7 | La alerta del 80% genera acción | Medio | Entrevista y prueba conceptual | ≥50% declara una acción concreta |
| H8 | El dashboard responde dudas reales | Medio | Prueba de comprensión de 5 segundos | 80% identifica gastos y saldo correctamente |

## Experimento 1: entrevistas de problema

- Participantes: 8 a 12.
- Duración: 30 minutos.
- Objetivo: descubrir hábitos actuales, abandonos, contexto y lenguaje.
- No mostrar la solución durante los primeros 20 minutos.
- Registrar frases exactas utilizadas para montos, fechas y categorías.

Decisión:

- Continuar si al menos 6 participantes describen fricción recurrente al registrar.
- Reformular el público si el dolor existe solo en un segmento distinto.
- Detener la propuesta de voz si la mayoría rechaza usarla incluso en privado.

## Experimento 2: prototipo de voz simulado

Usar un prototipo “Mago de Oz”: el usuario habla y el moderador o prototipo
presenta inmediatamente una interpretación preparada. Así se valida la experiencia
antes de integrar reconocimiento real.

Tareas:

1. Registrar un almuerzo de $18.000.
2. Registrar gasolina de ayer por $90.000.
3. Registrar un salario de $1.000.000.
4. Corregir una categoría incorrecta.
5. Corregir un monto ambiguo.

Mediciones:

- tiempo por tarea;
- errores;
- campos corregidos;
- comprensión de la confirmación;
- confianza de 1 a 5;
- preferencia frente al registro manual.

## Experimento 3: dataset de lenguaje

Crear al menos 150 frases anonimizadas:

- 60 gastos cotidianos;
- 30 ingresos;
- 20 fechas relativas;
- 20 expresiones coloquiales;
- 20 casos ambiguos o con autocorrección.

Cada caso tendrá una salida esperada:

```json
{
  "text": "Ayer pagué noventa mil de gasolina",
  "type": "expense",
  "amount": 90000,
  "currency": "COP",
  "category": "Transporte",
  "date_rule": "yesterday",
  "description": "Gasolina"
}
```

No se deben almacenar nombres, cuentas bancarias, direcciones ni información
sensible de los participantes.

## Experimento 4: diario de uso

- Participantes: 5.
- Duración: 7 días.
- Instrumento: formulario breve o prototipo.
- Evento registrado: movimiento, contexto, método preferido y razón para posponer.

Preguntas después de cada registro:

1. ¿Dónde estabas?
2. ¿Podías hablar en ese momento?
3. ¿Qué método habrías usado?
4. ¿Cuánto tardaste en registrarlo?
5. ¿Qué te habría impedido hacerlo?

## Criterio general para pasar a construcción

La fase se considera validada cuando:

- hay evidencia de dolor en al menos 6 de 10 entrevistas;
- 70% prefiere voz en al menos dos de las tareas simples;
- 80% comprende la confirmación sin explicación;
- la mediana del flujo simulado es de 5 segundos o menos;
- el equipo reúne 150 frases etiquetadas;
- no aparece un impedimento grave de privacidad o contexto.

