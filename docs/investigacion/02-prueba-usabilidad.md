# Prueba de usabilidad del prototipo

## Objetivo

Validar que una persona pueda registrar, revisar y corregir movimientos por voz
sin entrenamiento y en menos de cinco segundos para casos simples.

## Prototipo mínimo necesario

Pantallas:

1. Inicio.
2. Estado de escucha.
3. Transcripción.
4. Confirmación correcta.
5. Confirmación con campo dudoso.
6. Edición rápida de monto.
7. Movimiento guardado.
8. Lista de movimientos.

No se necesita backend ni reconocimiento real. La interacción puede simularse.

## Preparación

- Dispositivo móvil de tamaño común.
- Grabación de pantalla con consentimiento.
- Cronómetro desde que termina la frase.
- Hoja de observación.
- Datos ficticios.

## Introducción

> Estamos probando el diseño, no tus habilidades. Piensa en voz alta. Algunas
> respuestas están simuladas. No uses datos financieros reales.

## Tareas

### Tarea 1: gasto simple

> Imagina que acabas de pagar $18.000 por el almuerzo. Regístralo hablando.

Éxito: confirma gasto, monto y alimentación sin ayuda.

### Tarea 2: fecha relativa

> Ayer compraste gasolina por $90.000. Registra ese movimiento.

Éxito: comprende que la fecha interpretada es ayer.

### Tarea 3: ingreso

> Recibiste $1.000.000 de salario. Regístralo.

Éxito: distingue ingreso de gasto.

### Tarea 4: categoría incorrecta

El prototipo interpreta gasolina como “Compras”.

Éxito: detecta el error, modifica la categoría y guarda.

### Tarea 5: monto dudoso

El prototipo muestra dos posibilidades.

Éxito: entiende la duda y selecciona el monto correcto.

## Preguntas posteriores

1. ¿Qué creías que ocurriría al confirmar?
2. ¿Hubo algún dato que no revisaste?
3. ¿Qué tan seguro te sentirías usando esta función? De 1 a 5.
4. ¿En qué situación usarías el formulario en vez de la voz?
5. ¿Qué información sobre privacidad esperarías encontrar?

## Hoja de observación

| Tarea | Completada | Tiempo | Ayuda | Error | Campo corregido |
|---|---|---:|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

## Criterios de aprobación

- 4 de cada 5 participantes completan tareas simples sin ayuda.
- Mediana de 5 segundos o menos después de finalizar el dictado.
- Al menos 80% identifica correctamente qué se guardará.
- Al menos 80% encuentra cómo corregir monto y categoría.
- Confianza media igual o superior a 4/5.

