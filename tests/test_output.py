import json
import unittest
import tempfile
from decimal import Decimal
from pathlib import Path

from budget_lib.output import build_metadata, write_json


class TestBuildMetadata(unittest.TestCase):
    def test_counts_ok_and_divergente(self):
        records = [
            {'status': 'OK', 'diferenca': Decimal('0')},
            {'status': 'Divergente', 'diferenca': Decimal('30')},
            {'status': 'Divergente', 'diferenca': Decimal('-10')},
        ]
        metadata = build_metadata(records)
        self.assertEqual(metadata['total_combinacoes'], 3)
        self.assertEqual(metadata['total_ok'], 1)
        self.assertEqual(metadata['total_divergente'], 2)
        self.assertEqual(metadata['soma_divergencias_abs'], '40')

    def test_empty_records(self):
        metadata = build_metadata([])
        self.assertEqual(metadata['total_combinacoes'], 0)
        self.assertEqual(metadata['total_ok'], 0)
        self.assertEqual(metadata['total_divergente'], 0)
        self.assertEqual(metadata['soma_divergencias_abs'], '0')


class TestWriteJson(unittest.TestCase):
    def test_writes_valid_json_with_decimal_as_string(self):
        records = [{
            'uo': '1011', 'nome_uo': 'ALMG', 'fonte': '60', 'nome_fonte': '',
            'valor_despesa': Decimal('100.00'), 'valor_repassado_saida': Decimal('0'),
            'valor_loa': Decimal('100'), 'valor_repassado_entrada': Decimal('0'),
            'diferenca': Decimal('0.00'), 'status': 'OK',
        }]
        metadata = {'total_combinacoes': 1}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.json'
            write_json(records, metadata, path)
            payload = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(payload['metadata'], metadata)
        self.assertEqual(payload['registros'][0]['valor_despesa'], '100.00')
        self.assertEqual(payload['registros'][0]['status'], 'OK')


if __name__ == '__main__':
    unittest.main()
