"""Parser determinista de referencia para validar lenguaje financiero en español.

No es código de producción. Su propósito es establecer una línea base medible
durante la Fase 0 sin depender todavía de proveedores de IA o Speech-to-Text.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


NUMBER_WORDS = {
    "cero": 0,
    "un": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "veintiuno": 21,
    "veintidos": 22,
    "veintitres": 23,
    "veinticuatro": 24,
    "veinticinco": 25,
    "veintiseis": 26,
    "veintisiete": 27,
    "veintiocho": 28,
    "veintinueve": 29,
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
    "cien": 100,
    "ciento": 100,
    "doscientos": 200,
    "trescientos": 300,
    "cuatrocientos": 400,
    "quinientos": 500,
    "seiscientos": 600,
    "setecientos": 700,
    "ochocientos": 800,
    "novecientos": 900,
}

INCOME_MARKERS = (
    "me pagaron",
    "recibi",
    "me consignaron",
    "vendi",
    "reembolso",
    "me devolvieron",
    "ingreso",
)

CATEGORY_KEYWORDS = {
    "Alimentación": ("almuerzo", "desayuno", "mercado", "comida", "restaurante"),
    "Transporte": ("gasolina", "taxi", "bus", "transporte", "parqueadero"),
    "Salud": ("medicamentos", "consulta medica", "medico", "farmacia"),
    "Educación": ("matricula", "libros", "curso", "colegio", "universidad"),
    "Vivienda": ("arriendo", "vivienda", "administracion"),
    "Servicios": ("energia", "internet", "agua", "telefono", "gas"),
    "Entretenimiento": ("cine", "concierto", "juego"),
    "Compras": ("ropa", "zapatos", "compra"),
    "Mascotas": ("veterinario", "mascota"),
    "Viajes": ("hotel", "vuelo", "viaje"),
    "Salario": ("salario", "nomina"),
    "Trabajo independiente": ("trabajo", "honorarios"),
    "Ventas": ("vendi", "venta"),
    "Reembolsos": ("reembolso", "devolvieron", "devolucion"),
    "Otros ingresos": ("de un amigo",),
    "Otros": ("regalo",),
}

DATE_MARKERS = (
    ("esta manana", "today_morning"),
    ("anoche", "yesterday_night"),
    ("ayer", "yesterday"),
    ("hoy", "today"),
)


@dataclass(frozen=True)
class ParsedTransaction:
    movement_type: str
    amount: int | None
    category: str
    date_rule: str


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def contains_phrase(text: str, phrase: str) -> bool:
    pattern = rf"(?<![a-z]){re.escape(phrase)}(?![a-z])"
    return re.search(pattern, text) is not None


def parse_number_words(text: str) -> int | None:
    normalized = normalize(text)

    digit_match = re.search(r"\b\d[\d.,]*\b", normalized)
    if digit_match:
        return int(re.sub(r"[.,]", "", digit_match.group()))

    tokens = re.findall(r"[a-z]+", normalized)
    best: int | None = None

    for start in range(len(tokens)):
        total = 0
        current = 0
        consumed = False

        for token in tokens[start:]:
            if token == "y":
                continue
            if token in NUMBER_WORDS:
                current += NUMBER_WORDS[token]
                consumed = True
                continue
            if token in ("mil", "miles") and consumed:
                current = max(current, 1) * 1_000
                total += current
                current = 0
                continue
            if token in ("millon", "millones") and consumed:
                current = max(current, 1) * 1_000_000
                total += current
                current = 0
                continue
            break

        if consumed:
            candidate = total + current
            if best is None or candidate > best:
                best = candidate

    return best


def parse_transaction(text: str) -> ParsedTransaction:
    normalized = normalize(text)
    movement_type = (
        "income"
        if any(contains_phrase(normalized, marker) for marker in INCOME_MARKERS)
        else "expense"
    )

    category = "Otros"
    for candidate, keywords in CATEGORY_KEYWORDS.items():
        if any(contains_phrase(normalized, keyword) for keyword in keywords):
            category = candidate
            break

    date_rule = "today"
    for marker, rule in DATE_MARKERS:
        if contains_phrase(normalized, marker):
            date_rule = rule
            break

    return ParsedTransaction(
        movement_type=movement_type,
        amount=parse_number_words(normalized),
        category=category,
        date_rule=date_rule,
    )
