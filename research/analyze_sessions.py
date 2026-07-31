"""Analiza sesiones reales de usabilidad sin inventar datos faltantes."""

from __future__ import annotations

import argparse
import csv
import statistics
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs" / "investigacion" / "03-registro-sesiones.csv"
DEFAULT_OUTPUT = ROOT / "docs" / "investigacion" / "07-resultados-calculados.md"

TASKS = range(1, 6)
TRUE_VALUES = {"true", "1", "yes", "si", "sí", "y"}
VOICE_VALUES = {"voice", "voz", "si", "sí", "yes", "true", "1"}


@dataclass(frozen=True)
class Metric:
    name: str
    result: float
    target: float
    comparison: str
    unit: str = "%"

    @property
    def passes(self) -> bool:
        return self.result >= self.target if self.comparison == ">=" else self.result <= self.target


def clean(value: str | None) -> str:
    return (value or "").strip().lower()


def parse_bool(value: str | None) -> bool | None:
    normalized = clean(value)
    if not normalized:
        return None
    return normalized in TRUE_VALUES


def parse_number(value: str | None) -> float | None:
    normalized = clean(value).replace(",", ".")
    if not normalized:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def completed_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if clean(row.get("participant_code"))
        and any(clean(row.get(f"task_{task}_success")) for task in TASKS)
    ]


def calculate_metrics(rows: list[dict[str, str]]) -> tuple[list[Metric], list[str]]:
    metrics: list[Metric] = []
    warnings: list[str] = []

    simple_successes: list[bool] = []
    simple_times: list[float] = []
    correction_successes: list[bool] = []
    confidence: list[float] = []
    voice_preferences: list[bool] = []

    for row in rows:
        for task in (1, 2, 3):
            success = parse_bool(row.get(f"task_{task}_success"))
            seconds = parse_number(row.get(f"task_{task}_seconds"))
            if success is not None:
                simple_successes.append(success)
            if seconds is not None:
                simple_times.append(seconds)

        for task in (4, 5):
            success = parse_bool(row.get(f"task_{task}_success"))
            if success is not None:
                correction_successes.append(success)

        score = parse_number(row.get("confidence_1_5"))
        if score is not None:
            confidence.append(score)

        preference = clean(row.get("voice_preference"))
        if preference:
            voice_preferences.append(preference in VOICE_VALUES)

    if simple_successes:
        metrics.append(
            Metric(
                "Éxito en tareas simples",
                100 * sum(simple_successes) / len(simple_successes),
                80,
                ">=",
            )
        )
    else:
        warnings.append("No hay resultados de éxito para las tareas 1–3.")

    if simple_times:
        metrics.append(
            Metric(
                "Mediana del flujo simple",
                statistics.median(simple_times),
                5,
                "<=",
                " s",
            )
        )
    else:
        warnings.append("No hay tiempos para las tareas 1–3.")

    if correction_successes:
        metrics.append(
            Metric(
                "Corrección sin ayuda",
                100 * sum(correction_successes) / len(correction_successes),
                80,
                ">=",
            )
        )
    else:
        warnings.append("No hay resultados para las tareas 4–5.")

    if confidence:
        metrics.append(
            Metric(
                "Confianza media",
                statistics.mean(confidence),
                4,
                ">=",
                "/5",
            )
        )
    else:
        warnings.append("No hay puntuaciones de confianza.")

    if voice_preferences:
        metrics.append(
            Metric(
                "Preferencia por voz",
                100 * sum(voice_preferences) / len(voice_preferences),
                70,
                ">=",
            )
        )
    else:
        warnings.append("No hay respuestas de preferencia.")

    return metrics, warnings


def recommendation(metrics: list[Metric], participants: int) -> str:
    if participants < 5:
        return "Evidencia insuficiente: ejecutar al menos cinco pruebas completas."
    if not metrics:
        return "Evidencia insuficiente: faltan métricas calculables."

    failures = [metric for metric in metrics if not metric.passes]
    if not failures:
        return (
            "Los criterios de usabilidad medidos cumplen. Revisar también las "
            "entrevistas de problema antes de autorizar la Fase 1."
        )
    names = ", ".join(metric.name for metric in failures)
    return f"Iterar el prototipo y repetir la prueba. No cumplen: {names}."


def render_report(
    rows: list[dict[str, str]],
    metrics: list[Metric],
    warnings: list[str],
) -> str:
    lines = [
        "# Resultados calculados de usabilidad",
        "",
        f"- Participantes con tareas registradas: {len(rows)}.",
        "- Fuente: `03-registro-sesiones.csv`.",
        "",
        "## Métricas",
        "",
        "| Métrica | Resultado | Objetivo | Estado |",
        "|---|---:|---:|---|",
    ]

    if metrics:
        for metric in metrics:
            result = (
                f"{metric.result:.2f}{metric.unit}"
                if metric.unit != "%"
                else f"{metric.result:.2f}%"
            )
            target = f"{metric.comparison} {metric.target:g}{metric.unit}"
            lines.append(
                f"| {metric.name} | {result} | {target} | "
                f"{'Cumple' if metric.passes else 'No cumple'} |"
            )
    else:
        lines.append("| Sin datos suficientes | — | — | Pendiente |")

    lines.extend(["", "## Recomendación", "", recommendation(metrics, len(rows)), ""])

    if warnings:
        lines.extend(["## Datos faltantes", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")

    lines.extend(
        [
            "## Nota metodológica",
            "",
            "Este informe calcula resultados de usabilidad. La validación del problema",
            "y del contexto de uso debe sintetizarse por separado a partir de entrevistas.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8-sig", newline="") as file:
        rows = completed_rows(list(csv.DictReader(file)))

    metrics, warnings = calculate_metrics(rows)
    args.output.write_text(render_report(rows, metrics, warnings), encoding="utf-8")
    print(f"Participantes analizados: {len(rows)}")
    print(f"Informe: {args.output}")


if __name__ == "__main__":
    main()

