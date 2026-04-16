"""Kommandozeilen-Einstiegspunkt für die Ledger-Demo.

Ausführen mit::

    uv run ledger
    # oder
    python -m ledger

Diese Datei demonstriert drei aufeinander aufbauende Konzepte:

1. **In-Memory-Konto** – BankAccount mit generatorbasierter Iteration.
2. **Lazy Log-Leser** – Klassenbasierter Iterator und Generator-Funktion im Vergleich.
3. **Pipeline-Komposition** – Generator-Filter und -Aggregation à la Unix-Pipes.
"""

import sys
from pathlib import Path

from .account import BankAccount
from .analytics import filter_by_currency, filter_by_type, running_total, summarize
from .models import TransactionType
from .reader import parse_transactions, read_log_file

# Standardpfad relativ zum Projektverzeichnis (zwei Ebenen über diesem Modul)
_DEFAULT_LOG = Path(__file__).parent.parent.parent / "data" / "transactions_large.log"


def demo_account() -> None:
    """Demo 1: BankAccount mit generatorbasierter Iteration."""
    print("=" * 60)
    print("DEMO 1 – In-Memory BankAccount (Generator-Iteration)")
    print("=" * 60)

    account = BankAccount("Erika Mustermann", "AT98765")
    account.deposit(1_000.00)
    account.deposit(250.50)
    account.withdraw(120.00)
    account.deposit(75.00)

    print(f"Konto:    {account.owner} ({account.account_number})")
    print(f"Guthaben: {account.balance:.2f} EUR\n")

    print("Transaktionshistorie (1. Iteration):")
    for tx in account:
        print(f"  {tx}")

    # Zweite Iteration funktioniert, weil __iter__ einen neuen Generator erzeugt
    deposits = [tx for tx in account if tx.type == TransactionType.DEPOSIT]
    print(f"\nNur Einzahlungen (2. Iteration): {len(deposits)} Transaktionen")


def demo_reader(log_path: Path) -> None:
    """Demo 2: Lazy Log-Datei-Leser (Generator-Funktion)."""
    print("\n" + "=" * 60)
    print("DEMO 2 – Lazy Log-Reader (Generator-Funktion mit try/finally)")
    print("=" * 60)

    print(f"Lese: {log_path.name} ({log_path.stat().st_size:,} Bytes)\n")
    print("Erste 5 WITHDRAW-Transaktionen:")

    count = 0
    # read_log_file öffnet die Datei erst beim Iterieren – lazy!
    for line in read_log_file(str(log_path), filter_keyword="WITHDRAW"):
        print(f"  {line}")
        count += 1
        if count >= 5:
            # break löst den finally-Block im Generator aus → Datei wird geschlossen
            break

    print(f"\n→ Datei nach break sauber geschlossen (try/finally im Generator)")


def demo_pipeline(log_path: Path) -> None:
    """Demo 3: Komposierbare Generator-Pipeline."""
    print("\n" + "=" * 60)
    print("DEMO 3 – Komposierbare Analytics-Pipeline")
    print("=" * 60)

    print("Pipeline: read_log_file → parse_transactions → filter_by_currency → summarize\n")

    # Jede Funktion nimmt einen Iterator und gibt einen Iterator zurück.
    # Kein Schritt lädt die gesamte Datei in den Speicher.
    lines   = read_log_file(str(log_path))
    all_tx  = parse_transactions(lines)
    eur_tx  = filter_by_currency(all_tx, "EUR")
    stats   = summarize(eur_tx)  # Terminal-Operator: konsumiert den Stream

    print("EUR-Transaktionen – Zusammenfassung:")
    for tx_type, count in sorted(stats["counts"].items(), key=lambda x: x[0].value):
        total = stats["totals"][tx_type]
        print(f"  {tx_type.value:<10} {count:>5} Transaktionen   Σ {total:>14,.2f} EUR")

    eur_net = stats["by_currency"].get("EUR", 0.0)
    print(f"\n  Netto-EUR-Saldo: {eur_net:>14,.2f} EUR")

    # Zweite Pipeline: laufender Saldo für die ersten 10 Einzahlungen
    print("\nLaufender Saldo – erste 10 Einzahlungen (alle Währungen):")
    lines2   = read_log_file(str(log_path))
    all_tx2  = parse_transactions(lines2)
    deposits = filter_by_type(all_tx2, TransactionType.DEPOSIT)

    for i, (tx, balance) in enumerate(running_total(deposits)):
        print(f"  {tx}   Σ {balance:>12.2f}")
        if i >= 9:
            break


def main() -> None:
    """Einstiegspunkt für ``uv run ledger``."""
    log_path = _DEFAULT_LOG
    if not log_path.exists():
        print(
            f"FEHLER: Log-Datei nicht gefunden: {log_path}\n"
            "Hinweis: Stelle sicher, dass 'data/transactions_large.log' existiert.",
            file=sys.stderr,
        )
        sys.exit(1)

    demo_account()
    demo_reader(log_path)
    demo_pipeline(log_path)
    print("\nFertig.")
