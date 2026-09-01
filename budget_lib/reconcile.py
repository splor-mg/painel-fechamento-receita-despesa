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
