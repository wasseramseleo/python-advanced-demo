"""Domain-Modelle für das ledger-Paket.

Dieses Modul definiert die zentralen Datenstrukturen der Anwendung.
Es hat **keine** Abhängigkeiten zu anderen Modulen im Paket – es steht
an der untersten Ebene der Abhängigkeitshierarchie.

Designentscheidungen
--------------------
* ``Transaction`` ist ein *frozen* Dataclass: Transaktionen sind nach ihrer
  Erstellung unveränderlich, so wie echte Buchungseinträge im Hauptbuch.
* ``TransactionType`` erbt von ``str``, damit Enum-Werte direkt als Strings
  serialisiert werden können (z. B. in JSON) – ohne extra Konvertierung.

Docstrings vs. Kommentare – Faustregel in diesem Projekt
---------------------------------------------------------
* **Docstrings** (triple-quote) dokumentieren das **Was** und **Warum** für
  Klassen, Funktionen und Module – sie sind für Nutzer des Codes gedacht.
* **Inline-Kommentare** (#) erklären nicht-offensichtliche Implementierungs-
  details oder Fallstricke – sie sind für Entwickler gedacht, die den Code
  ändern.
"""

from dataclasses import dataclass
from enum import Enum


class TransactionType(str, Enum):
    """Unterstützte Transaktionstypen.

    Da ``TransactionType`` von ``str`` erbt, gilt z. B.::

        TransactionType.DEPOSIT == "DEPOSIT"  # True

    Das vereinfacht Logging, Serialisierung und Log-Datei-Parsing erheblich.
    """

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    PAYMENT = "PAYMENT"


@dataclass(frozen=True)
class Transaction:
    """Ein unveränderlicher Datensatz für eine einzelne Finanztransaktion.

    Attributes:
        id: Eindeutiger Transaktionsbezeichner (z. B. ``"T1000"``).
        type: Art der Transaktion (Einzahlung, Abhebung, Zahlung).
        amount: Betrag – immer positiv, die Richtung ergibt sich aus ``type``.
        currency: ISO-4217-Währungscode (z. B. ``"EUR"``, ``"USD"``).

    Example::

        tx = Transaction(id="T1", type=TransactionType.DEPOSIT,
                         amount=100.0, currency="EUR")
        print(tx)  # [T1] DEPOSIT      +    100.00 EUR
    """

    id: str
    type: TransactionType
    amount: float
    currency: str

    def __str__(self) -> str:
        # Vorzeichen visualisiert die Richtung: + für Einzahlungen, - für alles andere
        sign = "+" if self.type == TransactionType.DEPOSIT else "-"
        return f"[{self.id}] {self.type.value:<8} {sign}{self.amount:>10.2f} {self.currency}"


def parse_transaction_line(line: str) -> Transaction:
    """Parst eine einzelne Log-Datei-Zeile in ein Transaction-Objekt.

    Erwartetes Format (pipe-separiert, key-value mit Doppelpunkt)::

        ID: T1000 | TYPE: WITHDRAW | AMOUNT: 6657.49 | CURRENCY: USD

    Args:
        line: Eine einzelne, nicht-leere Zeile aus einer Transaktions-Log-Datei.

    Returns:
        Ein befülltes ``Transaction``-Objekt.

    Raises:
        ValueError: Wenn die Zeile nicht geparst werden kann oder unbekannte
            Felder enthält.
    """
    try:
        # Dict-Comprehension: jedes "|"-Segment in ein key-value-Paar aufteilen
        fields = {
            key.strip(): value.strip()
            for part in line.split("|")
            for key, value in [part.split(":", 1)]
        }
        return Transaction(
            id=fields["ID"],
            type=TransactionType(fields["TYPE"]),  # ValueError bei unbekanntem Typ
            amount=float(fields["AMOUNT"]),
            currency=fields["CURRENCY"],
        )
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Zeile kann nicht geparst werden: {line!r}") from exc
