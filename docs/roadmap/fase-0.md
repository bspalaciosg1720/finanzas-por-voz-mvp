# Fase 0: descubrimiento y validación

Duración sugerida: 10 días laborables.

> Estado: cerrada condicionalmente el 30 de julio de 2026 mediante aceptación
> formal del riesgo de avanzar sin participantes. Las hipótesis de deseabilidad y
> usabilidad continúan sin validar.

## Objetivo

Reducir el riesgo de construir una solución que las personas no usarían, y cerrar
el alcance funcional y de experiencia antes de iniciar el desarrollo.

## Semana 1

### Día 1 — Alineación

- [x] Brief de producto.
- [x] Público inicial.
- [x] Alcance y exclusiones.
- [x] Hipótesis priorizadas.
- [ ] Asignar responsable de producto.
- [ ] Definir presupuesto y tamaño del equipo.

### Días 2 y 3 — Investigación

- [x] Guion de entrevistas.
- [x] Preparar filtro, consentimiento y kit de reclutamiento.
- [ ] Reclutar 8 a 12 participantes.
- [ ] Ejecutar primeras 5 entrevistas.
- [x] Crear repositorio anónimo de hallazgos.

### Día 4 — Síntesis inicial

- [ ] Agrupar patrones de comportamiento.
- [ ] Identificar contextos favorables y desfavorables para voz.
- [x] Crear mapa de recorrido actual como hipótesis.
- [ ] Actualizar hipótesis.

### Día 5 — Prototipo

- [x] Diseñar wireframes de baja fidelidad.
- [x] Conectar el flujo navegable.
- [x] Preparar estados correctos, dudosos y de error.
- [x] Definir tareas de usabilidad.

## Semana 2

### Días 6 y 7 — Pruebas

- [ ] Probar con 5 participantes.
- [ ] Medir tiempo, éxito, errores y confianza.
- [x] Automatizar el cálculo de métricas de las sesiones.
- [ ] Corregir los principales problemas.

### Día 8 — Lenguaje

- [x] Crear una semilla sintética de 150 frases etiquetadas.
- [x] Implementar y medir una línea base determinista.
- [ ] Sustituir o complementar la semilla con frases reales anonimizadas.
- [ ] Incluir expresiones regionales reales y casos ambiguos observados.

### Día 9 — Segunda iteración

- [ ] Probar el prototipo corregido.
- [ ] Comparar registro por voz y manual.
- [ ] Validar el dashboard durante cinco segundos.

### Día 10 — Decisión

- [ ] Revisar los criterios de salida.
- [ ] Congelar alcance del MVP.
- [ ] Priorizar backlog de construcción.
- [ ] Documentar decisión: avanzar, ajustar o detener.

## Entregables

- Brief de producto.
- Matriz de hipótesis.
- Informe de entrevistas.
- Mapa de recorrido.
- Prototipo navegable.
- Informe de usabilidad.
- Dataset inicial de frases.
- Métricas y eventos.
- Alcance final del MVP.

## Criterios de salida

- Dolor observado en al menos 6 de 10 entrevistas.
- Preferencia por voz ≥70% en tareas simples.
- Comprensión de la confirmación ≥80%.
- Mediana del flujo simulado ≤5 segundos.
- Corrección de monto y categoría encontrada por ≥80%.
- Dataset con al menos 150 frases etiquetadas.
- Sin bloqueos graves de privacidad, accesibilidad o viabilidad.

## Decisión

| Resultado | Acción |
|---|---|
| Cumple todos los criterios críticos | Iniciar Fase 1 |
| Falla velocidad o comprensión | Iterar UX una semana |
| Falla precisión pero existe demanda | Probar otro pipeline de interpretación |
| Rechazo contextual generalizado de voz | Reposicionar voz como acceso secundario |
| No existe dolor recurrente | Detener o redefinir el segmento |
