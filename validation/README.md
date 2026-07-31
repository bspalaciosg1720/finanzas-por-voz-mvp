# Validación técnica del parser

Prueba de concepto determinista para establecer una línea base de extracción de:

- monto;
- tipo de movimiento;
- categoría;
- fecha relativa.

## Ejecutar pruebas

Desde la raíz:

```powershell
python -m unittest discover -s validation -p "test_*.py"
```

## Evaluar dataset

```powershell
python validation/evaluate_parser.py
```

El resultado se guarda en `parser-report.md`.

## Límites

- No procesa audio.
- No representa lenguaje espontáneo.
- No debe utilizarse como parser de producción.
- El dataset sintético comparte vocabulario con las reglas.
- La evaluación válida debe utilizar frases reales no vistas.

