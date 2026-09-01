import unittest
from decimal import Decimal

from budget_lib.parsing import parse_valor_despesa, parse_valor_plain


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


if __name__ == '__main__':
    unittest.main()
