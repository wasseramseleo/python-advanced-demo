class LazyTransactionReader:
    """
    Ein speichereffizienter Iterator, der eine große Transaktionsdatei
    Zeile für Zeile liest und optional filtert.
    """

    def __init__(self, filename: str, filter_keyword: str = None):
        print(f"LOG: LazyTransactionReader: Öffne Datei '{filename}'")
        self.filename = filename
        self.filter_keyword = filter_keyword
        try:
            self._file_handle = open(filename, "r")
        except FileNotFoundError:
            print(f"FEHLER: Datei {filename} nicht gefunden.")
            self._file_handle = None
            raise

    def __iter__(self):
        return self

    def __next__(self):
        if self._file_handle is None:
            raise StopIteration  # Bereits geschlossen oder Fehler

        while True:  # Intern loopen, bis wir ein Match finden oder die Datei endet
            line = self._file_handle.readline()

            if not line:
                # Ende der Datei (EOF)
                print("LOG: LazyTransactionReader: Dateiende erreicht.")
                self.close()  # Ressource freigeben
                raise StopIteration

            line = line.strip()  # \n entfernen

            # Filter-Logik
            if self.filter_keyword is None:
                return line  # Kein Filter, jede Zeile zurückgeben

            if self.filter_keyword.upper() in line.upper():
                return line  # Match gefunden!

    def close(self):
        """Schließt das Dateihandle, falls offen."""
        if self._file_handle:
            print(f"LOG: LazyTransactionReader: Schließe Datei '{self.filename}'")
            self._file_handle.close()
            self._file_handle = None
