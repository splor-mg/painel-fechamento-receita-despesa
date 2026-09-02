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


from budget_lib.reconcile import build_uo_names, build_uo_siglas, build_fonte_names, reconcile


class TestBuildUoNames(unittest.TestCase):
    def test_merges_despesa_and_receita_first_seen_wins(self):
        despesa_rows = [{'uo': '1011', 'nome_uo': 'ALMG'}]
        receita_rows = [{'uo': '1011', 'nome_uo': 'ALMG DUP'}, {'uo': '2001', 'nome_uo': 'OUTRA'}]
        names = build_uo_names(despesa_rows, receita_rows)
        self.assertEqual(names, {'1011': 'ALMG', '2001': 'OUTRA'})


class TestBuildUoSiglas(unittest.TestCase):
    def test_merges_despesa_and_receita_first_seen_wins(self):
        despesa_rows = [{'uo': '1251', 'sigla_uo': 'PMMG'}]
        receita_rows = [{'uo': '1251', 'sigla_uo': 'PMMG DUP'}, {'uo': '1011', 'sigla_uo': 'ALMG'}]
        siglas = build_uo_siglas(despesa_rows, receita_rows)
        self.assertEqual(siglas, {'1251': 'PMMG', '1011': 'ALMG'})


class TestBuildFonteNames(unittest.TestCase):
    def test_prefers_fonte_desc_over_repasse(self):
        fonte_desc_rows = [{'fonte': '60', 'nome_fonte': 'RECURSOS DIRETAMENTE ARRECADADOS'}]
        repasse_rows = [{'fonte': '60', 'nome_fonte': 'RECURSOS PROPRIOS'}]
        names = build_fonte_names(fonte_desc_rows, repasse_rows)
        self.assertEqual(names, {'60': 'RECURSOS DIRETAMENTE ARRECADADOS'})

    def test_falls_back_to_repasse_when_missing_from_fonte_desc(self):
        fonte_desc_rows = []
        repasse_rows = [{'fonte': '60', 'nome_fonte': 'RECURSOS PROPRIOS'}]
        names = build_fonte_names(fonte_desc_rows, repasse_rows)
        self.assertEqual(names, {'60': 'RECURSOS PROPRIOS'})


class TestReconcile(unittest.TestCase):
    def test_status_ok_when_equal(self):
        despesa = {('1011', '60'): Decimal('100')}
        receita = {('1011', '60'): Decimal('100')}
        records = reconcile(despesa, receita, {}, {}, {'1011': 'ALMG'}, {}, {})
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r['uo'], '1011')
        self.assertEqual(r['nome_uo'], 'ALMG')
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['diferenca'], Decimal('0'))

    def test_status_divergente_with_repasse_saida(self):
        despesa = {('1011', '60'): Decimal('100')}
        receita = {('1011', '60'): Decimal('100')}
        saida = {('1011', '60'): Decimal('30')}
        records = reconcile(despesa, receita, saida, {}, {}, {}, {})
        r = records[0]
        # lado_despesa = 100 + 30 = 130; lado_receita = 100 + 0 = 100
        self.assertEqual(r['diferenca'], Decimal('30'))
        self.assertEqual(r['status'], 'Divergente')

    def test_status_ok_with_repasse_entrada_balancing(self):
        despesa = {('4711', '60'): Decimal('0')}
        receita = {}
        entrada = {('4711', '60'): Decimal('50')}
        despesa2 = {('4711', '60'): Decimal('50')}
        records = reconcile(despesa2, receita, {}, entrada, {}, {}, {})
        r = records[0]
        # lado_despesa = 50 + 0 = 50; lado_receita = 0 + 50 = 50
        self.assertEqual(r['diferenca'], Decimal('0'))
        self.assertEqual(r['status'], 'OK')

    def test_union_of_keys_missing_treated_as_zero(self):
        despesa = {('1011', '60'): Decimal('100')}
        records = reconcile(despesa, {}, {}, {}, {}, {}, {})
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r['valor_loa'], Decimal('0'))
        self.assertEqual(r['diferenca'], Decimal('100'))

    def test_results_sorted_by_uo_then_fonte(self):
        despesa = {('2000', '10'): Decimal('1'), ('1000', '20'): Decimal('1'), ('1000', '10'): Decimal('1')}
        records = reconcile(despesa, {}, {}, {}, {}, {}, {})
        keys = [(r['uo'], r['fonte']) for r in records]
        self.assertEqual(keys, [('1000', '10'), ('1000', '20'), ('2000', '10')])

    def test_includes_sigla_uo_from_lookup(self):
        despesa = {('1251', '60'): Decimal('100')}
        records = reconcile(despesa, {}, {}, {}, {}, {}, {'1251': 'PMMG'})
        self.assertEqual(records[0]['sigla_uo'], 'PMMG')


if __name__ == '__main__':
    unittest.main()
