import json
from datetime import datetime, timezone
from decimal import Decimal

from budget_lib.reconcile import STATUS_ARRECADADA_9901


def build_metadata(records: list[dict]) -> dict:
    """KPI counters for a reconciliation tab.

    Statuses other than OK/Divergente (such as the fontes collected by UO
    9901) are counted on their own and left out of both the divergence
    count and the divergence total, matching what the table shows.
    """
    total = len(records)
    ok = sum(1 for r in records if r['status'] == 'OK')
    divergentes = [r for r in records if r['status'] == 'Divergente']
    arrecadadas_9901 = sum(1 for r in records if r['status'] == STATUS_ARRECADADA_9901)
    soma_divergencias_abs = sum((abs(r['diferenca']) for r in divergentes), Decimal('0'))
    return {
        'gerado_em': datetime.now(timezone.utc).isoformat(),
        'total_combinacoes': total,
        'total_ok': ok,
        'total_divergente': len(divergentes),
        'total_arrecadadas_9901': arrecadadas_9901,
        'soma_divergencias_abs': format(soma_divergencias_abs, 'f'),
    }


def build_metadata_simples(records: list[dict], valor_key: str) -> dict:
    valor_total = sum((r[valor_key] for r in records), Decimal('0'))
    return {
        'gerado_em': datetime.now(timezone.utc).isoformat(),
        'total_registros': len(records),
        'valor_total': format(valor_total, 'f'),
    }


def _decimal_to_str(value):
    if isinstance(value, Decimal):
        return format(value, 'f')
    return value


def _record_to_json_ready(record: dict) -> dict:
    return {k: _decimal_to_str(v) for k, v in record.items()}


def write_json(records: list[dict], metadata: dict, path) -> None:
    payload = {
        'metadata': metadata,
        'registros': [_record_to_json_ready(r) for r in records],
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
