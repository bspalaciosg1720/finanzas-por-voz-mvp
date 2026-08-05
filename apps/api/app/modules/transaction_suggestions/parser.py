import re
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ParsedFinancialEmail:
    type: str
    amount_minor: int
    currency: str
    description: str
    occurred_at: datetime
    confidence: float


AMOUNT_PATTERNS = (
    re.compile(r"(?:COP|\$)\s*([0-9][0-9.,]{2,})", re.IGNORECASE),
    re.compile(r"(?:por|valor(?:\s+de)?)\s*(?:COP|\$)?\s*([0-9][0-9.,]{2,})", re.IGNORECASE),
)
INCOME_WORDS = ("recibiste", "abono", "consignación", "consignacion", "transferencia recibida")
EXPENSE_WORDS = ("compra", "pagaste", "pago", "retiro", "débito", "debito")


def parse_financial_email(
    subject: str, text: str, occurred_at: datetime
) -> ParsedFinancialEmail | None:
    content = " ".join(f"{subject} {text}".split())
    lowered = content.lower()
    amount = next(
        (match.group(1) for pattern in AMOUNT_PATTERNS if (match := pattern.search(content))), None
    )
    if amount is None:
        return None
    normalized = amount.replace(".", "").replace(",", "")
    if not normalized.isdigit() or int(normalized) <= 0:
        return None
    movement_type = "income" if any(word in lowered for word in INCOME_WORDS) else "expense"
    has_type_signal = any(word in lowered for word in (*INCOME_WORDS, *EXPENSE_WORDS))
    description = extract_description(content, movement_type)
    return ParsedFinancialEmail(
        type=movement_type,
        amount_minor=int(normalized),
        currency="COP",
        description=description,
        occurred_at=occurred_at,
        confidence=0.92 if has_type_signal and description else 0.78,
    )


def extract_description(content: str, movement_type: str) -> str:
    patterns = (
        r"(?:en|comercio|establecimiento)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ0-9 .&_-]{2,60})",
        r"(?:de|desde)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ0-9 .&_-]{2,60})",
    )
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            value = re.split(r"\s+(?:el|por|con|desde|a las)\s+", match.group(1), maxsplit=1)[0]
            return value.strip(" .,-")[:240]
    return (
        "Ingreso detectado por correo"
        if movement_type == "income"
        else "Compra detectada por correo"
    )
