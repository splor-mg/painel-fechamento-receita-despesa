import unittest
from decimal import Decimal

from budget_lib.limite_orcamentario import aggregate_por_uo_grupo_iag_fonte_ipu, reconcile_limite


class TestAggregatePorUoGrupoIagFonteIpu(unittest.TestCase):
    def test_sums_values_for_same_key(self):
        rows = [
            {'uo': '2371', 'grupo': '3', 'iag': '1', 'fonte': '91', 'ipu': '1', 'valor': Decimal('100')},
            {'uo': '2371', 'grupo': '3', 'iag': '1', 'fonte': '91', 'ipu': '1', 'valor': Decimal('50')},
            {'uo': '2371', 'grupo': '3', 'iag': '1', 'fonte': '91', 'ipu': '2', 'valor': Decimal('5')},
        ]
        totals = aggregate_por_uo_grupo_iag_fonte_ipu(rows)
        self.assertEqual(totals, {
            ('2371', '3', '1', '91', '1'): Decimal('150'),
            ('2371', '3', '1', '91', '2'): Decimal('5'),
        })

    def test_empty_rows_gives_empty_dict(self):
        self.assertEqual(aggregate_por_uo_grupo_iag_fonte_ipu([]), {})


class TestReconcileLimite(unittest.TestCase):
    def test_status_ok_when_equal(self):
        despesa = {('2371', '3', '1', '91', '1'): Decimal('100')}
        limite = {('2371', '3', '1', '91', '1'): Decimal('100')}
        records = reconcile_limite(despesa, limite, {'2371': 'IMA'})
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r['uo'], '2371')
        self.assertEqual(r['sigla_uo'], 'IMA')
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['diferenca'], Decimal('0'))

    def test_diferenca_is_limite_minus_despesa(self):
        despesa = {('2371', '3', '1', '91', '1'): Decimal('80')}
        limite = {('2371', '3', '1', '91', '1'): Decimal('100')}
        records = reconcile_limite(despesa, limite, {})
        # limite (100) - despesa (80) = 20 (positivo = ainda ha margem)
        self.assertEqual(records[0]['diferenca'], Decimal('20'))
        self.assertEqual(records[0]['status'], 'Divergente')

    def test_diferenca_is_negative_when_despesa_exceeds_limite(self):
        despesa = {('2371', '3', '1', '91', '1'): Decimal('120')}
        limite = {('2371', '3', '1', '91', '1'): Decimal('100')}
        records = reconcile_limite(despesa, limite, {})
        # limite (100) - despesa (120) = -20 (negativo = estourou o limite)
        self.assertEqual(records[0]['diferenca'], Decimal('-20'))

    def test_union_of_keys_missing_treated_as_zero(self):
        despesa = {('2371', '3', '1', '91', '1'): Decimal('100')}
        records = reconcile_limite(despesa, {}, {})
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r['valor_limite'], Decimal('0'))
        self.assertEqual(r['diferenca'], Decimal('-100'))

    def test_results_sorted_by_key(self):
        despesa = {
            ('2000', '3', '1', '91', '1'): Decimal('1'),
            ('1000', '3', '2', '91', '1'): Decimal('1'),
            ('1000', '3', '1', '91', '1'): Decimal('1'),
        }
        records = reconcile_limite(despesa, {}, {})
        keys = [(r['uo'], r['iag']) for r in records]
        self.assertEqual(keys, [('1000', '1'), ('1000', '2'), ('2000', '1')])


if __name__ == '__main__':
    unittest.main()
