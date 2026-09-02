from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from budget_lib.parsing import parse_valor_plain, read_csv_rows

CREDORES = [
    ('FFP', '4711'),
    ('IPSM', '2121'),
    ('IPLEMG', '2361'),
    ('IPSEMG', '2011'),
]


def read_projetado(path: Path) -> list[dict]:
    rows = read_csv_rows(path)
    result = []
    for row in rows:
        for credor, uo_credor in CREDORES:
            result.append({
                'uo': row['UO'].strip(),
                'sigla_uo': row['UO_SIGLA'].strip(),
                'credor': credor,
                'uo_credor': uo_credor,
                'valor_projetado': parse_valor_plain(row[credor]),
            })
    return result


def aggregate_intra_orcamentaria(rows: list[dict]) -> dict:
    totals = defaultdict(lambda: Decimal('0'))
    for row in rows:
        totals[(row['uo_repassadora'], row['uo_beneficiada'])] += row['valor']
    return dict(totals)


def reconcile_intra_patronal(projetado_rows: list[dict], distribuido_totais: dict) -> list[dict]:
    zero = Decimal('0')
    records = []
    for row in projetado_rows:
        valor_projetado = row['valor_projetado']
        valor_repassado = distribuido_totais.get((row['uo'], row['uo_credor']), zero)
        if valor_projetado == zero and valor_repassado == zero:
            continue
        diferenca = valor_projetado - valor_repassado
        records.append({
            'uo': row['uo'],
            'sigla_uo': row['sigla_uo'],
            'credor': row['credor'],
            'uo_credor': row['uo_credor'],
            'valor_projetado': valor_projetado,
            'valor_repassado': valor_repassado,
            'diferenca': diferenca,
            'status': 'OK' if diferenca == zero else 'Divergente',
        })
    records.sort(key=lambda r: (r['uo'], r['credor']))
    return records
