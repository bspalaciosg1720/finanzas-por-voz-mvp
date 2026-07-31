# Dataset inicial de frases

`voice_phrases_seed.csv` contiene 150 frases sintéticas etiquetadas para iniciar
las pruebas del parser:

- 120 gastos;
- 30 ingresos;
- 15 valores diferentes;
- fechas como hoy, ayer, esta mañana y anoche;
- categorías financieras principales.

## Generación

```powershell
python generate_seed.py
```

## Advertencia

Este dataset es una semilla técnica y no valida el lenguaje del mercado. Durante
las entrevistas debe complementarse con frases reales anonimizadas, expresiones
regionales, ruido, autocorrecciones y casos ambiguos.

No deben incluirse nombres, cuentas, direcciones ni datos financieros reales.

