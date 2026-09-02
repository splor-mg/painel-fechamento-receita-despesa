from collections import defaultdict
from decimal import Decimal


def aggregate_by_uo_fonte(rows: list[dict]) -> dict:
    totals = defaultdict(lambda: Decimal('0'))
    for row in rows:
        totals[(row['uo'], row['fonte'])] += row['valor']
    return dict(totals)


def aggregate_repasse(rows: list[dict]) -> tuple[dict, dict]:
    saida = defaultdict(lambda: Decimal('0'))
    entrada = defaultdict(lambda: Decimal('0'))
    for row in rows:
        saida[(row['uo_cedente'], row['fonte'])] += row['valor']
        entrada[(row['uo_beneficiada'], row['fonte'])] += row['valor']
    return dict(saida), dict(entrada)


def build_uo_names(despesa_rows: list[dict], receita_rows: list[dict]) -> dict:
    names = {}
    for row in despesa_rows:
        names.setdefault(row['uo'], row['nome_uo'])
    for row in receita_rows:
        names.setdefault(row['uo'], row['nome_uo'])
    return names


def build_fonte_names(repasse_rows: list[dict]) -> dict:
    names = {}
    for row in repasse_rows:
        names.setdefault(row['fonte'], row['nome_fonte'])
    return names


def reconcile(
    despesa_totals: dict,
    receita_totals: dict,
    repasse_saida: dict,
    repasse_entrada: dict,
    uo_names: dict,
    fonte_names: dict,
) -> list[dict]:
    zero = Decimal('0')
    keys = set(despesa_totals) | set(receita_totals) | set(repasse_saida) | set(repasse_entrada)
    records = []
    for uo, fonte in sorted(keys):
        valor_despesa = despesa_totals.get((uo, fonte), zero)
        valor_loa = receita_totals.get((uo, fonte), zero)
        valor_repassado_saida = repasse_saida.get((uo, fonte), zero)
        valor_repassado_entrada = repasse_entrada.get((uo, fonte), zero)
        lado_despesa = valor_despesa + valor_repassado_saida
        lado_receita = valor_loa + valor_repassado_entrada
        diferenca = lado_despesa - lado_receita
        records.append({
            'uo': uo,
            'nome_uo': uo_names.get(uo, ''),
            'fonte': fonte,
            'nome_fonte': fonte_names.get(fonte, ''),
            'valor_despesa': valor_despesa,
            'valor_repassado_saida': valor_repassado_saida,
            'valor_loa': valor_loa,
            'valor_repassado_entrada': valor_repassado_entrada,
            'diferenca': diferenca,
            'status': 'OK' if diferenca == zero else 'Divergente',
        })
    return records
