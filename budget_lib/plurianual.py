from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

ANOS_PLURIANUAL = ('previsao_2028', 'previsao_2029', 'previsao_2030')


def aggregate_despesa_por_acao(rows: list[dict]) -> dict:
    totals = defaultdict(lambda: Decimal('0'))
    for row in rows:
        totals[(row['uo'], row['acao'])] += row['valor']
    return dict(totals)


def aggregate_previsoes(acao_rows: list[dict]) -> dict:
    """Sum the four Previsão Orçamentária columns per UO+Ação.

    Rows carrying a "Justificativa  Exclusão da Ação" are dropped: those
    ações are being removed from the PPAG and are not conferred here.
    """
    previsoes = {}
    for row in acao_rows:
        if row['justificativa_exclusao']:
            continue
        chave = (row['uo'], row['acao'])
        atual = previsoes.get(chave)
        if atual is None:
            previsoes[chave] = {
                'nome_uo': row['nome_uo'],
                'nome_acao': row['nome_acao'],
                'exclusao_logica': row['exclusao_logica'],
                'previsao_2027': row['previsao_2027'],
                'previsao_2028': row['previsao_2028'],
                'previsao_2029': row['previsao_2029'],
                'previsao_2030': row['previsao_2030'],
            }
        else:
            atual['exclusao_logica'] = atual['exclusao_logica'] or row['exclusao_logica']
            for ano in ('previsao_2027',) + ANOS_PLURIANUAL:
                atual[ano] += row[ano]
    return previsoes


def reconcile_plurianual(previsoes: dict, despesa_totais: dict, uo_siglas: dict) -> list[dict]:
    zero = Decimal('0')
    records = []
    for (uo, acao), previsao in sorted(previsoes.items()):
        valor_despesa = despesa_totais.get((uo, acao), zero)
        # Ações flagged for removal from the PPAG are only conferred while
        # they still carry detailed expense in 2027.
        if previsao['exclusao_logica'] and valor_despesa == zero:
            continue
        diferenca_2027 = previsao['previsao_2027'] - valor_despesa
        tem_ano_zerado = any(previsao[ano] == zero for ano in ANOS_PLURIANUAL)
        records.append({
            'uo': uo,
            'sigla_uo': uo_siglas.get(uo, ''),
            'nome_uo': previsao['nome_uo'],
            'acao': acao,
            'nome_acao': previsao['nome_acao'],
            'valor_despesa': valor_despesa,
            'previsao_2027': previsao['previsao_2027'],
            'previsao_2028': previsao['previsao_2028'],
            'previsao_2029': previsao['previsao_2029'],
            'previsao_2030': previsao['previsao_2030'],
            'diferenca_2027': diferenca_2027,
            'status_2027': 'OK' if diferenca_2027 == zero else 'Divergente',
            'status_plurianual': 'Zerado' if tem_ano_zerado else 'OK',
        })
    return records


def build_metadata_plurianual(records: list[dict]) -> dict:
    total = len(records)
    ok_2027 = sum(1 for r in records if r['status_2027'] == 'OK')
    plurianual_zerado = sum(1 for r in records if r['status_plurianual'] == 'Zerado')
    soma_divergencias_abs = sum((abs(r['diferenca_2027']) for r in records), Decimal('0'))
    return {
        'gerado_em': datetime.now(timezone.utc).isoformat(),
        'total_acoes': total,
        'total_2027_ok': ok_2027,
        'total_2027_divergente': total - ok_2027,
        'total_plurianual_zerado': plurianual_zerado,
        'soma_divergencias_abs': format(soma_divergencias_abs, 'f'),
    }
