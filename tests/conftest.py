"""Gemeinsame pytest-Fixtures für die ledger-Testsuite.

Fixtures in dieser Datei werden automatisch an alle Testmodule
im selben Verzeichnis weitergegeben – kein Import nötig.
"""

from pathlib import Path

import pytest

# Repräsentative Log-Zeilen im echten Format der Log-Datei
SAMPLE_LINES = [
    "ID: T1000 | TYPE: WITHDRAW | AMOUNT: 6657.49 | CURRENCY: USD",
    "ID: T1001 | TYPE: DEPOSIT  | AMOUNT: 1000.00 | CURRENCY: EUR",
    "ID: T1002 | TYPE: PAYMENT  | AMOUNT:  250.00 | CURRENCY: EUR",
    "ID: T1003 | TYPE: DEPOSIT  | AMOUNT:  500.00 | CURRENCY: GBP",
]


@pytest.fixture
def sample_log_file(tmp_path: Path) -> Path:
    """Temporäre Transaktions-Log-Datei mit 4 wohlgeformten Zeilen."""
    log_file = tmp_path / "test_transactions.log"
    log_file.write_text("\n".join(SAMPLE_LINES) + "\n", encoding="utf-8")
    return log_file


@pytest.fixture
def sample_log_file_with_blanks(tmp_path: Path) -> Path:
    """Log-Datei mit eingestreuten Leerzeilen – sollten übersprungen werden."""
    log_file = tmp_path / "test_with_blanks.log"
    content = (
        SAMPLE_LINES[0] + "\n"
        "\n"
        + SAMPLE_LINES[1] + "\n"
        "\n\n"
        + SAMPLE_LINES[2] + "\n"
        + SAMPLE_LINES[3] + "\n"
    )
    log_file.write_text(content, encoding="utf-8")
    return log_file
