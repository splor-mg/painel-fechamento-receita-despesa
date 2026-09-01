import csv
from decimal import Decimal
from pathlib import Path


def parse_valor_despesa(raw: str) -> Decimal:
    """Parse Despesa's comma-decimal format, e.g. '1000000,00' -> Decimal('1000000.00')."""
    return Decimal(raw.strip().replace(',', '.'))


def parse_valor_plain(raw: str) -> Decimal:
    """Parse Receita/Repasse's plain integer format, e.g. '23500000' -> Decimal('23500000')."""
    return Decimal(raw.strip())
