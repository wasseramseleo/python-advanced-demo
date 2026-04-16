"""Tests für ledger.analytics – Generator-basierte Analytics-Pipeline."""

import pytest

from ledger.analytics import filter_by_currency, filter_by_type, running_total, summarize
from ledger.models import Transaction, TransactionType


@pytest.fixture
def mixed_transactions() -> list[Transaction]:
    """Fixture mit verschiedenen Typen und Währungen für Pipeline-Tests."""
    return [
        Transaction("T1", TransactionType.DEPOSIT,  1_000.0, "EUR"),
        Transaction("T2", TransactionType.WITHDRAW,   200.0, "EUR"),
        Transaction("T3", TransactionType.DEPOSIT,    500.0, "USD"),
        Transaction("T4", TransactionType.PAYMENT,     50.0, "EUR"),
        Transaction("T5", TransactionType.DEPOSIT,    300.0, "EUR"),
    ]


class TestFilterByType:
    def test_filters_deposits(self, mixed_transactions: list[Transaction]):
        result = list(filter_by_type(mixed_transactions, TransactionType.DEPOSIT))
        assert len(result) == 3
        assert all(tx.type == TransactionType.DEPOSIT for tx in result)

    def test_filters_withdrawals(self, mixed_transactions: list[Transaction]):
        result = list(filter_by_type(mixed_transactions, TransactionType.WITHDRAW))
        assert len(result) == 1
        assert result[0].id == "T2"

    def test_filters_payments(self, mixed_transactions: list[Transaction]):
        result = list(filter_by_type(mixed_transactions, TransactionType.PAYMENT))
        assert len(result) == 1

    def test_empty_source_returns_empty(self):
        result = list(filter_by_type([], TransactionType.DEPOSIT))
        assert result == []

    def test_returns_generator(self, mixed_transactions: list[Transaction]):
        """filter_by_type ist lazy – gibt einen Generator zurück."""
        import types
        result = filter_by_type(mixed_transactions, TransactionType.DEPOSIT)
        assert isinstance(result, types.GeneratorType)


class TestFilterByCurrency:
    def test_filters_eur(self, mixed_transactions: list[Transaction]):
        result = list(filter_by_currency(mixed_transactions, "EUR"))
        assert len(result) == 4
        assert all(tx.currency == "EUR" for tx in result)

    def test_filters_usd(self, mixed_transactions: list[Transaction]):
        result = list(filter_by_currency(mixed_transactions, "USD"))
        assert len(result) == 1
        assert result[0].id == "T3"

    def test_case_insensitive(self, mixed_transactions: list[Transaction]):
        lower = list(filter_by_currency(mixed_transactions, "eur"))
        upper = list(filter_by_currency(mixed_transactions, "EUR"))
        assert lower == upper

    def test_no_matching_currency(self, mixed_transactions: list[Transaction]):
        result = list(filter_by_currency(mixed_transactions, "GBP"))
        assert result == []

    def test_empty_source_returns_empty(self):
        assert list(filter_by_currency([], "EUR")) == []


class TestRunningTotal:
    def test_deposits_increase_balance(self):
        txs = [
            Transaction("T1", TransactionType.DEPOSIT, 100.0, "EUR"),
            Transaction("T2", TransactionType.DEPOSIT, 200.0, "EUR"),
        ]
        results = list(running_total(txs))
        assert results[0][1] == pytest.approx(100.0)
        assert results[1][1] == pytest.approx(300.0)

    def test_withdrawals_decrease_balance(self):
        txs = [
            Transaction("T1", TransactionType.DEPOSIT,  500.0, "EUR"),
            Transaction("T2", TransactionType.WITHDRAW, 200.0, "EUR"),
        ]
        results = list(running_total(txs))
        assert results[1][1] == pytest.approx(300.0)

    def test_payments_decrease_balance(self):
        txs = [
            Transaction("T1", TransactionType.DEPOSIT, 200.0, "EUR"),
            Transaction("T2", TransactionType.PAYMENT,  50.0, "EUR"),
        ]
        results = list(running_total(txs))
        assert results[1][1] == pytest.approx(150.0)

    def test_yields_transaction_and_balance_tuples(self):
        txs = [Transaction("T1", TransactionType.DEPOSIT, 100.0, "EUR")]
        result = list(running_total(txs))
        tx, balance = result[0]
        assert tx.id == "T1"
        assert balance == pytest.approx(100.0)

    def test_empty_source_returns_empty(self):
        assert list(running_total([])) == []


class TestSummarize:
    def test_counts_per_type(self, mixed_transactions: list[Transaction]):
        stats = summarize(mixed_transactions)
        assert stats["counts"][TransactionType.DEPOSIT] == 3
        assert stats["counts"][TransactionType.WITHDRAW] == 1
        assert stats["counts"][TransactionType.PAYMENT] == 1

    def test_totals_per_type(self, mixed_transactions: list[Transaction]):
        stats = summarize(mixed_transactions)
        # Einzahlungen: 1000 + 500 + 300 = 1800
        assert stats["totals"][TransactionType.DEPOSIT] == pytest.approx(1_800.0)
        # Abhebungen: 200
        assert stats["totals"][TransactionType.WITHDRAW] == pytest.approx(200.0)

    def test_net_balance_by_currency(self, mixed_transactions: list[Transaction]):
        stats = summarize(mixed_transactions)
        # EUR: +1000 - 200 - 50 + 300 = 1050
        assert stats["by_currency"]["EUR"] == pytest.approx(1_050.0)
        # USD: +500
        assert stats["by_currency"]["USD"] == pytest.approx(500.0)

    def test_empty_input_returns_empty_dicts(self):
        stats = summarize([])
        assert stats["counts"] == {}
        assert stats["totals"] == {}
        assert stats["by_currency"] == {}

    def test_pipeline_composition(self, mixed_transactions: list[Transaction]):
        """filter_by_currency | summarize – nur EUR-Transaktionen aggregiert."""
        eur_only = filter_by_currency(mixed_transactions, "EUR")
        stats = summarize(eur_only)
        # USD-Währung darf nicht auftauchen
        assert "USD" not in stats["by_currency"]
        assert stats["counts"][TransactionType.DEPOSIT] == 2  # T1 und T5

    def test_chained_filters(self, mixed_transactions: list[Transaction]):
        """filter_by_type | filter_by_currency | summarize – vollständige Pipeline."""
        eur_deposits = filter_by_type(
            filter_by_currency(mixed_transactions, "EUR"),
            TransactionType.DEPOSIT,
        )
        stats = summarize(eur_deposits)
        assert TransactionType.WITHDRAW not in stats["counts"]
        assert stats["totals"].get(TransactionType.DEPOSIT, 0) == pytest.approx(1_300.0)
