import json
from datetime import datetime, timezone
from decimal import Decimal


def build_metadata(records: list[dict]) -> dict:
    total = len(records)
    ok = sum(1 for r in records if r['status'] == 'OK')
    divergente = total - ok
    soma_divergencias_abs = sum((abs(r['diferenca']) for r in records), Decimal('0'))
    return {
        'gerado_em': datetime.now(timezone.utc).isoformat(),
        'total_combinacoes': total,
        'total_ok': ok,
        'total_divergente': divergente,
        'soma_divergencias_abs': format(soma_divergencias_abs, 'f'),
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
