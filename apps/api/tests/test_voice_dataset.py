import csv
from pathlib import Path

import pytest
from app.modules.voice.parser import normalize, parse_voice_text

DATASET = Path(__file__).parents[3] / "dataset" / "voice_phrases_seed.csv"
SUPPORTED_CATEGORY_SLUGS = {
    "alimentacion",
    "transporte",
    "salud",
    "educacion",
    "vivienda",
    "servicios",
    "entretenimiento",
    "compras",
    "mascotas",
    "viajes",
}


def load_cases() -> list[dict[str, str]]:
    with DATASET.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


@pytest.mark.parametrize("case", load_cases(), ids=lambda case: case["id"])
def test_production_parser_against_synthetic_seed(case: dict[str, str]) -> None:
    parsed = parse_voice_text(case["text"], timezone="America/Bogota")

    assert parsed.movement_type == case["type"]
    assert parsed.amount_minor == int(case["amount"])

    expected_category = normalize(case["category"]).replace(" ", "-")
    if expected_category in SUPPORTED_CATEGORY_SLUGS:
        assert parsed.category_slug == expected_category
