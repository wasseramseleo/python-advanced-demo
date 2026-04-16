"""Speichereffiziente Transaktions-Log-Leser.

Zwei komplementäre Ansätze werden demonstriert:

``LazyTransactionReader``
    Klassenbasierter Iterator (``__iter__`` / ``__next__``): nützlich, wenn
    ein zustandsbehaftetes Objekt weitergegeben werden soll. Unterstützt auch
    das Context-Manager-Protokoll (``with``-Statement).

``read_log_file``
    Generator-Funktion: erreicht dasselbe mit deutlich weniger Code.
    Der ``try/finally``-Block garantiert, dass die Datei immer geschlossen
    wird – auch wenn der Aufrufer die Schleife vorzeitig mit ``break`` verlässt.

``parse_transactions``
    Generator, der rohe Log-Zeilen in ``Transaction``-Objekte umwandelt.
    Kombiniert mit ``read_log_file`` entsteht eine lazy Pipeline::

        transactions = parse_transactions(
            read_log_file("data/transactions_large.log")
        )

Alle drei Ansätze laden die Datei **nicht** vollständig in den Speicher –
sie sind daher für sehr große Log-Dateien geeignet.
"""

from collections.abc import Iterator

from .models import Transaction, parse_transaction_line


class LazyTransactionReader:
    """Zustandsbehafteter, klassenbasierter Iterator über eine Log-Datei.

    Die Datei wird beim Konstruktor geöffnet und via ``__next__`` zeilenweise
    gelesen. Datei-Handle wird bei Erschöpfung automatisch geschlossen.
    Alternativ: Context-Manager nutzen, um frühzeitig zu schließen.

    Args:
        filename: Pfad zur Transaktions-Log-Datei.
        filter_keyword: Falls gesetzt, werden nur Zeilen geliefert, die dieses
            Schlüsselwort enthalten (Groß-/Kleinschreibung ignoriert).

    Raises:
        FileNotFoundError: Wenn *filename* nicht existiert.

    Example::

        with LazyTransactionReader("data/transactions_large.log", "DEPOSIT") as r:
            for line in r:
                print(line)
    """

    def __init__(self, filename: str, filter_keyword: str | None = None) -> None:
        self.filename = filename
        self.filter_keyword = filter_keyword
        # open() wirft FileNotFoundError, falls die Datei fehlt – gewollt!
        self._file_handle = open(filename, "r", encoding="utf-8")

    # Context-Manager-Support für "with LazyTransactionReader(...) as r:"
    def __enter__(self) -> "LazyTransactionReader":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __iter__(self) -> "LazyTransactionReader":
        # Ein Iterator gibt sich selbst zurück – das ist das Protokoll
        return self

    def __next__(self) -> str:
        if self._file_handle is None:
            raise StopIteration

        while True:
            line = self._file_handle.readline()

            if not line:
                # Dateiende (EOF): leere Zeile wird von readline() zurückgegeben
                self.close()
                raise StopIteration

            line = line.strip()

            if not line:
                continue  # Leerzeilen überspringen, bevor Filter greift

            if self.filter_keyword is None or self.filter_keyword.upper() in line.upper():
                return line

    def close(self) -> None:
        """Schließt das Datei-Handle, falls noch offen."""
        if self._file_handle is not None:
            self._file_handle.close()
            # self._file_handle = None


def read_log_file(
    filename: str,
    filter_keyword: str | None = None,
) -> Iterator[str]:
    """Generator, der eine Transaktions-Log-Datei zeilenweise liest.

    Das ``try/finally``-Muster stellt sicher, dass die Datei *immer*
    geschlossen wird – selbst wenn der Aufrufer die Schleife mit ``break``
    abbricht oder eine Exception auftritt.

    Args:
        filename: Pfad zur Transaktions-Log-Datei.
        filter_keyword: Falls gesetzt, werden nur passende Zeilen geliefert
            (Groß-/Kleinschreibung ignoriert).

    Yields:
        Bereinigte (gestripte), nicht-leere Zeilen, die dem Filter entsprechen.

    Raises:
        FileNotFoundError: Wenn *filename* nicht existiert.

    Example::

        for line in read_log_file("data/transactions_large.log", "EUR"):
            print(line)
    """
    file_handle = None
    try:
        file_handle = open(filename, "r", encoding="utf-8")
        for line in file_handle:
            line = line.strip()

            if not line:
                continue  # Leerzeilen überspringen

            if filter_keyword is None or filter_keyword.upper() in line.upper():
                yield line
    finally:
        # Dieser Block läuft IMMER – auch bei break im Aufrufer oder Exception.
        # Das verhindert Resource-Leaks (unclosed file handles).
        if file_handle is not None:
            file_handle.close()


def parse_transactions(lines: Iterator[str]) -> Iterator[Transaction]:
    """Generator, der rohe Log-Zeilen in ``Transaction``-Objekte umwandelt.

    Kombiniert mit :func:`read_log_file` entsteht eine vollständig lazy Pipeline::

        txs = parse_transactions(read_log_file("data/transactions_large.log"))
        for tx in txs:
            print(tx)

    Args:
        lines: Ein Iterable von rohen Log-Datei-Zeilen.

    Yields:
        Geparste :class:`~ledger.models.Transaction`-Objekte.

    Note:
        Zeilen, die nicht geparst werden können, werden mit einer Warnung
        übersprungen statt eine Exception zu werfen. In einer Produktionsumgebung
        würde man hier das ``logging``-Modul statt ``print`` verwenden.
    """
    for line in lines:
        try:
            yield parse_transaction_line(line)
        except ValueError as exc:
            # Log-und-weiter: Eine fehlerhafte Zeile soll nicht die gesamte
            # Verarbeitung einer großen Datei abbrechen.
            print(f"WARNUNG: Überspringe fehlerhafte Zeile – {exc}")
