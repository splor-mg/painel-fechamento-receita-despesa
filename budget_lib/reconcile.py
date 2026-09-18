from collections import defaultdict
from decimal import Decimal

STATUS_ARRECADADA_9901 = 'Fontes Arrecadadas pela 9901'

# Fontes whose revenue is collected centrally by UO 9901 (RGE): the receita
# sits entirely on 9901 while the despesa sits on each spending UO, so the
# two sides never match per UO. That is structural, not an error, and gets
# its own status instead of "Divergente".
FONTES_ARRECADADAS_9901 = frozenset({
    '10', '11', '12', '15', '20', '23', '25', '27', '29', '30', '31', '32',
    '33', '40', '46', '48', '51', '53', '71', '72', '75', '80', '82', '89',
    '94', '95', '97',
})


def status_uo_fonte(diferenca: Decimal, fonte: str) -> str:
    if diferenca == 0:
        return 'OK'
    if fonte in FONTES_ARRECADADAS_9901:
        return STATUS_ARRECADADA_9901
    return 'Divergente'


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


def build_uo_siglas(despesa_rows: list[dict], receita_rows: list[dict]) -> dict:
    siglas = {}
    for row in despesa_rows:
        siglas.setdefault(row['uo'], row['sigla_uo'])
    for row in receita_rows:
        siglas.setdefault(row['uo'], row['sigla_uo'])
    return siglas


def build_fonte_names(fonte_desc_rows: list[dict], repasse_rows: list[dict]) -> dict:
    names = {}
    for row in fonte_desc_rows:
        names.setdefault(row['fonte'], row['nome_fonte'])
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
    uo_siglas: dict,
) -> list[dict]:
    zero = Decimal('0')
    keys = set(despesa_totals) | set(receita_totals) | set(repasse_saida) | set(repasse_entrada)
    records = []
    for uo, fonte in sorted(keys):
        valor_despesa = despesa_totals.get((uo, fonte), zero)
        valor_loa = receita_totals.get((uo, fonte), zero)
        valor_repassado_saida = repasse_saida.get((uo, fonte), zero)
        valor_repassado_entrada = repasse_entrada.get((uo, fonte), zero)
        lado_saida = valor_despesa + valor_repassado_saida
        lado_entrada = valor_loa + valor_repassado_entrada
        diferenca = lado_entrada - lado_saida
        records.append({
            'uo': uo,
            'nome_uo': uo_names.get(uo, ''),
            'sigla_uo': uo_siglas.get(uo, ''),
            'fonte': fonte,
            'nome_fonte': fonte_names.get(fonte, ''),
            'valor_despesa': valor_despesa,
            'valor_repassado_saida': valor_repassado_saida,
            'valor_loa': valor_loa,
            'valor_repassado_entrada': valor_repassado_entrada,
            'diferenca': diferenca,
            'status': status_uo_fonte(diferenca, fonte),
        })
    return records
