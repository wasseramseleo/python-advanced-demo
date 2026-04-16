"""Tests für ledger.models – Transaction-Dataclass und Parser."""

import pytest

from ledger.models import Transaction, TransactionType, parse_transaction_line


class TestTransactionType:
    """TransactionType-Enum verhält sich wie ein String."""

    def test_string_equality(self):
        assert TransactionType.DEPOSIT == "DEPOSIT"
        assert TransactionType.WITHDRAW == "WITHDRAW"
        assert TransactionType.PAYMENT == "PAYMENT"

    def test_from_string(self):
        assert TransactionType("DEPOSIT") is TransactionType.DEPOSIT

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            TransactionType("TRANSFER")


class TestTransaction:
    """Transaction ist ein frozen Dataclass – unveränderlich nach Erstellung."""

    def test_fields_accessible(self):
        tx = Transaction(id="T1", type=TransactionType.DEPOSIT, amount=100.0, currency="EUR")
        assert tx.id == "T1"
        assert tx.type == TransactionType.DEPOSIT
        assert tx.amount == pytest.approx(100.0)
        assert tx.currency == "EUR"

    def test_immutable(self):
        """frozen=True verhindert Mutation – wichtig für Buchhaltungsintegrität."""
        tx = Transaction(id="T1", type=TransactionType.DEPOSIT, amount=100.0, currency="EUR")
        with pytest.raises(AttributeError):
            tx.amount = 999.0  # type: ignore[misc]

    def test_str_contains_key_info(self):
        tx = Transaction(id="T42", type=TransactionType.DEPOSIT, amount=100.0, currency="EUR")
        result = str(tx)
        assert "T42" in result
        assert "DEPOSIT" in result
        assert "100.00" in result
        assert "EUR" in result

    def test_deposit_str_has_plus_sign(self):
        tx = Transaction(id="T1", type=TransactionType.DEPOSIT, amount=50.0, currency="EUR")
        assert "+" in str(tx)

    def test_withdraw_str_has_minus_sign(self):
        tx = Transaction(id="T1", type=TransactionType.WITHDRAW, amount=50.0, currency="EUR")
        assert "-" in str(tx)


class TestParseTransactionLine:
    """parse_transaction_line parst das pipe-separierte Log-Format."""

    def test_parse_withdraw(self):
        line = "ID: T1000 | TYPE: WITHDRAW | AMOUNT: 6657.49 | CURRENCY: USD"
        tx = parse_transaction_line(line)
        assert tx.id == "T1000"
        assert tx.type == TransactionType.WITHDRAW
        assert tx.amount == pytest.approx(6657.49)
        assert tx.currency == "USD"

    def test_parse_deposit(self):
        line = "ID: T9999 | TYPE: DEPOSIT | AMOUNT: 1.00 | CURRENCY: EUR"
        tx = parse_transaction_line(line)
        assert tx.type == TransactionType.DEPOSIT
        assert tx.amount == pytest.approx(1.00)

    def test_parse_payment(self):
        line = "ID: T0001 | TYPE: PAYMENT | AMOUNT: 99.99 | CURRENCY: CHF"
        tx = parse_transaction_line(line)
        assert tx.type == TransactionType.PAYMENT
        assert tx.currency == "CHF"

    def test_whitespace_is_trimmed(self):
        """Leerzeichen um Schlüssel und Werte werden toleriert."""
        line = "ID:  T1  | TYPE:  DEPOSIT  | AMOUNT:  10.00  | CURRENCY:  EUR  "
        tx = parse_transaction_line(line)
        assert tx.id == "T1"
        assert tx.currency == "EUR"

    def test_invalid_line_raises_value_error(self):
        with pytest.raises(ValueError, match="geparst"):
            parse_transaction_line("das ist kein gültiges Format")

    def test_unknown_transaction_type_raises(self):
        line = "ID: T1 | TYPE: TRANSFER | AMOUNT: 10.00 | CURRENCY: EUR"
        with pytest.raises(ValueError):
            parse_transaction_line(line)

    def test_invalid_amount_raises(self):
        line = "ID: T1 | TYPE: DEPOSIT | AMOUNT: abc | CURRENCY: EUR"
        with pytest.raises(ValueError):
            parse_transaction_line(line)
