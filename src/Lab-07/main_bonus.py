def read_log_file(filename: str, filter_keyword: str = None):
    """
    Ein Generator, der eine Log-Datei Zeile für Zeile liest
    und optional filtert. Verwendet try...finally für
    sicheres Ressourcen-Management.
    """
    file_handle = None  # Wichtig für finally
    try:
        file_handle = open(filename, "r")
        print(f"\nLOG (Generator): Datei '{filename}' geöffnet.")

        for line in file_handle:
            line = line.strip()

            if filter_keyword is None:
                yield line  # Kein Filter, alles 'yielden'
            else:
                if filter_keyword.upper() in line.upper():
                    yield line  # Match gefunden, 'yielden'
                # else: (Zeile wird einfach ignoriert)

    except FileNotFoundError:
        print(f"FEHLER (Generator): Datei {filename} nicht gefunden.")

    finally:
        if file_handle:
            file_handle.close()
            print(f"LOG (Generator): Datei '{filename}' geschlossen.")


# --- Setup: Erstellen einer Dummy-Logdatei ---
log_filename = "test_tx_bonus.log"


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
        break  # Der Generator ist nicht erschöpft
# 'finally' wird trotzdem aufgerufen, wenn der Generator
# (log_gen_3) beim nächsten Garbage-Collection-Zyklus
# oder am Skript-Ende zerstört wird.
