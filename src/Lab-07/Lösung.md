# Lab 7: Generatoren - Lösung

## Erläuterung der Lösung

### Basis-Aufgabe

Die Lösung demonstriert die Eleganz von Generatoren als Ersatz für Iterator-Klassen.

1.  **`get_transaction_history(self)`**: Dies ist eine Generator-Funktion, erkennbar am `yield`-Schlüsselwort. Statt eine Liste zu erstellen und zurückzugeben, "pausiert" die Funktion bei jedem `yield` und liefert einen Wert zurück.
2.  **Zustandsverwaltung**: Der Generator "merkt" sich automatisch, wo er in der `for tx in self.__transactions:`-Schleife war. Wir müssen keinen `self._index` manuell verwalten.
3.  **`__iter__`**: Diese Methode wird aufgerufen, wenn Python ein Iterable benötigt (z.B. `for tx in account:`). Wir rufen einfach `self.get_transaction_history()` auf. Dieser Aufruf führt die Generator-Funktion *nicht* aus, sondern gibt sofort ein **Generator-Objekt** zurück.
4.  **Iterator-Protokoll**: Dieses Generator-Objekt implementiert automatisch `__iter__` (gibt sich selbst zurück) und `__next__` (setzt die Funktion bis zum nächsten `yield` fort). Es löst auch automatisch `StopIteration` aus, wenn die Funktion endet.

Der gesamte Boilerplate-Code der `AccountHistoryIterator`-Klasse (ca. 10-15 Zeilen) aus Lab 5 wird durch diese 3-zeilige Generator-Methode ersetzt.

### Bonus-Herausforderung

Die Generator-Funktion `read_log_file` ist der "pythonische" Weg, um Dateien "lazy" zu verarbeiten.

1.  **`yield` statt `return`**: Die Funktion lädt nie die ganze Datei. Sie liest eine Zeile, `yield`et sie und pausiert. Erst beim nächsten `next()`-Aufruf (durch die `for`-Schleife des Aufrufers) liest sie die nächste Zeile.
2.  **`try...finally`**: Dies ist ein kritisches Muster für Generatoren, die externe Ressourcen (wie Dateien oder Netzwerk-Sockets) verwalten. Der `finally`-Block wird garantiert ausgeführt, wenn der Generator "erschöpft" ist (d.h. `StopIteration` auslöst) oder wenn er extern zerstört wird (z.B. durch `del` oder wenn die `for`-Schleife, die ihn nutzt, mit `break` verlassen wird). Dies verhindert "Resource Leaks".
3.  **Alternative (noch besser)**: In modernem Python würde man `with open(...) as file_handle:` direkt verwenden, da der `with`-Kontext dasselbe Ressourcen-Management bietet. Die `try...finally`-Lösung zeigt jedoch expliziter, wie Generatoren Ressourcen verwalten. (Der Code unten zeigt die `try...finally`-Variante, wie in der Angabe gefordert).

## Python-Code: Basis-Aufgabe

```python
class BankAccount:
    """
    Stellt ein Bankkonto dar, das (intern) eine Liste von Transaktionen hält.
    Diese Version verwendet einen Generator für die Iteration.
    """
    def __init__(self, owner: str, account_number: str):
        self.owner = owner
        self.account_number = account_number
        self.__transactions = [] 

    def deposit(self, amount: float):
        self.__transactions.append(f"DEPOSIT: {amount} EUR")

    def withdraw(self, amount: float):
        self.__transactions.append(f"WITHDRAW: {amount} EUR")

    def get_transaction_history(self):
        """
        Dies ist eine Generator-Funktion.
        Sie 'yieldet' Transaktionen einzeln, anstatt eine Liste zurückzugeben.
        """
        print("\nLOG: get_transaction_history (Generator) gestartet.")
        for tx in self.__transactions:
            print("LOG: Generator 'yieldet' eine Transaktion.")
            yield tx
        print("LOG: Generator ist am Ende.")

    def __iter__(self):
        """ 
        Gibt das Generator-Objekt zurück.
        Dies macht BankAccount "iterable".
        """
        print("LOG: BankAccount.__iter__ aufgerufen.")
        # Ruft die Generator-Funktion auf, was ein Generator-Objekt zurückgibt
        return self.get_transaction_history()
            

# --- Beispiel-Nutzung (Angabe) ---
print("--- Angabe Test ---")
my_account = BankAccount("Erika Mustermann", "AT98765")
my_account.deposit(500)
my_account.withdraw(100)
my_account.deposit(50)

print(f"Beginne Iteration über Konto: {my_account.owner}")

# 1. Nutzung in einer for-Schleife
# Dies ruft __iter__() auf, erhält den Generator und ruft
# implizit next() darauf auf, bis StopIteration kommt.
for tx in my_account:
    print(f"  -> Transaktion: {tx}")

print("\nZweite Iteration (erzeugt neuen Generator):")
# 2. Eine for-Schleife kann mehrmals verwendet werden, da __iter__
# jedes Mal einen NEUEN Generator erstellt.
for tx in my_account:
    print(f"  -> Zweiter Durchgang: {tx}")


# 3. Manuelle Prüfung des Typs
tx_gen = my_account.__iter__()
print(f"\nTyp des Iterators: {type(tx_gen)}")
print(f"Manuelles next(): {next(tx_gen)}")
```

