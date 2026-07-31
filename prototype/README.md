# Prototipo navegable

Prototipo móvil de baja fidelidad para las pruebas de la Fase 0. No contiene un
backend ni reconocimiento de voz real: utiliza escenarios predeterminados para
validar comprensión, velocidad, corrección y confianza.

## Cómo abrirlo

Opción rápida: abrir `index.html` en un navegador.

Opción recomendada desde esta carpeta:

```powershell
python -m http.server 4173
```

Después, visitar `http://localhost:4173`.

## Escenarios

1. Almuerzo correctamente interpretado.
2. Gasolina con fecha relativa.
3. Salario identificado como ingreso.
4. Gasolina clasificada incorrectamente como compras.
5. Frase con dos montos posibles.
6. Estado adicional de voz no reconocida.

En escritorio, el panel izquierdo permite cambiar de escenario. En un teléfono
el panel se oculta; debe elegirse el escenario antes de ajustar la ventana.

## Alcance de la prueba

- Inicio y movimientos recientes.
- Captura de voz simulada.
- Procesamiento.
- Confirmación compacta.
- Resolución de monto ambiguo.
- Corrección de categoría.
- Error recuperable.
- Registro manual completo como alternativa a la voz.
- Confirmación de guardado.

Las otras secciones aparecen como vistas conceptuales porque no forman parte de
las tareas de usabilidad de esta iteración.
