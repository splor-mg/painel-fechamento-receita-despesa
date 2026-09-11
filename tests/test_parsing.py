import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from budget_lib.parsing import (
    parse_valor_despesa,
    parse_valor_opcional,
    parse_valor_plain,
    read_acao_exportacao,
    read_despesa,
    read_despesa_detalhada,
    read_fonte_desc,
    read_intra_orcamentaria,
    read_limite_orcamentario,
    read_receita,
    read_repasse,
)


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
            'sigla_uo': 'UOT',
            'fonte': '10',
            'valor': Decimal('1500.00'),
        }])

    def test_sums_nothing_but_reads_multiple_rows(self):
        content = (
            'Unidade Orçamentária;Nome da UO;Sigla da UO;Fonte de Recursos;Valor Proposto Ano\n'
            '1011;UO A;UOA;10;"100,00"\n'
            '1011;UO A;UOA;10;"50,00"\n'
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
            'sigla_uo': 'UOT',
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


class TestReadFonteDesc(unittest.TestCase):
    def test_reads_relevant_columns(self):
        content = (
            'Fonte;Nome da Fonte\n'
            '60;RECURSOS DIRETAMENTE ARRECADADOS\n'
            '10;RECURSOS ORDINARIOS\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fonte_desc.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_fonte_desc(path)
        self.assertEqual(rows, [
            {'fonte': '60', 'nome_fonte': 'RECURSOS DIRETAMENTE ARRECADADOS'},
            {'fonte': '10', 'nome_fonte': 'RECURSOS ORDINARIOS'},
        ])


class TestParseValorOpcional(unittest.TestCase):
    def test_parses_plain_integer(self):
        self.assertEqual(parse_valor_opcional('1000'), Decimal('1000'))

    def test_blank_becomes_zero(self):
        self.assertEqual(parse_valor_opcional(''), Decimal('0'))
        self.assertEqual(parse_valor_opcional('   '), Decimal('0'))


class TestReadAcaoExportacao(unittest.TestCase):
    def test_reads_relevant_columns(self):
        content = (
            'Código da Unidade Orçamentária Responsável pela Ação;'
            'Unidade Orçamentária Responsável pela Ação;Exclusão Lógica da Ação;'
            'Justificativa  Exclusão da Ação;Código da Ação;Título da Ação;'
            'Previsão Orçamentária 2027;Previsão Orçamentária 2028;'
            'Previsão Orçamentária 2029;Previsão Orçamentária 2030\n'
            '2181;FUNDACAO CLOVIS SALGADO;Não;;7004;PRECATORIOS;368237;1000;1000;1000\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'acao.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_acao_exportacao(path)
        self.assertEqual(rows, [{
            'uo': '2181',
            'nome_uo': 'FUNDACAO CLOVIS SALGADO',
            'acao': '7004',
            'nome_acao': 'PRECATORIOS',
            'justificativa_exclusao': '',
            'exclusao_logica': False,
            'previsao_2027': Decimal('368237'),
            'previsao_2028': Decimal('1000'),
            'previsao_2029': Decimal('1000'),
            'previsao_2030': Decimal('1000'),
        }])

    def test_blank_previsao_becomes_zero_and_keeps_justificativa(self):
        content = (
            'Código da Unidade Orçamentária Responsável pela Ação;'
            'Unidade Orçamentária Responsável pela Ação;Exclusão Lógica da Ação;'
            'Justificativa  Exclusão da Ação;Código da Ação;Título da Ação;'
            'Previsão Orçamentária 2027;Previsão Orçamentária 2028;'
            'Previsão Orçamentária 2029;Previsão Orçamentária 2030\n'
            '4651;FECIDAT;Sim;Fundo extinto pela Lei 25.350;7038;APORTE;100;;;\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'acao.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_acao_exportacao(path)
        r = rows[0]
        self.assertEqual(r['justificativa_exclusao'], 'Fundo extinto pela Lei 25.350')
        self.assertTrue(r['exclusao_logica'])
        self.assertEqual(r['previsao_2028'], Decimal('0'))
        self.assertEqual(r['previsao_2029'], Decimal('0'))
        self.assertEqual(r['previsao_2030'], Decimal('0'))


class TestReadDespesaDetalhada(unittest.TestCase):
    def test_reads_relevant_columns(self):
        content = (
            'Ano;Poder;Órgão;Nome do Órgão;Unidade Orçamentária;Nome da UO;Sigla da UO;'
            'Função;Subfunção;Programa;Nome do Programa;Ação;Identificador Projeto Atividade;'
            'Projeto Atividade;Nome da Ação;Subprojeto / Subatividade;Categoria;'
            'Grupo de Despesa (GND);Modalidade de Aplicação;Elemento de Despesa;'
            'Item de Despesa;IAG;Fonte de Recursos;Identificador de Procedência e Uso;'
            'Valor Proposto Ano\n'
            '2027;1;1010;ORGAO TESTE;1011;UO TESTE;UOT;28;846;705;NOME PROGRAMA;7004;7;004;'
            'NOME ACAO TESTE;0001;3;1;90;91;3;0;10;9;"1000000,00"\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'despesa.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_despesa_detalhada(path)
        self.assertEqual(rows, [{
            'uo': '1011',
            'nome_uo': 'UO TESTE',
            'sigla_uo': 'UOT',
            'funcao': '28',
            'acao': '7004',
            'nome_acao': 'NOME ACAO TESTE',
            'grupo': '1',
            'modalidade': '90',
            'elemento': '91',
            'item': '3',
            'iag': '0',
            'fonte': '10',
            'ipu': '9',
            'valor': Decimal('1000000.00'),
        }])


class TestReadLimiteOrcamentario(unittest.TestCase):
    def test_reads_relevant_columns(self):
        content = (
            'Ano;UO;SIGLA;GRUPO;IAG;FONTE;IPU;VALOR LIMITE\n'
            '2027;2371;IMA;3;1;91;1;1000\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'limite.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_limite_orcamentario(path)
        self.assertEqual(rows, [{
            'uo': '2371',
            'sigla_uo': 'IMA',
            'grupo': '3',
            'iag': '1',
            'fonte': '91',
            'ipu': '1',
            'valor': Decimal('1000'),
        }])


class TestReadIntraOrcamentaria(unittest.TestCase):
    def test_reads_relevant_columns(self):
        content = (
            'Ano;Unidade Orçamentária Beneficiada;Nome da Ação;Programa de Trabalho;'
            'Natureza da Despesa;Código do Item;Nome do Elemento Item;Valor Distribuído;'
            'Data da Inclusão;Unidade Orçamentária Repassadora;Sigla Repassadora;'
            'Sigla Beneficiada;Valor Detalhado (R$)\n'
            '2027;2011;ACAO TESTE;2.15.1;3.1.91.13;21;ELEMENTO TESTE;"3258,00";'
            '27/08/2026;2151;FHA;IPSEMG;"9999,00"\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'intra.csv'
            path.write_text(content, encoding='utf-8-sig')
            rows = read_intra_orcamentaria(path)
        self.assertEqual(rows, [{
            'uo_repassadora': '2151',
            'sigla_repassadora': 'FHA',
            'uo_beneficiada': '2011',
            'sigla_beneficiada': 'IPSEMG',
            'valor': Decimal('3258.00'),
        }])


if __name__ == '__main__':
    unittest.main()
