"""Evalúa el parser contra el dataset etiquetado y genera un informe Markdown."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from finance_parser import parse_transaction


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "voice_phrases_seed.csv"
REPORT = ROOT / "validation" / "parser-report.md"


def percentage(value: int, total: int) -> float:
    return round(value * 100 / total, 2)


def main() -> None:
    with DATASET.open(encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    correct = Counter()
    failures: list[dict[str, str]] = []

    for row in rows:
        parsed = parse_transaction(row["text"])
        checks = {
            "amount": parsed.amount == int(row["amount"]),
            "type": parsed.movement_type == row["type"],
            "category": parsed.category == row["category"],
            "date": parsed.date_rule == row["date_rule"],
        }
        correct.update(name for name, passed in checks.items() if passed)

        if not all(checks.values()):
            failures.append(
                {
                    "id": row["id"],
                    "text": row["text"],
                    "fields": ", ".join(name for name, passed in checks.items() if not passed),
                    "expected": f"{row['type']} · {row['amount']} · {row['category']} · {row['date_rule']}",
                    "actual": (
                        f"{parsed.movement_type} · {parsed.amount} · "
                        f"{parsed.category} · {parsed.date_rule}"
                    ),
                }
            )

    total = len(rows)
    exact = total - len(failures)
    metrics = {
        "Monto": percentage(correct["amount"], total),
        "Tipo": percentage(correct["type"], total),
        "Categoría": percentage(correct["category"], total),
        "Fecha relativa": percentage(correct["date"], total),
        "Frase completa": percentage(exact, total),
    }

    lines = [
        "# Informe de validación del parser",
        "",
        "Línea base determinista evaluada contra el dataset sintético de Fase 0.",
        "No representa precisión en audio real ni lenguaje espontáneo.",
        "",
        "## Resultados",
        "",
        "| Campo | Precisión | Umbral MVP | Estado |",
        "|---|---:|---:|---|",
    ]

    thresholds = {"Monto": 95, "Tipo": 97, "Categoría": 80}
    for name, score in metrics.items():
        threshold = thresholds.get(name)
        threshold_label = f"{threshold}%" if threshold else "Por definir"
        status = "Cumple" if threshold is not None and score >= threshold else (
            "No cumple" if threshold is not None else "Informativo"
        )
        lines.append(f"| {name} | {score:.2f}% | {threshold_label} | {status} |")

    lines.extend(
        [
            "",
            f"- Frases evaluadas: {total}.",
            f"- Frases completamente correctas: {exact}.",
            f"- Frases con algún error: {len(failures)}.",
            "",
            "## Errores de muestra",
            "",
            "| ID | Campos | Esperado | Obtenido |",
            "|---|---|---|---|",
        ]
    )

    for failure in failures[:20]:
        lines.append(
            f"| {failure['id']} | {failure['fields']} | "
            f"{failure['expected']} | {failure['actual']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretación",
            "",
            "- Esta prueba evalúa texto limpio; Speech-to-Text debe medirse por separado.",
            "- El dataset sintético puede favorecer las reglas que lo generaron.",
            "- La siguiente evaluación debe utilizar frases reales no vistas por el parser.",
            "- Los casos ambiguos deben producir confirmación, no una predicción forzada.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Evaluadas {total} frases")
    for name, score in metrics.items():
        print(f"{name}: {score:.2f}%")
    print(f"Informe: {REPORT}")


if __name__ == "__main__":
    main()

