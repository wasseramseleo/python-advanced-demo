# Lab 7: Generatoren

## Lernziele

In diesem Lab ersetzen Sie die komplexen Iterator-Klassen aus dem vorherigen Lab durch elegante und speichereffiziente Generator-Funktionen.

  * Das `yield`-Schlüsselwort verstehen und anwenden.
  * Eine Funktion in eine Generator-Funktion umwandeln.
  * Verstehen, wie ein Generator automatisch das Iterator-Protokoll implementiert.
  * Den "Pause & Resume"-Mechanismus von `yield` nutzen.
  * Generatoren für speichereffiziente Datenströme (z.B. Dateiverarbeitung) einsetzen.

## Szenario

In Lab 5 haben wir eine separate `AccountHistoryIterator`-Klasse erstellt, um die `BankAccount`-Klasse "iterable" zu machen. 
Dies erforderte die manuelle Implementierung von `__init__`, `__iter__` und `__next__` sowie die Verwaltung eines internen Zustands (z.B. `self._index`).

Dieser Ansatz ist "Boilerplate"-Code. Das `yield`-Schlüsselwort in Python erlaubt es uns, das *exakt gleiche* Ergebnis mit einer einzigen, viel einfacheren Funktion zu erzielen. 
Ihre Aufgabe ist es, die `BankAccount`-Klasse auf die Verwendung von Generatoren umzustellen (Refactoring).

### Angabe

**Ziel:** Ersetzen Sie die Logik des `AccountHistoryIterator` (Lab 5) durch eine Generator-Funktion.

1.  **Vorbereitung:** Wir gehen erneut von der vereinfachten `BankAccount`-Klasse aus (siehe Kopiervorlage unten).

    ```python
    class BankAccount:
        """
        Stellt ein Bankkonto dar, das (intern) eine Liste von Transaktionen hält.
        """
        def __init__(self, owner: str, account_number: str):
            self.owner = owner
            self.account_number = account_number
            # Hält den Verlauf.
            self.__transactions = [] 

        def deposit(self, amount: float):
            """Fügt eine Einzahlung als Transaktion hinzu."""
            self.__transactions.append(f"DEPOSIT: {amount} EUR")

        def withdraw(self, amount: float):
            """Fügt eine Abhebung als Transaktion hinzu."""
            self.__transactions.append(f"WITHDRAW: {amount} EUR")

        # HIER SOLL __iter__ AKTUALISIERT WERDEN
        def __iter__(self):
            """ 
            Sollte einen Generator zurückgeben, anstatt eine
            separate Iterator-Klasse zu instanziieren.
            """
            # TODO: Implementierung fehlt
            pass 
            
    ```

2.  **Generator-Funktion implementieren:**

      * Fügen Sie *innerhalb* der `BankAccount`-Klasse eine neue Methode hinzu (z.B. `get_transaction_history(self)`).
      * Diese Methode soll eine einfache `for`-Schleife über `self.__transactions` implementieren.
      * Anstatt eine Liste zurückzugeben, soll die Methode das `yield`-Schlüsselwort verwenden, um *jede einzelne Transaktion* "zurückzugeben".

3.  **`__iter__` aktualisieren:**

      * Passen Sie die `__iter__`-Methode der `BankAccount`-Klasse an.
      * `__iter__` soll jetzt lediglich Ihre neue Generator-Methode (`get_transaction_history`) aufrufen und deren Ergebnis (das Generator-Objekt) zurückgeben.
      * `def __iter__(self): return self.get_transaction_history()`

4.  **Testen:**

      * Erstellen Sie ein `BankAccount`, fügen Sie Transaktionen hinzu und testen Sie, ob die `for`-Schleife (`for tx in my_account:`) weiterhin wie in Lab 5 funktioniert.
      * Prüfen Sie (z.B. mit `print(my_account.__iter__())`), dass der Aufruf von `__iter__` nun ein `generator object` zurückgibt.

-----

### Bonus-Herausforderung

**Ziel:** Gestalten Sie die *Bonus-Aufgabe* aus Lab 5 (den `LazyTransactionReader` zum Lesen von Log-Dateien) in eine Generator-Funktion um.

1.  **Szenario:** Wir benötigen eine Funktion, die eine (potenziell riesige) Transaktions-Logdatei Zeile für Zeile liest und optional filtert, ohne die gesamte Datei in den Speicher zu laden.

2.  **Generator-Funktion `read_log_file`:**

      * Erstellen Sie eine *eigenständige* Generator-Funktion (nicht Teil einer Klasse) namens `read_log_file(filename: str, filter_keyword: str = None)`.
      * Die Funktion soll die Datei (mit `open()`) öffnen.
      * **WICHTIG:** Verwenden Sie einen `try...finally`-Block. Das `open()` sollte im `try` stehen und das `file.close()` im `finally` Block. Dies stellt sicher, dass die Datei *immer* geschlossen wird, selbst wenn der Generator vorzeitig beendet wird (z.B. durch ein `break` in der `for`-Schleife des Aufrufers).
      * Innerhalb des `try`-Blocks: Iterieren Sie Zeile für Zeile über die Datei (`for line in file_handle:`).
      * Führen Sie die Filterlogik durch: Wenn ein `filter_keyword` gesetzt ist und *nicht* in der Zeile (ignoriere Groß/Kleinschreibung) vorkommt, überspringen Sie die Zeile.
      * Wenn die Zeile passt (oder kein Filter gesetzt ist), `yield`en Sie die bereinigte Zeile (z.B. mit `.strip()`).

3.  **Test:** Erstellen Sie (wie in Lab 5) eine Dummy-Datei `test_tx.log` und testen Sie Ihre `read_log_file`-Funktion mit und ohne `filter_keyword`.
