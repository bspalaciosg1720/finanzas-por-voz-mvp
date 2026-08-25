"""Fail when tracked files contain common secret material or private credentials."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {
    ".env",
    "credentials.json",
    "google-services.json",
    "GoogleService-Info.plist",
}
FORBIDDEN_SUFFIXES = {".jks", ".keystore", ".p8", ".p12", ".pem"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "OpenAI key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        relative = path.relative_to(ROOT)
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(f"forbidden credential file: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                findings.append(f"possible {label}: {relative}")
    if findings:
        print("Security check failed:")
        print("\n".join(f"- {finding}" for finding in findings))
        return 1
    print("Security check passed: no common secrets found in tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
