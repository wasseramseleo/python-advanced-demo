from account import BankAccount

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
print(f"Manuelles next(): {next(tx_gen)}")
