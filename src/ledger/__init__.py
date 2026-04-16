"""ledger – Bankkonto-Hauptbuch als Python-Generator-Demo.

Dieses Paket demonstriert Python-Konzepte, die in der Vorlesung behandelt werden:

* **Generatoren** (``yield``) als elegante Alternative zu Iterator-Klassen
* **Iterator-Protokoll** (``__iter__`` / ``__next__``) vs. Iterables
* **Lazy Pipelines** – Komposition von Generatoren wie Unix-Pipes
* **Dataclasses** mit ``frozen=True`` für unveränderliche Domain-Objekte
* **Enums** mit String-Vererbung für robuste Typen

Öffentliche API
---------------
Die meistgenutzten Symbole werden hier für einfachen Import re-exportiert::

    from ledger import BankAccount, Transaction, TransactionType
    from ledger import read_log_file, parse_transactions
    from ledger import filter_by_type, filter_by_currency, summarize

Paketstruktur
-------------
::

    ledger/
    ├── __init__.py          ← Öffentliche API (diese Datei)
    ├── models.py            ← Transaction, TransactionType, parse_transaction_line
    ├── account.py           ← BankAccount, InsufficientFundsError
    ├── reader.py            ← LazyTransactionReader, read_log_file, parse_transactions
    ├── analytics.py         ← filter_by_type, filter_by_currency, running_total, summarize
    └── cli.py               ← Demo-Einstiegspunkt (uv run ledger)
"""

from .account import BankAccount, InsufficientFundsError
from .analytics import filter_by_currency, filter_by_type, running_total, summarize
from .models import Transaction, TransactionType, parse_transaction_line
from .reader import LazyTransactionReader, parse_transactions, read_log_file

__all__ = [
    # Domain-Modelle
    "Transaction",
    "TransactionType",
    "parse_transaction_line",
    # Konto
    "BankAccount",
    "InsufficientFundsError",
    # Datei-Reader
    "LazyTransactionReader",
    "read_log_file",
    "parse_transactions",
    # Analytics-Pipeline
    "filter_by_type",
    "filter_by_currency",
    "running_total",
    "summarize",
]
