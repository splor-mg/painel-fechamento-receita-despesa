import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from budget_lib.intra_patronal import aggregate_intra_orcamentaria, read_projetado, reconcile_intra_patronal


class TestReadProjetado(unittest.TestCase):
    def test_flattens_one_row_per_credor(self):
        content = (
            'UO;UO_SIGLA;FFP;IPSM;IPLEMG;IPSEMG\n'
            '1251;PMMG;575901984;2310592704;0;3551729\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'projetado.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_projetado(path)
        self.assertEqual(rows, [
            {'uo': '1251', 'sigla_uo': 'PMMG', 'credor': 'FFP', 'uo_credor': '4711', 'valor_projetado': Decimal('575901984')},
            {'uo': '1251', 'sigla_uo': 'PMMG', 'credor': 'IPSM', 'uo_credor': '2121', 'valor_projetado': Decimal('2310592704')},
            {'uo': '1251', 'sigla_uo': 'PMMG', 'credor': 'IPLEMG', 'uo_credor': '2361', 'valor_projetado': Decimal('0')},
            {'uo': '1251', 'sigla_uo': 'PMMG', 'credor': 'IPSEMG', 'uo_credor': '2011', 'valor_projetado': Decimal('3551729')},
        ])


class TestAggregateIntraOrcamentaria(unittest.TestCase):
    def test_sums_by_uo_repassadora_beneficiada(self):
        rows = [
            {'uo_repassadora': '2151', 'uo_beneficiada': '2011', 'valor': Decimal('3258')},
            {'uo_repassadora': '2151', 'uo_beneficiada': '2011', 'valor': Decimal('6290')},
            {'uo_repassadora': '2151', 'uo_beneficiada': '4711', 'valor': Decimal('100')},
        ]
        totals = aggregate_intra_orcamentaria(rows)
        self.assertEqual(totals, {
            ('2151', '2011'): Decimal('9548'),
            ('2151', '4711'): Decimal('100'),
        })


class TestReconcileIntraPatronal(unittest.TestCase):
    def test_status_ok_when_projetado_equals_repassado(self):
        projetado_rows = [
            {'uo': '1251', 'sigla_uo': 'PMMG', 'credor': 'FFP', 'uo_credor': '4711', 'valor_projetado': Decimal('100')},
        ]
        repasse_totais = {('1251', '4711'): Decimal('100')}
        records = reconcile_intra_patronal(projetado_rows, repasse_totais)
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r['diferenca'], Decimal('0'))
        self.assertEqual(r['status'], 'OK')

    def test_diferenca_is_projetado_minus_repassado(self):
        projetado_rows = [
            {'uo': '1251', 'sigla_uo': 'PMMG', 'credor': 'FFP', 'uo_credor': '4711', 'valor_projetado': Decimal('150')},
        ]
        repasse_totais = {('1251', '4711'): Decimal('100')}
        records = reconcile_intra_patronal(projetado_rows, repasse_totais)
        # projetado (150) - repassado (100) = 50 (positivo = falta repassar)
        self.assertEqual(records[0]['diferenca'], Decimal('50'))
        self.assertEqual(records[0]['status'], 'Divergente')

    def test_diferenca_is_negative_when_repassado_exceeds_projetado(self):
        projetado_rows = [
            {'uo': '1251', 'sigla_uo': 'PMMG', 'credor': 'FFP', 'uo_credor': '4711', 'valor_projetado': Decimal('100')},
        ]
        repasse_totais = {('1251', '4711'): Decimal('150')}
        records = reconcile_intra_patronal(projetado_rows, repasse_totais)
        self.assertEqual(records[0]['diferenca'], Decimal('-50'))
        self.assertEqual(records[0]['status'], 'Divergente')

    def test_skips_zero_projetado_and_zero_repassado(self):
        projetado_rows = [
            {'uo': '1011', 'sigla_uo': 'ALMG', 'credor': 'FFP', 'uo_credor': '4711', 'valor_projetado': Decimal('0')},
        ]
        records = reconcile_intra_patronal(projetado_rows, {})
        self.assertEqual(records, [])

    def test_missing_from_repasse_totais_treated_as_zero(self):
        projetado_rows = [
            {'uo': '1011', 'sigla_uo': 'ALMG', 'credor': 'FFP', 'uo_credor': '4711', 'valor_projetado': Decimal('100')},
        ]
        records = reconcile_intra_patronal(projetado_rows, {})
        self.assertEqual(records[0]['valor_repassado'], Decimal('0'))
        self.assertEqual(records[0]['diferenca'], Decimal('100'))

    def test_results_sorted_by_uo_then_credor(self):
        projetado_rows = [
            {'uo': '2000', 'sigla_uo': 'B', 'credor': 'IPSM', 'uo_credor': '2121', 'valor_projetado': Decimal('1')},
            {'uo': '1000', 'sigla_uo': 'A', 'credor': 'IPSEMG', 'uo_credor': '2011', 'valor_projetado': Decimal('1')},
            {'uo': '1000', 'sigla_uo': 'A', 'credor': 'FFP', 'uo_credor': '4711', 'valor_projetado': Decimal('1')},
        ]
        records = reconcile_intra_patronal(projetado_rows, {})
        keys = [(r['uo'], r['credor']) for r in records]
        self.assertEqual(keys, [('1000', 'FFP'), ('1000', 'IPSEMG'), ('2000', 'IPSM')])


if __name__ == '__main__':
    unittest.main()
