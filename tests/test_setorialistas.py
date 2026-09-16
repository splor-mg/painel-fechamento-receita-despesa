import unittest

from budget_lib.setorialistas import SEM_SETORIALISTA, aplicar_setorialistas, build_lookup


def setorialista_row(uo='1011', setorialista='Otto', dupla_trio='Bárbara/Otto'):
    return {'uo': uo, 'sigla_uo': 'ALMG', 'setorialista': setorialista, 'dupla_trio': dupla_trio}


class TestBuildLookup(unittest.TestCase):
    def test_maps_uo_to_setorialista_e_dupla(self):
        lookup = build_lookup([setorialista_row()])
        self.assertEqual(lookup, {
            '1011': {'setorialista': 'Otto', 'dupla_trio': 'Bárbara/Otto'},
        })

    def test_primeira_linha_vence_em_uo_repetida(self):
        lookup = build_lookup([
            setorialista_row(setorialista='Otto'),
            setorialista_row(setorialista='Barbara'),
        ])
        self.assertEqual(lookup['1011']['setorialista'], 'Otto')

    def test_celula_vazia_vira_outros(self):
        lookup = build_lookup([setorialista_row(setorialista='', dupla_trio='')])
        self.assertEqual(lookup['1011'], {
            'setorialista': SEM_SETORIALISTA,
            'dupla_trio': SEM_SETORIALISTA,
        })


class TestAplicarSetorialistas(unittest.TestCase):
    def test_marca_registro_com_a_atribuicao_da_uo(self):
        lookup = build_lookup([setorialista_row()])
        records = aplicar_setorialistas([{'uo': '1011'}], lookup)
        self.assertEqual(records[0]['setorialista'], 'Otto')
        self.assertEqual(records[0]['dupla_trio'], 'Bárbara/Otto')

    def test_uo_fora_da_planilha_vira_outros(self):
        lookup = build_lookup([setorialista_row()])
        records = aplicar_setorialistas([{'uo': '4761'}], lookup)
        self.assertEqual(records[0]['setorialista'], SEM_SETORIALISTA)
        self.assertEqual(records[0]['dupla_trio'], SEM_SETORIALISTA)

    def test_preserva_os_demais_campos(self):
        lookup = build_lookup([setorialista_row()])
        records = aplicar_setorialistas([{'uo': '1011', 'valor': 10, 'status': 'OK'}], lookup)
        self.assertEqual(records[0]['valor'], 10)
        self.assertEqual(records[0]['status'], 'OK')

    def test_lista_vazia(self):
        self.assertEqual(aplicar_setorialistas([], build_lookup([])), [])


if __name__ == '__main__':
    unittest.main()
