"""Validaciones estructurales mínimas del contrato sin dependencias externas."""

from pathlib import Path


CONTRACT = Path(__file__).with_name("openapi.yaml")

REQUIRED_MARKERS = [
    "openapi: 3.1.0",
    "/auth/register:",
    "/auth/login:",
    "/transactions:",
    "/transactions/{transaction_id}:",
    "/voice/interpretations:",
    "/voice/interpretations/{interpretation_id}/confirm:",
    "Idempotency-Key",
    "application/problem+json",
    "amount_minor:",
    "bearerAuth:",
]


def main() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    if missing:
        raise SystemExit(f"Faltan elementos obligatorios: {', '.join(missing)}")

    if "\t" in text:
        raise SystemExit("El YAML contiene tabulaciones")

    print(f"Contrato verificado: {CONTRACT}")
    print(f"Elementos obligatorios: {len(REQUIRED_MARKERS)}")


if __name__ == "__main__":
    main()

