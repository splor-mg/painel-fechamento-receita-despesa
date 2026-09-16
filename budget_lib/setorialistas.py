SEM_SETORIALISTA = 'Outros'


def build_lookup(setorialista_rows: list[dict]) -> dict:
    """Map each UO code to its setorialista and dupla/trio (first row wins)."""
    lookup = {}
    for row in setorialista_rows:
        lookup.setdefault(row['uo'], {
            'setorialista': row['setorialista'] or SEM_SETORIALISTA,
            'dupla_trio': row['dupla_trio'] or SEM_SETORIALISTA,
        })
    return lookup


def aplicar_setorialistas(records: list[dict], lookup: dict) -> list[dict]:
    """Tag every record with the setorialista and dupla/trio of its UO.

    UOs missing from the lookup fall back to "Outros", so the filters always
    cover the whole table.
    """
    for record in records:
        atribuicao = lookup.get(record['uo'])
        record['setorialista'] = atribuicao['setorialista'] if atribuicao else SEM_SETORIALISTA
        record['dupla_trio'] = atribuicao['dupla_trio'] if atribuicao else SEM_SETORIALISTA
    return records
