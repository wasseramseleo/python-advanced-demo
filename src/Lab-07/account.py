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
