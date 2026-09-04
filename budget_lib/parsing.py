import csv
from decimal import Decimal
from pathlib import Path


def parse_valor_despesa(raw: str) -> Decimal:
    """Parse Despesa's comma-decimal format, e.g. '1000000,00' -> Decimal('1000000.00')."""
    return Decimal(raw.strip().replace(',', '.'))


def parse_valor_plain(raw: str) -> Decimal:
    """Parse Receita/Repasse's plain integer format, e.g. '23500000' -> Decimal('23500000')."""
    return Decimal(raw.strip())


def read_csv_rows(path: Path) -> list[dict]:
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        return list(reader)


def read_despesa(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    return [{
        'uo': row['Unidade Orçamentária'].strip(),
        'nome_uo': row['Nome da UO'].strip(),
        'sigla_uo': row['Sigla da UO'].strip(),
        'fonte': row['Fonte de Recursos'].strip(),
        'valor': parse_valor_despesa(row['Valor Proposto Ano']),
    } for row in rows]


def read_receita(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    return [{
        'uo': row['Unidade Orçamentária'].strip(),
        'nome_uo': row['Nome da UO'].strip(),
        'sigla_uo': row['Sigla UO'].strip(),
        'fonte': row['Fonte'].strip(),
        'valor': parse_valor_plain(row['Valor LOA']),
    } for row in rows]


def read_fonte_desc(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    return [{
        'fonte': row['Fonte'].strip(),
        'nome_fonte': row['Nome da Fonte'].strip(),
    } for row in rows]


def read_repasse(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    return [{
        'uo_cedente': row['U.O. Cedente'].strip(),
        'nome_uo_cedente': row['Nome da U.O. Cedente'].strip(),
        'uo_beneficiada': row['U.O. Beneficiada'].strip(),
        'nome_uo_beneficiada': row['Nome U.O. Beneficiada'].strip(),
        'fonte': row['Fonte'].strip(),
        'nome_fonte': row['Nome da Fonte'].strip(),
        'valor': parse_valor_plain(row['Valor Repassado']),
    } for row in rows]


def read_despesa_detalhada(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    return [{
        'uo': row['Unidade Orçamentária'].strip(),
        'nome_uo': row['Nome da UO'].strip(),
        'sigla_uo': row['Sigla da UO'].strip(),
        'funcao': row['Função'].strip(),
        'acao': row['Ação'].strip(),
        'nome_acao': row['Nome da Ação'].strip(),
        'grupo': row['Grupo de Despesa (GND)'].strip(),
        'modalidade': row['Modalidade de Aplicação'].strip(),
        'elemento': row['Elemento de Despesa'].strip(),
        'item': row['Item de Despesa'].strip(),
        'fonte': row['Fonte de Recursos'].strip(),
        'ipu': row['Identificador de Procedência e Uso'].strip(),
        'valor': parse_valor_despesa(row['Valor Proposto Ano']),
    } for row in rows]


def read_intra_orcamentaria(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    return [{
        'uo_repassadora': row['Unidade Orçamentária Repassadora'].strip(),
        'sigla_repassadora': row['Sigla Repassadora'].strip(),
        'uo_beneficiada': row['Unidade Orçamentária Beneficiada'].strip(),
        'sigla_beneficiada': row['Sigla Beneficiada'].strip(),
        'valor': parse_valor_despesa(row['Valor Distribuído']),
    } for row in rows]
