import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from budget_lib.parsing import parse_valor_despesa, parse_valor_plain, read_despesa, read_receita, read_repasse


class TestParseValorDespesa(unittest.TestCase):
    def test_parses_comma_decimal(self):
        self.assertEqual(parse_valor_despesa('1000000,00'), Decimal('1000000.00'))

    def test_parses_comma_decimal_with_cents(self):
        self.assertEqual(parse_valor_despesa('30000,50'), Decimal('30000.50'))

    def test_strips_whitespace(self):
        self.assertEqual(parse_valor_despesa('  1500,00 '), Decimal('1500.00'))


class TestParseValorPlain(unittest.TestCase):
    def test_parses_plain_integer_string(self):
        self.assertEqual(parse_valor_plain('23500000'), Decimal('23500000'))

    def test_strips_whitespace(self):
        self.assertEqual(parse_valor_plain(' 100 '), Decimal('100'))


class TestReadDespesa(unittest.TestCase):
    def test_reads_relevant_columns(self):
        content = (
            'Ano;Poder;Órgão;Nome do Órgão;Unidade Orçamentária;Nome da UO;Sigla da UO;'
            'Fonte de Recursos;Valor Proposto Ano\n'
            '2027;1;1010;ORGAO TESTE;1011;UO TESTE;UOT;10;"1500,00"\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'despesa.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_despesa(path)
        self.assertEqual(rows, [{
            'uo': '1011',
            'nome_uo': 'UO TESTE',
            'fonte': '10',
            'valor': Decimal('1500.00'),
        }])

    def test_sums_nothing_but_reads_multiple_rows(self):
        content = (
            'Unidade Orçamentária;Nome da UO;Fonte de Recursos;Valor Proposto Ano\n'
            '1011;UO A;10;"100,00"\n'
            '1011;UO A;10;"50,00"\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'despesa.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_despesa(path)
        self.assertEqual(len(rows), 2)


class TestReadReceita(unittest.TestCase):
    def test_reads_relevant_columns(self):
        content = (
            'Ano;Unidade Orçamentária;Nome da UO;Sigla UO;Fonte;Valor LDO;Valor LOA\n'
            '2027;1011;UO TESTE;UOT;60;100;23500000\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'receita.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_receita(path)
        self.assertEqual(rows, [{
            'uo': '1011',
            'nome_uo': 'UO TESTE',
            'fonte': '60',
            'valor': Decimal('23500000'),
        }])


class TestReadRepasse(unittest.TestCase):
    def test_reads_relevant_columns(self):
        content = (
            'Ano;U.O. Cedente;Nome da U.O. Cedente;U.O. Beneficiada;Nome U.O. Beneficiada;'
            'Fonte;Nome da Fonte;Valor Repassado\n'
            '2027;2261;UO CEDENTE;4711;UO BENEFICIADA;60;RECURSOS PROPRIOS;34739894\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'repasse.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_repasse(path)
        self.assertEqual(rows, [{
            'uo_cedente': '2261',
            'nome_uo_cedente': 'UO CEDENTE',
            'uo_beneficiada': '4711',
            'nome_uo_beneficiada': 'UO BENEFICIADA',
            'fonte': '60',
            'nome_fonte': 'RECURSOS PROPRIOS',
            'valor': Decimal('34739894'),
        }])


if __name__ == '__main__':
    unittest.main()
