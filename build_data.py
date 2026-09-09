from pathlib import Path

from budget_lib.parsing import (
    read_despesa,
    read_despesa_detalhada,
    read_fonte_desc,
    read_intra_orcamentaria,
    read_limite_orcamentario,
    read_receita,
    read_repasse,
)
from budget_lib.reconcile import (
    aggregate_by_uo_fonte,
    aggregate_repasse,
    build_fonte_names,
    build_uo_names,
    build_uo_siglas,
    reconcile,
)
from budget_lib.intra_patronal import aggregate_intra_orcamentaria, read_projetado, reconcile_intra_patronal
from budget_lib.limite_orcamentario import aggregate_por_uo_grupo_iag_fonte_ipu, reconcile_limite
from budget_lib.output import build_metadata, build_metadata_simples, write_json

BASE_DIR = Path(__file__).parent
DESPESA_CSV = BASE_DIR / 'Despesa_Orcamentaria_Fiscal_2027.csv'
RECEITA_CSV = BASE_DIR / 'Orcamento_Receita.csv'
REPASSE_CSV = BASE_DIR / 'repasse-recurso.csv'
FONTE_DESC_CSV = BASE_DIR / 'fonte_desc.csv'
PROJETADO_CSV = BASE_DIR / 'pessoal_intra_credor_patronal.csv'
INTRA_ORCAMENTARIA_CSV = BASE_DIR / 'Despesa_Intraorcamentaria_2027.csv'
LIMITE_CSV = BASE_DIR / 'Limite_Orcamentario.csv'
OUTPUT_JSON = BASE_DIR / 'data.json'
OUTPUT_INTRA_JSON = BASE_DIR / 'data_intra_patronal.json'
OUTPUT_DESPESA_DETALHADA_JSON = BASE_DIR / 'data_despesa_detalhada.json'
OUTPUT_LIMITE_JSON = BASE_DIR / 'data_limite_orcamentario.json'


def main() -> None:
    despesa_rows = read_despesa(DESPESA_CSV)
    receita_rows = read_receita(RECEITA_CSV)
    repasse_rows = read_repasse(REPASSE_CSV)
    fonte_desc_rows = read_fonte_desc(FONTE_DESC_CSV)

    despesa_totals = aggregate_by_uo_fonte(despesa_rows)
    receita_totals = aggregate_by_uo_fonte(receita_rows)
    repasse_saida, repasse_entrada = aggregate_repasse(repasse_rows)

    uo_names = build_uo_names(despesa_rows, receita_rows)
    uo_siglas = build_uo_siglas(despesa_rows, receita_rows)
    fonte_names = build_fonte_names(fonte_desc_rows, repasse_rows)

    records = reconcile(
        despesa_totals, receita_totals, repasse_saida, repasse_entrada, uo_names, fonte_names, uo_siglas
    )
    metadata = build_metadata(records)

    write_json(records, metadata, OUTPUT_JSON)
    print(
        f"Gerado {OUTPUT_JSON} com {metadata['total_combinacoes']} combinacoes UO+Fonte "
        f"({metadata['total_ok']} OK, {metadata['total_divergente']} divergentes)."
    )

    projetado_rows = read_projetado(PROJETADO_CSV)
    intra_orcamentaria_rows = read_intra_orcamentaria(INTRA_ORCAMENTARIA_CSV)
    distribuido_totais = aggregate_intra_orcamentaria(intra_orcamentaria_rows)
    intra_records = reconcile_intra_patronal(projetado_rows, distribuido_totais)
    intra_metadata = build_metadata(intra_records)

    write_json(intra_records, intra_metadata, OUTPUT_INTRA_JSON)
    print(
        f"Gerado {OUTPUT_INTRA_JSON} com {intra_metadata['total_combinacoes']} combinacoes UO+Credor "
        f"({intra_metadata['total_ok']} OK, {intra_metadata['total_divergente']} divergentes)."
    )

    despesa_detalhada_rows = read_despesa_detalhada(DESPESA_CSV)
    despesa_detalhada_metadata = build_metadata_simples(despesa_detalhada_rows, 'valor')

    write_json(despesa_detalhada_rows, despesa_detalhada_metadata, OUTPUT_DESPESA_DETALHADA_JSON)
    print(
        f"Gerado {OUTPUT_DESPESA_DETALHADA_JSON} com {despesa_detalhada_metadata['total_registros']} registros "
        f"(valor total {despesa_detalhada_metadata['valor_total']})."
    )

    limite_rows = read_limite_orcamentario(LIMITE_CSV)
    despesa_totais_limite = aggregate_por_uo_grupo_iag_fonte_ipu(despesa_detalhada_rows)
    limite_totais = aggregate_por_uo_grupo_iag_fonte_ipu(limite_rows)
    uo_siglas_limite = build_uo_siglas(limite_rows, despesa_detalhada_rows)
    limite_records = reconcile_limite(despesa_totais_limite, limite_totais, uo_siglas_limite)
    limite_metadata = build_metadata(limite_records)

    write_json(limite_records, limite_metadata, OUTPUT_LIMITE_JSON)
    print(
        f"Gerado {OUTPUT_LIMITE_JSON} com {limite_metadata['total_combinacoes']} combinacoes "
        f"UO+Grupo+IAG+Fonte+IPU ({limite_metadata['total_ok']} OK, {limite_metadata['total_divergente']} divergentes)."
    )


if __name__ == '__main__':
    main()
