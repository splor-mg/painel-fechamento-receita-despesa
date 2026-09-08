from collections import defaultdict
from decimal import Decimal


def aggregate_por_uo_grupo_iag_fonte_ipu(rows: list[dict]) -> dict:
    totals = defaultdict(lambda: Decimal('0'))
    for row in rows:
        key = (row['uo'], row['grupo'], row['iag'], row['fonte'], row['ipu'])
        totals[key] += row['valor']
    return dict(totals)


def reconcile_limite(despesa_totais: dict, limite_totais: dict, uo_siglas: dict) -> list[dict]:
    zero = Decimal('0')
    keys = set(despesa_totais) | set(limite_totais)
    records = []
    for uo, grupo, iag, fonte, ipu in sorted(keys):
        valor_despesa = despesa_totais.get((uo, grupo, iag, fonte, ipu), zero)
        valor_limite = limite_totais.get((uo, grupo, iag, fonte, ipu), zero)
        diferenca = valor_limite - valor_despesa
        records.append({
            'uo': uo,
            'sigla_uo': uo_siglas.get(uo, ''),
            'grupo': grupo,
            'iag': iag,
            'fonte': fonte,
            'ipu': ipu,
            'valor_limite': valor_limite,
            'valor_despesa': valor_despesa,
            'diferenca': diferenca,
            'status': 'OK' if diferenca == zero else 'Divergente',
        })
    return records
