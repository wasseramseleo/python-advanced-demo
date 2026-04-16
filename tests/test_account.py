"""Tests für ledger.account – BankAccount-Klasse."""

import types

import pytest

from ledger.account import BankAccount, InsufficientFundsError
from ledger.models import TransactionType


@pytest.fixture
def funded_account() -> BankAccount:
    """BankAccount mit vorgeladenen Transaktionen für Wiederverwendung in Tests."""
    acc = BankAccount("Test User", "TEST001")
    acc.deposit(1_000.00)
    acc.deposit(500.00)
    acc.withdraw(200.00)
    return acc


class TestDeposit:
    def test_increases_balance(self):
        acc = BankAccount("Jane", "X001")
        acc.deposit(500.00)
        assert acc.balance == pytest.approx(500.00)

    def test_multiple_deposits_accumulate(self):
        acc = BankAccount("Jane", "X001")
        acc.deposit(100.00)
        acc.deposit(200.00)
        assert acc.balance == pytest.approx(300.00)

    def test_returns_transaction_object(self):
        acc = BankAccount("Jane", "X001")
        tx = acc.deposit(100.00)
        assert tx.type == TransactionType.DEPOSIT
        assert tx.amount == pytest.approx(100.00)
        assert tx.currency == "EUR"

    def test_custom_currency(self):
        acc = BankAccount("Jane", "X001")
        tx = acc.deposit(500.00, currency="USD")
        assert tx.currency == "USD"

    def test_zero_amount_raises(self):
        acc = BankAccount("Jane", "X001")
        with pytest.raises(ValueError, match="positiv"):
            acc.deposit(0)

    def test_negative_amount_raises(self):
        acc = BankAccount("Jane", "X001")
        with pytest.raises(ValueError, match="positiv"):
            acc.deposit(-50)


class TestWithdraw:
    def test_decreases_balance(self, funded_account: BankAccount):
        before = funded_account.balance
        funded_account.withdraw(100.00)
        assert funded_account.balance == pytest.approx(before - 100.00)

    def test_returns_transaction_object(self, funded_account: BankAccount):
        tx = funded_account.withdraw(50.00)
        assert tx.type == TransactionType.WITHDRAW
        assert tx.amount == pytest.approx(50.00)

    def test_exact_balance_withdraw(self):
        acc = BankAccount("Jane", "X001")
        acc.deposit(100.00)
        tx = acc.withdraw(100.00)
        assert tx.type == TransactionType.WITHDRAW
        assert acc.balance == pytest.approx(0.00)

    def test_insufficient_funds_raises(self):
        acc = BankAccount("Jane", "X001")
        acc.deposit(100.00)
        with pytest.raises(InsufficientFundsError):
            acc.withdraw(200.00)

    def test_zero_amount_raises(self, funded_account: BankAccount):
        with pytest.raises(ValueError, match="positiv"):
            funded_account.withdraw(0)

    def test_negative_amount_raises(self, funded_account: BankAccount):
        with pytest.raises(ValueError):
            funded_account.withdraw(-10)


class TestBalance:
    def test_empty_account_balance_is_zero(self):
        acc = BankAccount("Empty", "E001")
        assert acc.balance == pytest.approx(0.00)

    def test_balance_reflects_all_transactions(self, funded_account: BankAccount):
        # 1000 + 500 - 200 = 1300
        assert funded_account.balance == pytest.approx(1_300.00)

    def test_balance_only_counts_eur(self):
        """Fremdwährungs-Transaktionen fließen nicht in den EUR-Saldo ein."""
        acc = BankAccount("Multi", "M001")
        acc.deposit(1_000.00, "EUR")
        acc.deposit(500.00, "USD")  # soll den EUR-Saldo nicht beeinflussen
        assert acc.balance == pytest.approx(1_000.00)


class TestIteration:
    def test_yields_all_transactions(self, funded_account: BankAccount):
        transactions = list(funded_account)
        assert len(transactions) == 3

    def test_repeatable_iteration(self, funded_account: BankAccount):
        """__iter__ erzeugt jedes Mal einen neuen Generator → kein geteilter Zustand."""
        first = list(funded_account)
        second = list(funded_account)
        assert first == second

    def test_chronological_order(self, funded_account: BankAccount):
        types = [tx.type for tx in funded_account]
        assert types == [
            TransactionType.DEPOSIT,
            TransactionType.DEPOSIT,
            TransactionType.WITHDRAW,
        ]

    def test_empty_account_yields_nothing(self):
        acc = BankAccount("Empty", "E001")
        assert list(acc) == []

    def test_get_transaction_history_is_generator(self, funded_account: BankAccount):
        """get_transaction_history() muss ein echter Generator sein, kein Iterator."""
        gen = funded_account.get_transaction_history()
        assert isinstance(gen, types.GeneratorType)

    def test_two_generators_are_independent(self, funded_account: BankAccount):
        """Zwei gleichzeitige Iterationen beeinflussen sich nicht gegenseitig."""
        gen1 = funded_account.get_transaction_history()
        gen2 = funded_account.get_transaction_history()
        first_of_gen1 = next(gen1)
        first_of_gen2 = next(gen2)
        assert first_of_gen1 == first_of_gen2  # beide starten vom Anfang
