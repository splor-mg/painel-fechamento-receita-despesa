from pathlib import Path

from budget_lib.parsing import read_despesa, read_receita, read_repasse
from budget_lib.reconcile import (
    aggregate_by_uo_fonte,
    aggregate_repasse,
    build_fonte_names,
    build_uo_names,
    reconcile,
)
from budget_lib.output import build_metadata, write_json

BASE_DIR = Path(__file__).parent
DESPESA_CSV = BASE_DIR / 'Despesa_Orcamentaria_Fiscal_2027.csv'
RECEITA_CSV = BASE_DIR / 'Orcamento_Receita.csv'
REPASSE_CSV = BASE_DIR / 'repasse-recurso.csv'
OUTPUT_JSON = BASE_DIR / 'data.json'


def main() -> None:
    despesa_rows = read_despesa(DESPESA_CSV)
    receita_rows = read_receita(RECEITA_CSV)
    repasse_rows = read_repasse(REPASSE_CSV)

    despesa_totals = aggregate_by_uo_fonte(despesa_rows)
    receita_totals = aggregate_by_uo_fonte(receita_rows)
    repasse_saida, repasse_entrada = aggregate_repasse(repasse_rows)

    uo_names = build_uo_names(despesa_rows, receita_rows)
    fonte_names = build_fonte_names(repasse_rows)

    records = reconcile(
        despesa_totals, receita_totals, repasse_saida, repasse_entrada, uo_names, fonte_names
    )
    metadata = build_metadata(records)

    write_json(records, metadata, OUTPUT_JSON)
    print(
        f"Gerado {OUTPUT_JSON} com {metadata['total_combinacoes']} combinacoes UO+Fonte "
        f"({metadata['total_ok']} OK, {metadata['total_divergente']} divergentes)."
    )


if __name__ == '__main__':
    main()