## Python-Code: Bonus-Herausforderung

```python
import os

def read_log_file(filename: str, filter_keyword: str = None):
    """
    Ein Generator, der eine Log-Datei Zeile für Zeile liest
    und optional filtert. Verwendet try...finally für 
    sicheres Ressourcen-Management.
    """
    file_handle = None # Wichtig für finally
    try:
        file_handle = open(filename, 'r')
        print(f"\nLOG (Generator): Datei '{filename}' geöffnet.")
        
        for line in file_handle:
            line = line.strip()
            
            if filter_keyword is None:
                yield line # Kein Filter, alles 'yielden'
            else:
                if filter_keyword.upper() in line.upper():
                    yield line # Match gefunden, 'yielden'
                # else: (Zeile wird einfach ignoriert)

    except FileNotFoundError:
        print(f"FEHLER (Generator): Datei {filename} nicht gefunden.")
    
    finally:
        if file_handle:
            file_handle.close()
            print(f"LOG (Generator): Datei '{filename}' geschlossen.")

# --- Setup: Erstellen einer Dummy-Logdatei ---
log_filename = "test_tx_bonus.log"
dummy_data = """
DEPOSIT: 1000.50
WITHDRAW: 50.00
WITHDRAW: 120.25
DEPOSIT: 300.00
SYSTEM:FEE: 5.00
WITHDRAW: 80.00
"""
try:
    with open(log_filename, "w") as f:
        f.write(dummy_data.strip())
except IOError as e:
    print(f"Setup fehlgeschlagen: {e}")

# --- Beispiel-Nutzung (Bonus) ---
print("\n--- Bonus-Herausforderung Test 1 (alle Transaktionen) ---")

# 1. Alle Transaktionen lesen
log_gen_1 = read_log_file(log_filename)
for line in log_gen_1:
    print(f"  Gelesene Zeile: {line}")
# Am Ende dieser Schleife (StopIteration) wird 'finally' ausgeführt.

print("\n--- Bonus-Herausforderung Test 2 (nur 'WITHDRAW') ---")
# 2. Nur Abhebungen filtern
log_gen_2 = read_log_file(log_filename, filter_keyword="WITHDRAW")
for line in log_gen_2:
    print(f"  Gefilterte Zeile: {line}")


print("\n--- Bonus-Herausforderung Test 3 (Abbruch-Test) ---")
# 3. Test mit 'break' (zeigt, dass 'finally' trotzdem läuft)
log_gen_3 = read_log_file(log_filename)
for line in log_gen_3:
    print(f"  Gelesene Zeile: {line}")
    if "120.25" in line:
        print("  -> TEST: Breche Schleife vorzeitig ab...")
        break # Der Generator ist nicht erschöpft
# 'finally' wird trotzdem aufgerufen, wenn der Generator
# (log_gen_3) beim nächsten Garbage-Collection-Zyklus 
# oder am Skript-Ende zerstört wird.

# Aufräumen
if os.path.exists(log_filename):
    os.remove(log_filename)
```