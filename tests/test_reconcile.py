import unittest
from decimal import Decimal

from budget_lib.reconcile import aggregate_by_uo_fonte, aggregate_repasse


class TestAggregateByUoFonte(unittest.TestCase):
    def test_sums_values_for_same_key(self):
        rows = [
            {'uo': '1011', 'fonte': '10', 'valor': Decimal('100')},
            {'uo': '1011', 'fonte': '10', 'valor': Decimal('50')},
            {'uo': '1011', 'fonte': '20', 'valor': Decimal('5')},
        ]
        totals = aggregate_by_uo_fonte(rows)
        self.assertEqual(totals, {
            ('1011', '10'): Decimal('150'),
            ('1011', '20'): Decimal('5'),
        })

    def test_empty_rows_gives_empty_dict(self):
        self.assertEqual(aggregate_by_uo_fonte([]), {})


class TestAggregateRepasse(unittest.TestCase):
    def test_splits_saida_e_entrada(self):
        rows = [
            {'uo_cedente': '2261', 'uo_beneficiada': '4711', 'fonte': '60', 'valor': Decimal('100')},
        ]
        saida, entrada = aggregate_repasse(rows)
        self.assertEqual(saida, {('2261', '60'): Decimal('100')})
        self.assertEqual(entrada, {('4711', '60'): Decimal('100')})

    def test_sums_multiple_repasses_same_uo_fonte(self):
        rows = [
            {'uo_cedente': '2261', 'uo_beneficiada': '4711', 'fonte': '60', 'valor': Decimal('100')},
            {'uo_cedente': '2261', 'uo_beneficiada': '9999', 'fonte': '60', 'valor': Decimal('30')},
        ]
        saida, entrada = aggregate_repasse(rows)
        self.assertEqual(saida, {('2261', '60'): Decimal('130')})
        self.assertEqual(entrada, {('4711', '60'): Decimal('100'), ('9999', '60'): Decimal('30')})


if __name__ == '__main__':
    unittest.main()
