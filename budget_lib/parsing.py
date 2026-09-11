import csv
from decimal import Decimal
from pathlib import Path


def parse_valor_despesa(raw: str) -> Decimal:
    """Parse Despesa's comma-decimal format, e.g. '1000000,00' -> Decimal('1000000.00')."""
    return Decimal(raw.strip().replace(',', '.'))


def parse_valor_plain(raw: str) -> Decimal:
    """Parse Receita/Repasse's plain integer format, e.g. '23500000' -> Decimal('23500000')."""
    return Decimal(raw.strip())


def parse_valor_opcional(raw: str) -> Decimal:
    """Parse a plain integer that may be blank, e.g. '' -> Decimal('0')."""
    limpo = (raw or '').strip()
    return Decimal(limpo) if limpo else Decimal('0')


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
        'iag': row['IAG'].strip(),
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


def read_acao_exportacao(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    return [{
        'uo': row['Código da Unidade Orçamentária Responsável pela Ação'].strip(),
        'nome_uo': row['Unidade Orçamentária Responsável pela Ação'].strip(),
        'acao': row['Código da Ação'].strip(),
        'nome_acao': row['Título da Ação'].strip(),
        # NB: the source header really has two spaces in "Justificativa  Exclusão".
        'justificativa_exclusao': (row['Justificativa  Exclusão da Ação'] or '').strip(),
        'previsao_2027': parse_valor_opcional(row['Previsão Orçamentária 2027']),
        'previsao_2028': parse_valor_opcional(row['Previsão Orçamentária 2028']),
        'previsao_2029': parse_valor_opcional(row['Previsão Orçamentária 2029']),
        'previsao_2030': parse_valor_opcional(row['Previsão Orçamentária 2030']),
    } for row in rows]


def read_limite_orcamentario(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    return [{
        'uo': row['UO'].strip(),
        'sigla_uo': row['SIGLA'].strip(),
        'grupo': row['GRUPO'].strip(),
        'iag': row['IAG'].strip(),
        'fonte': row['FONTE'].strip(),
        'ipu': row['IPU'].strip(),
        'valor': parse_valor_plain(row['VALOR LIMITE']),
    } for row in rows]
