"""Auditoría reproducible de contraste para los tokens principales del prototipo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pair:
    name: str
    foreground: str
    background: str
    large_text: bool = False


PAIRS = [
    Pair("Texto principal sobre fondo", "#202624", "#F4F5F2"),
    Pair("Texto secundario sobre fondo", "#68716D", "#F4F5F2"),
    Pair("Texto principal sobre blanco", "#202624", "#FFFFFF"),
    Pair("Texto secundario sobre blanco", "#68716D", "#FFFFFF"),
    Pair("Blanco sobre azul petróleo", "#FFFFFF", "#245B62"),
    Pair("Azul petróleo sobre fondo suave", "#245B62", "#E8F0F0"),
    Pair("Error sobre fondo", "#A34D4D", "#F4F5F2"),
]


def channel(value: int) -> float:
    normalized = value / 255
    return normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def contrast(first: str, second: str) -> float:
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def main() -> None:
    failed = []
    for pair in PAIRS:
        ratio = contrast(pair.foreground, pair.background)
        target = 3 if pair.large_text else 4.5
        status = "PASS" if ratio >= target else "FAIL"
        print(f"{status} {pair.name}: {ratio:.2f}:1 (objetivo {target}:1)")
        if ratio < target:
            failed.append(pair.name)

    if failed:
        raise SystemExit(f"No cumplen contraste: {', '.join(failed)}")


if __name__ == "__main__":
    main()

