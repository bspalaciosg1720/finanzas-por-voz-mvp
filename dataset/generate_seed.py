"""Genera un dataset sintético inicial para probar el parser financiero.

Este conjunto no reemplaza las frases recogidas en entrevistas. Sirve para
construir pruebas reproducibles mientras se obtiene lenguaje real.
"""

from __future__ import annotations

import csv
from pathlib import Path


OUTPUT = Path(__file__).with_name("voice_phrases_seed.csv")

EXPENSES = [
    ("Gasté {spoken} en almuerzo", "Alimentación", "Almuerzo"),
    ("Pagué {spoken} por el desayuno", "Alimentación", "Desayuno"),
    ("Compré mercado por {spoken}", "Alimentación", "Mercado"),
    ("Compré gasolina por {spoken}", "Transporte", "Gasolina"),
    ("Pagué {spoken} de taxi", "Transporte", "Taxi"),
    ("Me cobraron {spoken} del bus", "Transporte", "Bus"),
    ("Pagué {spoken} en medicamentos", "Salud", "Medicamentos"),
    ("Gasté {spoken} en una consulta médica", "Salud", "Consulta médica"),
    ("Pagué {spoken} de matrícula", "Educación", "Matrícula"),
    ("Compré libros por {spoken}", "Educación", "Libros"),
    ("Pagué el arriendo por {spoken}", "Vivienda", "Arriendo"),
    ("Pagué {spoken} de energía", "Servicios", "Energía"),
    ("La factura de internet costó {spoken}", "Servicios", "Internet"),
    ("Gasté {spoken} en cine", "Entretenimiento", "Cine"),
    ("Compré ropa por {spoken}", "Compras", "Ropa"),
    ("Pagué {spoken} en el veterinario", "Mascotas", "Veterinario"),
    ("Gasté {spoken} en el hotel", "Viajes", "Hotel"),
    ("Pagué {spoken} por un regalo", "Otros", "Regalo"),
]

INCOMES = [
    ("Me pagaron {spoken} de salario", "Salario", "Salario"),
    ("Recibí {spoken} de un amigo", "Otros ingresos", "Dinero de un amigo"),
    ("Me consignaron {spoken} por un trabajo", "Trabajo independiente", "Trabajo"),
    ("Vendí una mesa por {spoken}", "Ventas", "Venta de mesa"),
    ("Recibí un reembolso de {spoken}", "Reembolsos", "Reembolso"),
    ("Me devolvieron {spoken}", "Reembolsos", "Devolución"),
]

AMOUNTS = [
    (8000, "ocho mil"),
    (12000, "doce mil"),
    (18000, "dieciocho mil"),
    (25000, "veinticinco mil"),
    (28500, "veintiocho mil quinientos"),
    (40000, "cuarenta mil"),
    (50000, "cincuenta mil"),
    (75000, "setenta y cinco mil"),
    (90000, "noventa mil"),
    (120000, "ciento veinte mil"),
    (150000, "ciento cincuenta mil"),
    (350000, "trescientos cincuenta mil"),
    (800000, "ochocientos mil"),
    (1000000, "un millón"),
    (2500000, "dos millones quinientos mil"),
]

DATE_VARIANTS = [
    ("", "today"),
    (" hoy", "today"),
    (" ayer", "yesterday"),
    (" esta mañana", "today_morning"),
    (" anoche", "yesterday_night"),
]

CONTEXT_VARIANTS = [
    "",
    " con la tarjeta",
    " en efectivo",
    " desde mi cuenta",
    " para este mes",
    " esta semana",
    " en el centro",
    " antes de llegar a casa",
]


def create_rows() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    row_id = 1

    for index in range(120):
        template, category, description = EXPENSES[index % len(EXPENSES)]
        amount, spoken = AMOUNTS[(index * 7) % len(AMOUNTS)]
        suffix, date_rule = DATE_VARIANTS[(index // len(EXPENSES)) % len(DATE_VARIANTS)]
        context = CONTEXT_VARIANTS[(index // 7) % len(CONTEXT_VARIANTS)]
        rows.append(
            {
                "id": f"E{row_id:03}",
                "text": template.format(spoken=spoken) + context + suffix,
                "type": "expense",
                "amount": amount,
                "currency": "COP",
                "category": category,
                "description": description,
                "date_rule": date_rule,
                "ambiguity": "none",
                "source": "synthetic_seed",
            }
        )
        row_id += 1

    for index in range(30):
        template, category, description = INCOMES[index % len(INCOMES)]
        amount, spoken = AMOUNTS[(index * 5 + 8) % len(AMOUNTS)]
        suffix, date_rule = DATE_VARIANTS[index % len(DATE_VARIANTS)]
        context = CONTEXT_VARIANTS[(index // len(INCOMES)) % len(CONTEXT_VARIANTS)]
        rows.append(
            {
                "id": f"I{index + 1:03}",
                "text": template.format(spoken=spoken) + context + suffix,
                "type": "income",
                "amount": amount,
                "currency": "COP",
                "category": category,
                "description": description,
                "date_rule": date_rule,
                "ambiguity": "none",
                "source": "synthetic_seed",
            }
        )

    return rows


def main() -> None:
    rows = create_rows()
    if len(rows) != 150:
        raise RuntimeError(f"Se esperaban 150 filas y se generaron {len(rows)}")

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generadas {len(rows)} frases en {OUTPUT}")


if __name__ == "__main__":
    main()
