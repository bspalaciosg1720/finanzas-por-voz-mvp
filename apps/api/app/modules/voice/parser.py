import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

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
    "me devolvieron",
    "vendi",
    "salario",
    "nomina",
    "reembolso",
    "ingreso",
)
EXPENSE_MARKERS = (
    "gaste",
    "pague",
    "compre",
    "me cobraron",
    "costo",
    "gasto",
)
CATEGORY_KEYWORDS = {
    "alimentacion": ("almuerzo", "desayuno", "mercado", "comida", "restaurante"),
    "transporte": ("gasolina", "taxi", "bus", "transporte", "parqueadero"),
    "salud": ("medicamentos", "consulta medica", "medico", "farmacia"),
    "educacion": ("matricula", "libros", "curso", "colegio", "universidad"),
    "vivienda": ("arriendo", "vivienda", "administracion"),
    "servicios": ("energia", "internet", "agua", "telefono", "gas"),
    "entretenimiento": ("cine", "concierto", "juego"),
    "compras": ("ropa", "zapatos", "compra"),
    "mascotas": ("veterinario", "mascota"),
    "viajes": ("hotel", "vuelo", "viaje"),
}


@dataclass(frozen=True)
class ParsedVoiceText:
    movement_type: str | None
    amount_minor: int | None
    category_slug: str | None
    description: str
    occurred_at: datetime
    confidence: dict[str, float]
    ambiguities: list[str]


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])", text) is not None


def parse_number(text: str) -> int | None:
    digit_match = re.search(r"\b\d[\d.,]*\b", text)
    if digit_match:
        return int(re.sub(r"[.,]", "", digit_match.group()))

    tokens = re.findall(r"[a-z]+", text)
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
            if token in {"mil", "miles"} and consumed:
                total += max(current, 1) * 1_000
                current = 0
                continue
            if token in {"millon", "millones"} and consumed:
                total += max(current, 1) * 1_000_000
                current = 0
                continue
            break
        if consumed:
            candidate = total + current
            if best is None or candidate > best:
                best = candidate
    return best


def parse_voice_text(
    transcript: str,
    *,
    timezone: str,
    reference_at: datetime | None = None,
) -> ParsedVoiceText:
    text = normalize(transcript)
    local_now = (reference_at or datetime.now(ZoneInfo(timezone))).astimezone(
        ZoneInfo(timezone)
    )
    ambiguities: list[str] = []

    income = any(contains_phrase(text, marker) for marker in INCOME_MARKERS)
    expense = any(contains_phrase(text, marker) for marker in EXPENSE_MARKERS)
    movement_type = (
        None
        if income == expense
        else "income"
        if income
        else "expense"
    )
    if movement_type is None:
        ambiguities.append("movement_type_uncertain")

    numeric_amounts = re.findall(r"\b\d[\d.,]*\b", text)
    amount = parse_number(text)
    if len(numeric_amounts) > 1:
        amount = None
        ambiguities.append("multiple_amounts")
    elif amount is None or amount <= 0:
        amount = None
        ambiguities.append("amount_missing")

    category_slug = None
    matched_keyword = None
    for slug, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if contains_phrase(text, keyword):
                category_slug = slug
                matched_keyword = keyword
                break
        if category_slug:
            break
    if category_slug is None:
        ambiguities.append("category_uncertain")

    occurred_at = local_now
    date_confidence = 0.75
    if contains_phrase(text, "anoche"):
        occurred_at = datetime.combine(
            local_now.date() - timedelta(days=1),
            time(20, 0),
            tzinfo=local_now.tzinfo,
        )
        date_confidence = 0.95
    elif contains_phrase(text, "ayer"):
        occurred_at -= timedelta(days=1)
        date_confidence = 0.95
    elif contains_phrase(text, "hoy"):
        date_confidence = 0.95

    description = matched_keyword.capitalize() if matched_keyword else transcript[:80]
    return ParsedVoiceText(
        movement_type=movement_type,
        amount_minor=amount,
        category_slug=category_slug,
        description=description,
        occurred_at=occurred_at,
        confidence={
            "amount": 0.98 if amount is not None else 0.0,
            "movement_type": 0.95 if movement_type else 0.0,
            "category": 0.9 if category_slug else 0.0,
            "description": 0.8 if matched_keyword else 0.45,
            "occurred_at": date_confidence,
        },
        ambiguities=ambiguities,
    )
