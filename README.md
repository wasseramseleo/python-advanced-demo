# PythonAdvancedUVDemo – `ledger`

Ein Banking-Hauptbuch als Demo-Projekt für:

* **Python-Generatoren** und das Iterator-Protokoll
* **`uv`** als modernes Projekt- und Dependency-Management-Tool
* **Best Practices** in Projektstruktur, Docstrings und Tests

---

## Schnellstart

```bash
# Umgebung einrichten und Paket installieren
uv sync --group dev

# Demo ausführen
uv run ledger

# Tests ausführen
uv run pytest

# Tests mit Coverage
uv run pytest --cov=ledger --cov-report=term-missing
```

---

## Projektstruktur

```
PythonAdvancedUVDemo/
│
├── pyproject.toml          ← Projektmetadaten, Dependencies, Tool-Konfiguration
├── uv.lock                 ← Exakt reproduzierbares Dependency-Abbild
│
├── src/
│   └── ledger/             ← Installierbares Python-Paket (src-Layout)
│       ├── __init__.py     ← Öffentliche API – hier wird re-exportiert
│       ├── models.py       ← Transaction-Dataclass, TransactionType-Enum
│       ├── account.py      ← BankAccount mit generatorbasierter Iteration
│       ├── reader.py       ← Lazy Log-Datei-Leser (2 Implementierungen)
│       ├── analytics.py    ← Komposierbare Generator-Pipeline
│       ├── cli.py          ← Demo-Einstiegspunkt (uv run ledger)
│       └── __main__.py     ← Erlaubt: python -m ledger
│
├── tests/
│   ├── conftest.py         ← Gemeinsame pytest-Fixtures
│   ├── test_models.py
│   ├── test_account.py
│   ├── test_reader.py
│   └── test_analytics.py
│
└── data/
    └── transactions_large.log  ← 100.000 Beispiel-Transaktionen
```

### Warum `src`-Layout?

Das `src`-Layout verhindert, dass Python das Paket aus dem Arbeitsverzeichnis
importiert statt aus der installierten Version. Dadurch testen Tests immer die
*installierte* Variante – und decken Paketierungsfehler frühzeitig auf.

---

## Modulübersicht

### `models.py` – Domain-Modelle

```python
from ledger import Transaction, TransactionType, parse_transaction_line

tx = parse_transaction_line("ID: T1 | TYPE: DEPOSIT | AMOUNT: 100.00 | CURRENCY: EUR")
print(tx)  # [T1] DEPOSIT      +    100.00 EUR
```

### `account.py` – BankAccount

```python
from ledger import BankAccount

account = BankAccount("Erika Mustermann", "AT98765")
account.deposit(1000.00)
account.withdraw(200.00)
print(account.balance)          # 800.00

for tx in account:              # Iterable dank __iter__ + Generator
    print(tx)

for tx in account:              # Zweite Iteration: funktioniert!
    print(tx)
```

### `reader.py` – Lazy Log-Leser

Zwei Implementierungen für denselben Zweck – klassischer Iterator vs. Generator:

```python
from ledger import read_log_file, parse_transactions

# Generator-Funktion (empfohlen – weniger Code, try/finally garantiert Schließen)
for line in read_log_file("data/transactions_large.log", filter_keyword="DEPOSIT"):
    print(line)

# Lazy Pipeline: Lesen + Parsen ohne die Datei in den Speicher zu laden
transactions = parse_transactions(read_log_file("data/transactions_large.log"))
```

### `analytics.py` – Generator-Pipeline

```python
from ledger import (
    read_log_file, parse_transactions,
    filter_by_currency, filter_by_type, summarize
)
from ledger import TransactionType

# Komposierbare Pipeline – kein Schritt lädt alles in den Speicher
stats = summarize(
    filter_by_type(
        filter_by_currency(
            parse_transactions(read_log_file("data/transactions_large.log")),
            "EUR"
        ),
        TransactionType.DEPOSIT
    )
)
print(stats["by_currency"])
```

---

## Docstrings vs. Inline-Kommentare

Dieses Projekt folgt einer klaren Konvention:

| Typ | Format | Zweck | Publikum |
|---|---|---|---|
| **Docstring** | `"""..."""` | Was tut diese Funktion/Klasse? Warum existiert sie? | Nutzer des Codes |
| **Inline-Kommentar** | `# ...` | Nicht-offensichtliche Implementierungsdetails | Entwickler, die den Code ändern |

**Faustregel:** Wenn `help(funktion)` es zeigen soll → Docstring. Wenn es erklärt, *warum* der Code so geschrieben ist → Kommentar.

---

## `uv`-Workflow-Cheatsheet

```bash
uv sync                    # Umgebung aus uv.lock reproduzieren
uv sync --group dev        # inkl. Entwicklungsabhängigkeiten (pytest)
uv add requests            # Neue Abhängigkeit hinzufügen + uv.lock aktualisieren
uv run pytest              # Tests in der verwalteten Umgebung ausführen
uv run pytest --cov=ledger # Mit Coverage-Report
uv build                   # Distributionspaket bauen (.whl + .tar.gz)
```
