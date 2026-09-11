import unittest
from decimal import Decimal

from budget_lib.plurianual import (
    aggregate_despesa_por_acao,
    aggregate_previsoes,
    build_metadata_plurianual,
    reconcile_plurianual,
)


def acao_row(uo='2181', acao='7004', justificativa='', exclusao_logica=False,
             p2027='100', p2028='100', p2029='100', p2030='100'):
    return {
        'uo': uo,
        'nome_uo': 'UO TESTE',
        'acao': acao,
        'nome_acao': 'ACAO TESTE',
        'justificativa_exclusao': justificativa,
        'exclusao_logica': exclusao_logica,
        'previsao_2027': Decimal(p2027),
        'previsao_2028': Decimal(p2028),
        'previsao_2029': Decimal(p2029),
        'previsao_2030': Decimal(p2030),
    }


class TestAggregateDespesaPorAcao(unittest.TestCase):
    def test_sums_by_uo_acao(self):
        rows = [
            {'uo': '1011', 'acao': '7004', 'valor': Decimal('100')},
            {'uo': '1011', 'acao': '7004', 'valor': Decimal('50')},
            {'uo': '1011', 'acao': '4416', 'valor': Decimal('5')},
        ]
        self.assertEqual(aggregate_despesa_por_acao(rows), {
            ('1011', '7004'): Decimal('150'),
            ('1011', '4416'): Decimal('5'),
        })


class TestAggregatePrevisoes(unittest.TestCase):
    def test_drops_rows_with_justificativa_de_exclusao(self):
        rows = [
            acao_row(acao='7004'),
            acao_row(acao='4502', justificativa='Fundo extinto pela Lei 25.350'),
        ]
        previsoes = aggregate_previsoes(rows)
        self.assertEqual(list(previsoes.keys()), [('2181', '7004')])

    def test_sums_duplicate_uo_acao_rows(self):
        rows = [
            acao_row(p2027='100', p2028='10', p2029='10', p2030='10'),
            acao_row(p2027='50', p2028='5', p2029='5', p2030='5'),
        ]
        previsoes = aggregate_previsoes(rows)
        entrada = previsoes[('2181', '7004')]
        self.assertEqual(entrada['previsao_2027'], Decimal('150'))
        self.assertEqual(entrada['previsao_2028'], Decimal('15'))
        self.assertEqual(entrada['previsao_2030'], Decimal('15'))


class TestReconcilePlurianual(unittest.TestCase):
    def test_status_2027_ok_when_previsao_equals_despesa(self):
        previsoes = aggregate_previsoes([acao_row(p2027='100')])
        records = reconcile_plurianual(previsoes, {('2181', '7004'): Decimal('100')}, {'2181': 'FCS'})
        r = records[0]
        self.assertEqual(r['sigla_uo'], 'FCS')
        self.assertEqual(r['diferenca_2027'], Decimal('0'))
        self.assertEqual(r['status_2027'], 'OK')

    def test_diferenca_is_previsao_minus_despesa(self):
        previsoes = aggregate_previsoes([acao_row(p2027='150')])
        records = reconcile_plurianual(previsoes, {('2181', '7004'): Decimal('100')}, {})
        self.assertEqual(records[0]['diferenca_2027'], Decimal('50'))
        self.assertEqual(records[0]['status_2027'], 'Divergente')

    def test_acao_sem_despesa_detalhada_fica_divergente(self):
        previsoes = aggregate_previsoes([acao_row(p2027='100')])
        records = reconcile_plurianual(previsoes, {}, {})
        self.assertEqual(records[0]['valor_despesa'], Decimal('0'))
        self.assertEqual(records[0]['status_2027'], 'Divergente')

    def test_exclusao_logica_sem_despesa_sai_do_painel(self):
        previsoes = aggregate_previsoes([acao_row(exclusao_logica=True)])
        records = reconcile_plurianual(previsoes, {}, {})
        self.assertEqual(records, [])

    def test_exclusao_logica_com_despesa_permanece_no_painel(self):
        previsoes = aggregate_previsoes([acao_row(exclusao_logica=True, p2027='100')])
        records = reconcile_plurianual(previsoes, {('2181', '7004'): Decimal('79419031')}, {})
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['valor_despesa'], Decimal('79419031'))

    def test_acao_normal_sem_despesa_continua_no_painel(self):
        previsoes = aggregate_previsoes([acao_row(exclusao_logica=False)])
        records = reconcile_plurianual(previsoes, {}, {})
        self.assertEqual(len(records), 1)

    def test_status_plurianual_zerado_quando_algum_ano_e_zero(self):
        previsoes = aggregate_previsoes([acao_row(p2028='100', p2029='0', p2030='100')])
        records = reconcile_plurianual(previsoes, {}, {})
        self.assertEqual(records[0]['status_plurianual'], 'Zerado')

    def test_status_plurianual_ok_quando_todos_os_anos_preenchidos(self):
        previsoes = aggregate_previsoes([acao_row(p2028='1', p2029='2', p2030='3')])
        records = reconcile_plurianual(previsoes, {}, {})
        self.assertEqual(records[0]['status_plurianual'], 'OK')

    def test_ano_de_2027_zerado_nao_afeta_status_plurianual(self):
        previsoes = aggregate_previsoes([acao_row(p2027='0', p2028='1', p2029='2', p2030='3')])
        records = reconcile_plurianual(previsoes, {}, {})
        self.assertEqual(records[0]['status_plurianual'], 'OK')

    def test_results_sorted_by_uo_then_acao(self):
        rows = [
            acao_row(uo='2000', acao='1000'),
            acao_row(uo='1000', acao='2000'),
            acao_row(uo='1000', acao='1000'),
        ]
        records = reconcile_plurianual(aggregate_previsoes(rows), {}, {})
        self.assertEqual(
            [(r['uo'], r['acao']) for r in records],
            [('1000', '1000'), ('1000', '2000'), ('2000', '1000')],
        )


class TestBuildMetadataPlurianual(unittest.TestCase):
    def test_counts_both_checks(self):
        records = [
            {'status_2027': 'OK', 'status_plurianual': 'OK', 'diferenca_2027': Decimal('0')},
            {'status_2027': 'Divergente', 'status_plurianual': 'OK', 'diferenca_2027': Decimal('30')},
            {'status_2027': 'OK', 'status_plurianual': 'Zerado', 'diferenca_2027': Decimal('-10')},
        ]
        metadata = build_metadata_plurianual(records)
        self.assertEqual(metadata['total_acoes'], 3)
        self.assertEqual(metadata['total_2027_ok'], 2)
        self.assertEqual(metadata['total_2027_divergente'], 1)
        self.assertEqual(metadata['total_plurianual_zerado'], 1)
        self.assertEqual(metadata['soma_divergencias_abs'], '40')

    def test_empty_records(self):
        metadata = build_metadata_plurianual([])
        self.assertEqual(metadata['total_acoes'], 0)
        self.assertEqual(metadata['soma_divergencias_abs'], '0')


if __name__ == '__main__':
    unittest.main()
