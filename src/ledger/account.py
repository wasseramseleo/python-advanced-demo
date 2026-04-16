"""BankAccount – zentrales Domain-Modell für In-Memory-Konten.

Dieses Modul zeigt, wie das Iterator-Protokoll mit einer **Generator-Methode**
implementiert wird – eleganter und kürzer als eine separate Iterator-Klasse.

Schlüsselkonzept: ``__iter__`` gibt jedes Mal einen *neuen* Generator zurück.
Das erlaubt mehrfache Iteration über dasselbe Konto ohne geteilten Zustand.
"""

from collections.abc import Iterator

from .models import Transaction, TransactionType


class InsufficientFundsError(ValueError):
    """Wird ausgelöst, wenn eine Abhebung das verfügbare Guthaben übersteigen würde.

    Erbt von ``ValueError``, weil es sich um einen ungültigen Eingabe-Wert
    im Kontext des aktuellen Kontostands handelt.
    """


class BankAccount:
    """Ein Bankkonto mit generatorbasierter Transaktionshistorie.

    Transaktionen werden intern als unveränderliche ``Transaction``-Objekte
    gespeichert. Das Konto ist *iterable*: Eine ``for``-Schleife liefert alle
    Transaktionen in chronologischer Reihenfolge.

    Da ``__iter__`` jedes Mal einen frischen Generator erzeugt, kann dasselbe
    Konto beliebig oft iteriert werden – ganz ohne Zustandsprobleme::

        account = BankAccount("Erika Mustermann", "AT98765")
        account.deposit(1000.00)
        account.withdraw(200.00)

        for tx in account:          # Erste Iteration
            print(tx)

        totals = list(account)      # Zweite Iteration – funktioniert!

    Args:
        owner: Vollständiger Name des Kontoinhabers.
        account_number: Eindeutige Kontonummer als String.
    """

    def __init__(self, owner: str, account_number: str) -> None:
        self.owner = owner
        self.account_number = account_number
        # Privat: Externe Code sollte deposit/withdraw nutzen, nicht diese Liste direkt.
        self._transactions: list[Transaction] = []
        self._next_tx_id = 1

    # ------------------------------------------------------------------
    # Öffentliche Mutations-API
    # ------------------------------------------------------------------

    def deposit(self, amount: float, currency: str = "EUR") -> Transaction:
        """Bucht eine Einzahlung auf dieses Konto.

        Args:
            amount: Positiver Betrag der Einzahlung.
            currency: ISO-4217-Währungscode. Standard: ``"EUR"``.

        Returns:
            Das erstellte ``Transaction``-Objekt.

        Raises:
            ValueError: Wenn *amount* nicht positiv ist.
        """
        if amount <= 0:
            raise ValueError(f"Einzahlungsbetrag muss positiv sein, erhalten: {amount}")
        tx = Transaction(
            id=self._generate_id(),
            type=TransactionType.DEPOSIT,
            amount=amount,
            currency=currency,
        )
        self._transactions.append(tx)
        return tx

    def withdraw(self, amount: float, currency: str = "EUR") -> Transaction:
        """Bucht eine Abhebung von diesem Konto.

        Args:
            amount: Positiver Betrag der Abhebung.
            currency: ISO-4217-Währungscode. Standard: ``"EUR"``.

        Returns:
            Das erstellte ``Transaction``-Objekt.

        Raises:
            ValueError: Wenn *amount* nicht positiv ist.
            InsufficientFundsError: Wenn das Guthaben für die Abhebung
                in dieser Währung nicht ausreicht.
        """
        if amount <= 0:
            raise ValueError(f"Abhebungsbetrag muss positiv sein, erhalten: {amount}")

        # Einfache Deckungsprüfung – nur für gleichwähriges Guthaben
        current_balance = self._balance_for(currency)
        if amount > current_balance:
            raise InsufficientFundsError(
                f"Kann {amount:.2f} {currency} nicht abheben: "
                f"Guthaben beträgt nur {current_balance:.2f} {currency}"
            )
        tx = Transaction(
            id=self._generate_id(),
            type=TransactionType.WITHDRAW,
            amount=amount,
            currency=currency,
        )
        self._transactions.append(tx)
        return tx

    # ------------------------------------------------------------------
    # Nur-Lese-Properties
    # ------------------------------------------------------------------

    @property
    def balance(self) -> float:
        """Netto-Guthaben über alle EUR-Transaktionen (Einzahlungen minus Abhebungen).

        Note:
            Für Multi-Währungs-Konten empfiehlt sich :func:`ledger.analytics.summarize`,
            das Salden pro Währung aufschlüsselt.
        """
        return self._balance_for("EUR")

    # ------------------------------------------------------------------
    # Iterator-Protokoll
    # ------------------------------------------------------------------

    def get_transaction_history(self) -> Iterator[Transaction]:
        """Generator, der alle Transaktionen einzeln liefert.

        Das ``yield``-Schlüsselwort verwandelt diese Methode in eine
        Generator-Funktion. Jeder Aufruf erstellt ein *neues* Generator-Objekt
        mit eigenem Zustand – Iterationen stören sich gegenseitig nicht.

        Yields:
            ``Transaction``-Objekte in chronologischer Reihenfolge.
        """
        # yield pausiert die Funktion und gibt den Wert an den Aufrufer.
        # Beim nächsten next()-Aufruf läuft sie genau hier weiter.
        for tx in self._transactions:
            yield tx

    def __iter__(self) -> Iterator[Transaction]:
        """Gibt einen Generator über alle Transaktionen zurück.

        Macht ``BankAccount`` zu einem *Iterable* – der Unterschied zu einem
        *Iterator* ist wichtig: Dieses Objekt kann mehrfach iteriert werden,
        weil ``__iter__`` jedes Mal einen frischen Generator erzeugt.
        """
        return self.get_transaction_history()

    def __repr__(self) -> str:
        return (
            f"BankAccount(owner={self.owner!r}, "
            f"account_number={self.account_number!r}, "
            f"transactions={len(self._transactions)})"
        )

    # ------------------------------------------------------------------
    # Private Hilfsmethoden
    # ------------------------------------------------------------------

    def _generate_id(self) -> str:
        """Erzeugt eine fortlaufende, interne Transaktions-ID."""
        tx_id = f"A{self._next_tx_id:04d}"
        self._next_tx_id += 1
        return tx_id

    def _balance_for(self, currency: str) -> float:
        """Berechnet den Netto-Saldo für eine einzelne Währung."""
        total = 0.0
        for tx in self._transactions:
            if tx.currency != currency:
                continue  # Andere Währungen überspringen
            if tx.type == TransactionType.DEPOSIT:
                total += tx.amount
            else:
                # WITHDRAW und PAYMENT reduzieren beide den Saldo
                total -= tx.amount
        return total
