"""Generator-basierte Analyse-Pipeline für Transaktionsströme.

Alle Funktionen akzeptieren und geben *Iterables* von ``Transaction``-Objekten
zurück. Das ermöglicht die Komposition zu lazy Pipelines, ohne den gesamten
Datensatz je vollständig in den Speicher zu laden:

.. code-block:: python

    from ledger import read_log_file, parse_transactions
    from ledger.analytics import filter_by_currency, filter_by_type, summarize
    from ledger.models import TransactionType

    # Lazy Pipeline: Lesen → Parsen → Filtern → Aggregieren
    lines        = read_log_file("data/transactions_large.log")
    all_tx       = parse_transactions(lines)
    eur_deposits = filter_by_type(filter_by_currency(all_tx, "EUR"), TransactionType.DEPOSIT)
    stats        = summarize(eur_deposits)

Das ist das klassische Unix-Pipe-Konzept – aber in Python mit Generatoren.
"""

from collections import defaultdict
from collections.abc import Iterable, Iterator

from .models import Transaction, TransactionType


def filter_by_type(
    transactions: Iterable[Transaction],
    tx_type: TransactionType,
) -> Iterator[Transaction]:
    """Liefert nur Transaktionen des angegebenen Typs.

    Args:
        transactions: Quell-Iterable von Transaction-Objekten.
        tx_type: Der gewünschte :class:`~ledger.models.TransactionType`.

    Yields:
        Transaktionen, deren ``type`` mit *tx_type* übereinstimmt.

    Example::

        deposits = list(filter_by_type(my_transactions, TransactionType.DEPOSIT))
    """
    for tx in transactions:
        if tx.type == tx_type:
            yield tx


def filter_by_currency(
    transactions: Iterable[Transaction],
    currency: str,
) -> Iterator[Transaction]:
    """Liefert nur Transaktionen in der angegebenen Währung.

    Der Vergleich ist Groß-/Kleinschreibungs-unabhängig
    (``"eur"`` findet ``"EUR"``).

    Args:
        transactions: Quell-Iterable von Transaction-Objekten.
        currency: ISO-4217-Währungscode (z. B. ``"EUR"``).

    Yields:
        Transaktionen, deren ``currency`` mit *currency* übereinstimmt.
    """
    # Einmalig normalisieren statt bei jeder Transaktion
    target = currency.upper()
    for tx in transactions:
        if tx.currency.upper() == target:
            yield tx


def running_total(
    transactions: Iterable[Transaction],
) -> Iterator[tuple[Transaction, float]]:
    """Liefert ``(Transaktion, laufender_Saldo)``-Paare.

    Einzahlungen erhöhen den laufenden Saldo, Abhebungen und Zahlungen
    reduzieren ihn. Der Saldo ist **nicht** währungsbewusst – das Mischen
    von Währungen führt zu bedeutungslosen Ergebnissen.

    Args:
        transactions: Quell-Iterable von Transaction-Objekten.

    Yields:
        Tupel aus ``(Transaction, float)``, wobei der Float der kumulative
        Saldo nach Anwenden der Transaktion ist.

    Example::

        for tx, balance in running_total(account):
            print(f"{tx}  →  Saldo: {balance:.2f}")
    """
    balance = 0.0
    for tx in transactions:
        if tx.type == TransactionType.DEPOSIT:
            balance += tx.amount
        else:
            # WITHDRAW und PAYMENT reduzieren den Saldo gleichermassen
            balance -= tx.amount
        yield tx, balance


def summarize(transactions: Iterable[Transaction]) -> dict:
    """Konsumiert einen Transaktionsstrom und gibt Aggregatstatistiken zurück.

    Diese Funktion ist ein *terminal operator* der Pipeline: Sie konsumiert
    den kompletten Strom und gibt ein Dict zurück (kein Generator mehr).

    Args:
        transactions: Quell-Iterable von Transaction-Objekten.

    Returns:
        Dictionary mit drei Schlüsseln:

        * ``"counts"``      – ``{TransactionType: int}`` Anzahl pro Typ.
        * ``"totals"``      – ``{TransactionType: float}`` Summe der Beträge pro Typ.
        * ``"by_currency"`` – ``{str: float}`` Netto-Saldo pro Währungscode.

    Example::

        stats = summarize(parse_transactions(read_log_file("data/tx.log")))
        print(stats["by_currency"]["EUR"])
    """
    counts: dict[TransactionType, int] = defaultdict(int)
    totals: dict[TransactionType, float] = defaultdict(float)
    by_currency: dict[str, float] = defaultdict(float)

    for tx in transactions:
        counts[tx.type] += 1
        totals[tx.type] += tx.amount
        # Einzahlungen sind positiv, Abhebungen/Zahlungen negativ im Netto-Saldo
        sign = 1.0 if tx.type == TransactionType.DEPOSIT else -1.0
        by_currency[tx.currency] += sign * tx.amount

    return {
        "counts": dict(counts),
        "totals": dict(totals),
        "by_currency": dict(by_currency),
    }
