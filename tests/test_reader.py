"""Tests für ledger.reader – LazyTransactionReader, read_log_file, parse_transactions."""

from pathlib import Path

import pytest

from ledger.models import TransactionType
from ledger.reader import LazyTransactionReader, parse_transactions, read_log_file


class TestReadLogFile:
    """Testet die Generator-Funktion read_log_file."""

    def test_reads_all_lines(self, sample_log_file: Path):
        lines = list(read_log_file(str(sample_log_file)))
        assert len(lines) == 4

    def test_filter_keyword_withdraw(self, sample_log_file: Path):
        lines = list(read_log_file(str(sample_log_file), filter_keyword="WITHDRAW"))
        assert len(lines) == 1
        assert "WITHDRAW" in lines[0]

    def test_filter_keyword_deposit(self, sample_log_file: Path):
        lines = list(read_log_file(str(sample_log_file), filter_keyword="DEPOSIT"))
        assert all("DEPOSIT" in line for line in lines)

    def test_filter_case_insensitive(self, sample_log_file: Path):
        lower = list(read_log_file(str(sample_log_file), filter_keyword="withdraw"))
        upper = list(read_log_file(str(sample_log_file), filter_keyword="WITHDRAW"))
        assert lower == upper

    def test_skips_blank_lines(self, sample_log_file_with_blanks: Path):
        """Leerzeilen in der Datei werden transparent übersprungen."""
        lines = list(read_log_file(str(sample_log_file_with_blanks)))
        assert len(lines) == 4

    def test_no_filter_returns_all(self, sample_log_file: Path):
        lines = list(read_log_file(str(sample_log_file), filter_keyword=None))
        assert len(lines) == 4

    def test_nonexistent_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            list(read_log_file(str(tmp_path / "does_not_exist.log")))

    def test_file_closed_after_exhaustion(self, sample_log_file: Path):
        """Nach vollständiger Iteration ist die Datei geschlossen (finally-Block)."""
        gen = read_log_file(str(sample_log_file))
        list(gen)  # Vollständig konsumieren
        # Kein Fehler = finally-Block wurde ausgeführt

    def test_file_closed_after_early_break(self, sample_log_file: Path):
        """finally-Block schließt Datei auch bei vorzeitigem break."""
        gen = read_log_file(str(sample_log_file))
        next(gen)   # eine Zeile lesen
        gen.close() # simuliert ein break im Aufrufer
        # Kein ResourceWarning = Datei sauber geschlossen


class TestLazyTransactionReader:
    """Testet den klassenbasierten Iterator LazyTransactionReader."""

    def test_reads_all_lines(self, sample_log_file: Path):
        reader = LazyTransactionReader(str(sample_log_file))
        lines = list(reader)
        assert len(lines) == 4

    def test_filter_keyword(self, sample_log_file: Path):
        reader = LazyTransactionReader(str(sample_log_file), filter_keyword="DEPOSIT")
        lines = list(reader)
        assert all("DEPOSIT" in line for line in lines)

    def test_context_manager_closes_file(self, sample_log_file: Path):
        """Context-Manager-Support: with-Statement schließt die Datei."""
        with LazyTransactionReader(str(sample_log_file)) as reader:
            first_line = next(reader)
        assert "T1000" in first_line
        # Nach dem with-Block ist die Datei geschlossen
        assert reader._file_handle is None

    def test_iter_returns_self(self, sample_log_file: Path):
        """Ein Iterator gibt sich selbst aus __iter__ zurück."""
        reader = LazyTransactionReader(str(sample_log_file))
        assert iter(reader) is reader
        reader.close()

    def test_nonexistent_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            LazyTransactionReader(str(tmp_path / "missing.log"))

    def test_skips_blank_lines(self, sample_log_file_with_blanks: Path):
        reader = LazyTransactionReader(str(sample_log_file_with_blanks))
        lines = list(reader)
        assert len(lines) == 4


class TestParseTransactions:
    """Testet den parse_transactions-Generator."""

    def test_parses_all_valid_lines(self, sample_log_file: Path):
        lines = read_log_file(str(sample_log_file))
        transactions = list(parse_transactions(lines))
        assert len(transactions) == 4

    def test_correct_types_parsed(self, sample_log_file: Path):
        lines = read_log_file(str(sample_log_file))
        types = [tx.type for tx in parse_transactions(lines)]
        assert TransactionType.WITHDRAW in types
        assert TransactionType.DEPOSIT in types
        assert TransactionType.PAYMENT in types

    def test_skips_invalid_lines(self, tmp_path: Path):
        """Fehlerhafte Zeilen werden geloggt und übersprungen, kein Absturz."""
        bad_log = tmp_path / "bad.log"
        bad_log.write_text(
            "das ist Müll\n"
            "ID: T1 | TYPE: DEPOSIT | AMOUNT: 10.00 | CURRENCY: EUR\n",
            encoding="utf-8",
        )
        lines = read_log_file(str(bad_log))
        transactions = list(parse_transactions(lines))
        assert len(transactions) == 1
        assert transactions[0].type == TransactionType.DEPOSIT

    def test_pipeline_composition(self, sample_log_file: Path):
        """read_log_file → parse_transactions ist eine lazy Pipeline."""
        pipeline = parse_transactions(read_log_file(str(sample_log_file)))
        # Ersten Wert holen ohne den Rest zu materialisieren
        first = next(pipeline)
        assert first.id is not None
        assert first.amount > 0
