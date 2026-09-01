# Painel de Fechamento Receita x Despesa Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static web dashboard that reconciles budget expenditure, revenue, and inter-unit transfers per Unidade Orçamentária (UO) + Fonte, and publish it on GitHub Pages.

**Architecture:** A Python script (`build_data.py`, split across a small `budget_lib` package) reads the three source CSVs, aggregates values by UO+Fonte, applies the reconciliation formula, and writes `data.json`. A dependency-free HTML/CSS/JS static page fetches `data.json` and renders KPI cards, two dropdown filters (UO, Fonte), a text search, a divergence-only toggle, and a sortable table.

**Tech Stack:** Python 3 standard library only (`csv`, `json`, `decimal`, `unittest`) for the data pipeline; vanilla HTML/CSS/JS for the frontend; GitHub + GitHub Pages for hosting.

**Reference spec:** `docs/superpowers/specs/2026-09-01-painel-fechamento-design.md`

---

## File Structure

- `budget_lib/__init__.py` — empty, makes `budget_lib` a package
- `budget_lib/parsing.py` — CSV reading + value parsing for all 3 sources
- `budget_lib/reconcile.py` — aggregation by UO+Fonte and the reconciliation formula
- `budget_lib/output.py` — KPI metadata + JSON serialization (Decimal → string)
- `build_data.py` — CLI entry point, wires the above together, writes `data.json`
- `tests/test_parsing.py` — unit tests for `budget_lib/parsing.py`
- `tests/test_reconcile.py` — unit tests for `budget_lib/reconcile.py`
- `tests/test_output.py` — unit tests for `budget_lib/output.py`
- `index.html` — page structure (KPI cards, filters, table)
- `style.css` — styling
- `app.js` — fetch, render, filter, sort logic
- `data.json` — generated output (created by running `build_data.py`, committed so the static site has data to serve)
- `.nojekyll` — tells GitHub Pages to serve files as-is (avoids Jekyll processing surprises)

---

### Task 1: Package scaffolding and CSV value parsing

**Files:**
- Create: `budget_lib/__init__.py`
- Create: `budget_lib/parsing.py`
- Test: `tests/test_parsing.py`
- Test: `tests/__init__.py`

- [ ] **Step 1: Create empty package init files**

```bash
mkdir -p budget_lib tests
```

`budget_lib/__init__.py`:
```python
```

`tests/__init__.py`:
```python
```

- [ ] **Step 2: Write the failing tests for value parsing**

`tests/test_parsing.py`:
```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m unittest tests.test_parsing -v`
Expected: FAIL with `ImportError: cannot import name 'parse_valor_despesa'` (module has no such function yet)

- [ ] **Step 4: Implement value parsing**

`budget_lib/parsing.py`:
```python
import csv
from decimal import Decimal
from pathlib import Path


def parse_valor_despesa(raw: str) -> Decimal:
    """Parse Despesa's comma-decimal format, e.g. '1000000,00' -> Decimal('1000000.00')."""
    return Decimal(raw.strip().replace(',', '.'))


def parse_valor_plain(raw: str) -> Decimal:
    """Parse Receita/Repasse's plain integer format, e.g. '23500000' -> Decimal('23500000')."""
    return Decimal(raw.strip())
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m unittest tests.test_parsing -v`
Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
git add budget_lib/__init__.py budget_lib/parsing.py tests/__init__.py tests/test_parsing.py
git commit -m "Add value parsing for despesa and plain numeric formats"
```

---

### Task 2: CSV row reading for the three sources

**Files:**
- Modify: `budget_lib/parsing.py`
- Modify: `tests/test_parsing.py`

- [ ] **Step 1: Write the failing tests for row reading**

Append to `tests/test_parsing.py` (add these imports and classes; keep the existing ones):

```python
import tempfile
from pathlib import Path

from budget_lib.parsing import read_despesa, read_receita, read_repasse


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_parsing -v`
Expected: FAIL with `ImportError: cannot import name 'read_despesa'`

- [ ] **Step 3: Implement row reading**

Append to `budget_lib/parsing.py`:
```python
def _read_csv_rows(path: Path) -> list[dict]:
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        return list(reader)


def read_despesa(path: Path) -> list[dict]:
    rows = _read_csv_rows(path)
    return [{
        'uo': row['Unidade Orçamentária'].strip(),
        'nome_uo': row['Nome da UO'].strip(),
        'fonte': row['Fonte de Recursos'].strip(),
        'valor': parse_valor_despesa(row['Valor Proposto Ano']),
    } for row in rows]


def read_receita(path: Path) -> list[dict]:
    rows = _read_csv_rows(path)
    return [{
        'uo': row['Unidade Orçamentária'].strip(),
        'nome_uo': row['Nome da UO'].strip(),
        'fonte': row['Fonte'].strip(),
        'valor': parse_valor_plain(row['Valor LOA']),
    } for row in rows]


def read_repasse(path: Path) -> list[dict]:
    rows = _read_csv_rows(path)
    return [{
        'uo_cedente': row['U.O. Cedente'].strip(),
        'nome_uo_cedente': row['Nome da U.O. Cedente'].strip(),
        'uo_beneficiada': row['U.O. Beneficiada'].strip(),
        'nome_uo_beneficiada': row['Nome U.O. Beneficiada'].strip(),
        'fonte': row['Fonte'].strip(),
        'nome_fonte': row['Nome da Fonte'].strip(),
        'valor': parse_valor_plain(row['Valor Repassado']),
    } for row in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_parsing -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Verify against the real CSV files (sanity check, not a unit test)**

Run:
```bash
python -c "
from pathlib import Path
from budget_lib.parsing import read_despesa, read_receita, read_repasse
d = read_despesa(Path('Despesa_Orcamentaria_Fiscal_2027.csv'))
r = read_receita(Path('Orcamento_Receita.csv'))
p = read_repasse(Path('repasse-recurso.csv'))
print(len(d), len(r), len(p))
print(d[0])
print(r[0])
print(p[0])
"
```
Expected: prints `8349 1425 27` (row counts minus header) and one sample dict per source with no `KeyError`.

- [ ] **Step 6: Commit**

```bash
git add budget_lib/parsing.py tests/test_parsing.py
git commit -m "Add CSV row reading for despesa, receita and repasse"
```

---

### Task 3: Aggregation by UO+Fonte

**Files:**
- Create: `budget_lib/reconcile.py`
- Create: `tests/test_reconcile.py`

- [ ] **Step 1: Write the failing tests for aggregation**

`tests/test_reconcile.py`:
```python
import unittest
from decimal import Decimal

from budget_lib.reconcile import aggregate_by_uo_fonte, aggregate_repasse


class TestAggregateByUoFonte(unittest.TestCase):
    def test_sums_values_for_same_key(self):
        rows = [
            {'uo': '1011', 'fonte': '10', 'valor': Decimal('100')},
            {'uo': '1011', 'fonte': '10', 'valor': Decimal('50')},
            {'uo': '1011', 'fonte': '20', 'valor': Decimal('5')},
        ]
        totals = aggregate_by_uo_fonte(rows)
        self.assertEqual(totals, {
            ('1011', '10'): Decimal('150'),
            ('1011', '20'): Decimal('5'),
        })

    def test_empty_rows_gives_empty_dict(self):
        self.assertEqual(aggregate_by_uo_fonte([]), {})


class TestAggregateRepasse(unittest.TestCase):
    def test_splits_saida_e_entrada(self):
        rows = [
            {'uo_cedente': '2261', 'uo_beneficiada': '4711', 'fonte': '60', 'valor': Decimal('100')},
        ]
        saida, entrada = aggregate_repasse(rows)
        self.assertEqual(saida, {('2261', '60'): Decimal('100')})
        self.assertEqual(entrada, {('4711', '60'): Decimal('100')})

    def test_sums_multiple_repasses_same_uo_fonte(self):
        rows = [
            {'uo_cedente': '2261', 'uo_beneficiada': '4711', 'fonte': '60', 'valor': Decimal('100')},
            {'uo_cedente': '2261', 'uo_beneficiada': '9999', 'fonte': '60', 'valor': Decimal('30')},
        ]
        saida, entrada = aggregate_repasse(rows)
        self.assertEqual(saida, {('2261', '60'): Decimal('130')})
        self.assertEqual(entrada, {('4711', '60'): Decimal('100'), ('9999', '60'): Decimal('30')})


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_reconcile -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'budget_lib.reconcile'`

- [ ] **Step 3: Implement aggregation**

`budget_lib/reconcile.py`:
```python
from collections import defaultdict
from decimal import Decimal


def aggregate_by_uo_fonte(rows: list[dict]) -> dict:
    totals = defaultdict(lambda: Decimal('0'))
    for row in rows:
        totals[(row['uo'], row['fonte'])] += row['valor']
    return dict(totals)


def aggregate_repasse(rows: list[dict]) -> tuple[dict, dict]:
    saida = defaultdict(lambda: Decimal('0'))
    entrada = defaultdict(lambda: Decimal('0'))
    for row in rows:
        saida[(row['uo_cedente'], row['fonte'])] += row['valor']
        entrada[(row['uo_beneficiada'], row['fonte'])] += row['valor']
    return dict(saida), dict(entrada)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_reconcile -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add budget_lib/reconcile.py tests/test_reconcile.py
git commit -m "Add UO+Fonte aggregation for despesa, receita and repasse"
```

---

### Task 4: Name lookups and the reconciliation formula

**Files:**
- Modify: `budget_lib/reconcile.py`
- Modify: `tests/test_reconcile.py`

- [ ] **Step 1: Write the failing tests for names and reconcile**

Append to `tests/test_reconcile.py`:

```python
from budget_lib.reconcile import build_uo_names, build_fonte_names, reconcile


class TestBuildUoNames(unittest.TestCase):
    def test_merges_despesa_and_receita_first_seen_wins(self):
        despesa_rows = [{'uo': '1011', 'nome_uo': 'ALMG'}]
        receita_rows = [{'uo': '1011', 'nome_uo': 'ALMG DUP'}, {'uo': '2001', 'nome_uo': 'OUTRA'}]
        names = build_uo_names(despesa_rows, receita_rows)
        self.assertEqual(names, {'1011': 'ALMG', '2001': 'OUTRA'})


class TestBuildFonteNames(unittest.TestCase):
    def test_builds_from_repasse_rows(self):
        repasse_rows = [{'fonte': '60', 'nome_fonte': 'RECURSOS PROPRIOS'}]
        names = build_fonte_names(repasse_rows)
        self.assertEqual(names, {'60': 'RECURSOS PROPRIOS'})


class TestReconcile(unittest.TestCase):
    def test_status_ok_when_equal(self):
        despesa = {('1011', '60'): Decimal('100')}
        receita = {('1011', '60'): Decimal('100')}
        records = reconcile(despesa, receita, {}, {}, {'1011': 'ALMG'}, {})
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r['uo'], '1011')
        self.assertEqual(r['nome_uo'], 'ALMG')
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['diferenca'], Decimal('0'))

    def test_status_divergente_with_repasse_saida(self):
        despesa = {('1011', '60'): Decimal('100')}
        receita = {('1011', '60'): Decimal('100')}
        saida = {('1011', '60'): Decimal('30')}
        records = reconcile(despesa, receita, saida, {}, {}, {})
        r = records[0]
        # lado_despesa = 100 + 30 = 130; lado_receita = 100 + 0 = 100
        self.assertEqual(r['diferenca'], Decimal('30'))
        self.assertEqual(r['status'], 'Divergente')

    def test_status_ok_with_repasse_entrada_balancing(self):
        despesa = {('4711', '60'): Decimal('0')}
        receita = {}
        entrada = {('4711', '60'): Decimal('50')}
        despesa2 = {('4711', '60'): Decimal('50')}
        records = reconcile(despesa2, receita, {}, entrada, {}, {})
        r = records[0]
        # lado_despesa = 50 + 0 = 50; lado_receita = 0 + 50 = 50
        self.assertEqual(r['diferenca'], Decimal('0'))
        self.assertEqual(r['status'], 'OK')

    def test_union_of_keys_missing_treated_as_zero(self):
        despesa = {('1011', '60'): Decimal('100')}
        records = reconcile(despesa, {}, {}, {}, {}, {})
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r['valor_loa'], Decimal('0'))
        self.assertEqual(r['diferenca'], Decimal('100'))

    def test_results_sorted_by_uo_then_fonte(self):
        despesa = {('2000', '10'): Decimal('1'), ('1000', '20'): Decimal('1'), ('1000', '10'): Decimal('1')}
        records = reconcile(despesa, {}, {}, {}, {}, {})
        keys = [(r['uo'], r['fonte']) for r in records]
        self.assertEqual(keys, [('1000', '10'), ('1000', '20'), ('2000', '10')])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_reconcile -v`
Expected: FAIL with `ImportError: cannot import name 'build_uo_names'`

- [ ] **Step 3: Implement names and reconcile**

Append to `budget_lib/reconcile.py`:
```python
def build_uo_names(despesa_rows: list[dict], receita_rows: list[dict]) -> dict:
    names = {}
    for row in despesa_rows:
        names.setdefault(row['uo'], row['nome_uo'])
    for row in receita_rows:
        names.setdefault(row['uo'], row['nome_uo'])
    return names


def build_fonte_names(repasse_rows: list[dict]) -> dict:
    names = {}
    for row in repasse_rows:
        names.setdefault(row['fonte'], row['nome_fonte'])
    return names


def reconcile(
    despesa_totals: dict,
    receita_totals: dict,
    repasse_saida: dict,
    repasse_entrada: dict,
    uo_names: dict,
    fonte_names: dict,
) -> list[dict]:
    zero = Decimal('0')
    keys = set(despesa_totals) | set(receita_totals) | set(repasse_saida) | set(repasse_entrada)
    records = []
    for uo, fonte in sorted(keys):
        valor_despesa = despesa_totals.get((uo, fonte), zero)
        valor_loa = receita_totals.get((uo, fonte), zero)
        valor_repassado_saida = repasse_saida.get((uo, fonte), zero)
        valor_repassado_entrada = repasse_entrada.get((uo, fonte), zero)
        lado_despesa = valor_despesa + valor_repassado_saida
        lado_receita = valor_loa + valor_repassado_entrada
        diferenca = lado_despesa - lado_receita
        records.append({
            'uo': uo,
            'nome_uo': uo_names.get(uo, ''),
            'fonte': fonte,
            'nome_fonte': fonte_names.get(fonte, ''),
            'valor_despesa': valor_despesa,
            'valor_repassado_saida': valor_repassado_saida,
            'valor_loa': valor_loa,
            'valor_repassado_entrada': valor_repassado_entrada,
            'diferenca': diferenca,
            'status': 'OK' if diferenca == zero else 'Divergente',
        })
    return records
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_reconcile -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add budget_lib/reconcile.py tests/test_reconcile.py
git commit -m "Add UO/Fonte name lookups and the reconciliation formula"
```

---

### Task 5: KPI metadata and JSON output

**Files:**
- Create: `budget_lib/output.py`
- Create: `tests/test_output.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_output.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_output -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'budget_lib.output'`

- [ ] **Step 3: Implement metadata and JSON writing**

`budget_lib/output.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_output -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add budget_lib/output.py tests/test_output.py
git commit -m "Add KPI metadata calculation and JSON output writer"
```

---

### Task 6: Wire it together in build_data.py and generate data.json

**Files:**
- Create: `build_data.py`

- [ ] **Step 1: Write build_data.py**

`build_data.py`:
```python
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
```

- [ ] **Step 2: Run it against the real CSVs**

Run: `python build_data.py`
Expected: prints a line like `Gerado .../data.json com N combinacoes UO+Fonte (X OK, Y divergentes).` and creates `data.json` in the project root.

- [ ] **Step 3: Spot-check the output**

Run:
```bash
python -c "
import json
data = json.load(open('data.json', encoding='utf-8'))
print(data['metadata'])
print(data['registros'][0])
print(len(data['registros']))
"
```
Expected: metadata dict with `total_combinacoes`, `total_ok`, `total_divergente`, `soma_divergencias_abs`; first record has keys `uo, nome_uo, fonte, nome_fonte, valor_despesa, valor_repassado_saida, valor_loa, valor_repassado_entrada, diferenca, status`; no Python exceptions.

- [ ] **Step 4: Commit**

```bash
git add build_data.py data.json
git commit -m "Add build_data.py entry point and generate data.json"
```

---

### Task 7: Static page structure and styling

**Files:**
- Create: `index.html`
- Create: `style.css`

- [ ] **Step 1: Write index.html**

`index.html`:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Painel de Fechamento Receita x Despesa</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <h1>Painel de Fechamento Receita x Despesa</h1>
  <p id="gerado-em" class="subtitle"></p>
</header>

<section id="kpis" class="kpi-grid">
  <div class="kpi-card">
    <span class="kpi-label">Combinações UO+Fonte</span>
    <span class="kpi-value" id="kpi-total">-</span>
  </div>
  <div class="kpi-card kpi-ok">
    <span class="kpi-label">OK</span>
    <span class="kpi-value" id="kpi-ok">-</span>
  </div>
  <div class="kpi-card kpi-divergente">
    <span class="kpi-label">Divergentes</span>
    <span class="kpi-value" id="kpi-divergente">-</span>
  </div>
  <div class="kpi-card">
    <span class="kpi-label">Soma das divergências (abs.)</span>
    <span class="kpi-value" id="kpi-soma-divergencias">-</span>
  </div>
</section>

<section id="filtros" class="filtros">
  <div class="filtro-campo">
    <label for="filtro-uo">Unidade Orçamentária</label>
    <select id="filtro-uo"><option value="">Todas</option></select>
  </div>
  <div class="filtro-campo">
    <label for="filtro-fonte">Fonte</label>
    <select id="filtro-fonte"><option value="">Todas</option></select>
  </div>
  <div class="filtro-campo">
    <label for="filtro-busca">Buscar</label>
    <input type="text" id="filtro-busca" placeholder="UO, Fonte ou nome...">
  </div>
  <div class="filtro-campo filtro-checkbox">
    <label><input type="checkbox" id="filtro-divergentes"> Mostrar só divergências</label>
  </div>
</section>

<main>
  <table id="tabela-reconciliacao">
    <thead>
      <tr>
        <th data-sort="uo">UO</th>
        <th data-sort="fonte">Fonte</th>
        <th data-sort="valor_despesa">Valor Proposto Ano</th>
        <th data-sort="valor_repassado_saida">Repassado (saída)</th>
        <th data-sort="valor_loa">Valor LOA</th>
        <th data-sort="valor_repassado_entrada">Repassado (entrada)</th>
        <th data-sort="diferenca">Diferença</th>
        <th data-sort="status">Status</th>
      </tr>
    </thead>
    <tbody id="tabela-corpo"></tbody>
  </table>
  <p id="tabela-vazia" class="tabela-vazia" hidden>Nenhum registro encontrado para os filtros aplicados.</p>
</main>

<script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write style.css**

`style.css`:
```css
* { box-sizing: border-box; }

body {
  font-family: system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
  margin: 0;
  padding: 1.5rem 2rem 3rem;
  background: #f5f6f8;
  color: #1f2933;
}

header h1 { margin: 0 0 0.25rem; font-size: 1.5rem; }
.subtitle { margin: 0 0 1.5rem; color: #616e7c; font-size: 0.85rem; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.kpi-card {
  background: #fff;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.kpi-label { font-size: 0.75rem; color: #616e7c; text-transform: uppercase; letter-spacing: 0.03em; }
.kpi-value { font-size: 1.5rem; font-weight: 600; }
.kpi-ok .kpi-value { color: #1a7f37; }
.kpi-divergente .kpi-value { color: #c0341d; }

.filtros {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  background: #fff;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.filtro-campo { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; }
.filtro-campo label { color: #616e7c; }
.filtro-campo select, .filtro-campo input[type="text"] {
  padding: 0.4rem 0.5rem;
  border: 1px solid #cbd2d9;
  border-radius: 6px;
  font-size: 0.9rem;
  min-width: 200px;
}
.filtro-checkbox { flex-direction: row; align-items: center; gap: 0.4rem; }
.filtro-checkbox label { display: flex; align-items: center; gap: 0.4rem; color: #1f2933; }

table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

thead th {
  text-align: left;
  background: #eef1f4;
  padding: 0.6rem 0.75rem;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  color: #616e7c;
  cursor: pointer;
  white-space: nowrap;
}

tbody td {
  padding: 0.55rem 0.75rem;
  border-top: 1px solid #eef1f4;
  font-size: 0.88rem;
  white-space: nowrap;
}

tbody tr:hover { background: #fafbfc; }

.status-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}
.status-ok { background: #dcfce7; color: #1a7f37; }
.status-divergente { background: #fde2e1; color: #c0341d; }

.tabela-vazia { text-align: center; color: #616e7c; padding: 2rem; }

main { overflow-x: auto; }
```

- [ ] **Step 3: Commit**

```bash
git add index.html style.css
git commit -m "Add static page structure and styling"
```

---

### Task 8: Frontend data loading, rendering, filtering and sorting

**Files:**
- Create: `app.js`

- [ ] **Step 1: Write app.js**

`app.js`:
```javascript
const state = {
  registros: [],
  sortKey: 'uo',
  sortDir: 1,
};

const els = {
  geradoEm: document.getElementById('gerado-em'),
  kpiTotal: document.getElementById('kpi-total'),
  kpiOk: document.getElementById('kpi-ok'),
  kpiDivergente: document.getElementById('kpi-divergente'),
  kpiSomaDivergencias: document.getElementById('kpi-soma-divergencias'),
  filtroUo: document.getElementById('filtro-uo'),
  filtroFonte: document.getElementById('filtro-fonte'),
  filtroBusca: document.getElementById('filtro-busca'),
  filtroDivergentes: document.getElementById('filtro-divergentes'),
  tabelaCorpo: document.getElementById('tabela-corpo'),
  tabelaVazia: document.getElementById('tabela-vazia'),
  tabela: document.getElementById('tabela-reconciliacao'),
};

const formatterBRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

function formatBRL(value) {
  return formatterBRL.format(Number(value));
}

function uniqueSorted(values) {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b, 'pt-BR', { numeric: true }));
}

function populateFiltros(registros) {
  const uos = uniqueSorted(registros.map((r) => r.uo));
  const fontes = uniqueSorted(registros.map((r) => r.fonte));

  for (const uo of uos) {
    const nome = registros.find((r) => r.uo === uo)?.nome_uo || '';
    const option = document.createElement('option');
    option.value = uo;
    option.textContent = nome ? `${uo} - ${nome}` : uo;
    els.filtroUo.appendChild(option);
  }

  for (const fonte of fontes) {
    const nome = registros.find((r) => r.fonte === fonte && r.nome_fonte)?.nome_fonte || '';
    const option = document.createElement('option');
    option.value = fonte;
    option.textContent = nome ? `${fonte} - ${nome}` : fonte;
    els.filtroFonte.appendChild(option);
  }
}

function renderKpis(metadata) {
  els.geradoEm.textContent = metadata.gerado_em
    ? `Gerado em ${new Date(metadata.gerado_em).toLocaleString('pt-BR')}`
    : '';
  els.kpiTotal.textContent = metadata.total_combinacoes;
  els.kpiOk.textContent = metadata.total_ok;
  els.kpiDivergente.textContent = metadata.total_divergente;
  els.kpiSomaDivergencias.textContent = formatBRL(metadata.soma_divergencias_abs);
}

function getFiltered() {
  const uo = els.filtroUo.value;
  const fonte = els.filtroFonte.value;
  const busca = els.filtroBusca.value.trim().toLowerCase();
  const soDivergentes = els.filtroDivergentes.checked;

  return state.registros.filter((r) => {
    if (uo && r.uo !== uo) return false;
    if (fonte && r.fonte !== fonte) return false;
    if (soDivergentes && r.status !== 'Divergente') return false;
    if (busca) {
      const haystack = `${r.uo} ${r.nome_uo} ${r.fonte} ${r.nome_fonte}`.toLowerCase();
      if (!haystack.includes(busca)) return false;
    }
    return true;
  });
}

function getSorted(registros) {
  const { sortKey, sortDir } = state;
  const numericKeys = new Set([
    'valor_despesa', 'valor_repassado_saida', 'valor_loa', 'valor_repassado_entrada', 'diferenca',
  ]);
  return [...registros].sort((a, b) => {
    let va = a[sortKey];
    let vb = b[sortKey];
    if (numericKeys.has(sortKey)) {
      va = Number(va);
      vb = Number(vb);
      return (va - vb) * sortDir;
    }
    return String(va).localeCompare(String(vb), 'pt-BR', { numeric: true }) * sortDir;
  });
}

function renderTabela() {
  const filtrados = getSorted(getFiltered());
  els.tabelaCorpo.innerHTML = '';

  if (filtrados.length === 0) {
    els.tabela.hidden = true;
    els.tabelaVazia.hidden = false;
    return;
  }

  els.tabela.hidden = false;
  els.tabelaVazia.hidden = true;

  const frag = document.createDocumentFragment();
  for (const r of filtrados) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.uo}${r.nome_uo ? ` - ${r.nome_uo}` : ''}</td>
      <td>${r.fonte}${r.nome_fonte ? ` - ${r.nome_fonte}` : ''}</td>
      <td>${formatBRL(r.valor_despesa)}</td>
      <td>${formatBRL(r.valor_repassado_saida)}</td>
      <td>${formatBRL(r.valor_loa)}</td>
      <td>${formatBRL(r.valor_repassado_entrada)}</td>
      <td>${formatBRL(r.diferenca)}</td>
      <td><span class="status-badge ${r.status === 'OK' ? 'status-ok' : 'status-divergente'}">${r.status}</span></td>
    `;
    frag.appendChild(tr);
  }
  els.tabelaCorpo.appendChild(frag);
}

function onSortClick(event) {
  const th = event.target.closest('th[data-sort]');
  if (!th) return;
  const key = th.dataset.sort;
  if (state.sortKey === key) {
    state.sortDir *= -1;
  } else {
    state.sortKey = key;
    state.sortDir = 1;
  }
  renderTabela();
}

function wireEvents() {
  els.filtroUo.addEventListener('change', renderTabela);
  els.filtroFonte.addEventListener('change', renderTabela);
  els.filtroBusca.addEventListener('input', renderTabela);
  els.filtroDivergentes.addEventListener('change', renderTabela);
  els.tabela.querySelector('thead').addEventListener('click', onSortClick);
}

async function init() {
  const response = await fetch('data.json');
  const data = await response.json();
  state.registros = data.registros;
  renderKpis(data.metadata);
  populateFiltros(state.registros);
  wireEvents();
  renderTabela();
}

init();
```

- [ ] **Step 2: Serve the page locally and verify in a browser**

Run: `python -m http.server 8000` (from the project root)
Open: `http://localhost:8000/index.html`

Verify manually:
- KPI cards show non-zero numbers matching the `build_data.py` output from Task 6.
- The UO dropdown lists codes with names, sorted; selecting one filters the table.
- The Fonte dropdown lists codes (with names where available); selecting one filters the table.
- Combining UO + Fonte filters narrows results further.
- The "Buscar" text field filters by typed text across UO/Fonte/names.
- The "Mostrar só divergências" checkbox restricts to `status === 'Divergente'` rows.
- Clicking a column header sorts by that column; clicking again reverses the order.
- Values are formatted as R$ with Brazilian thousands/decimal separators.
- Stop the server with Ctrl+C when done.

- [ ] **Step 3: Commit**

```bash
git add app.js
git commit -m "Add frontend rendering, filtering and sorting logic"
```

---

### Task 9: Publish to GitHub Pages

**Files:**
- Create: `.nojekyll`
- Create: `.gitignore`

- [ ] **Step 1: Add .nojekyll and a minimal .gitignore**

`.nojekyll`:
```
```
(empty file — its presence is what matters)

`.gitignore`:
```
__pycache__/
*.pyc
```

- [ ] **Step 2: Commit**

```bash
git add .nojekyll .gitignore
git commit -m "Add .nojekyll for GitHub Pages and ignore Python cache files"
```

- [ ] **Step 3: Create the GitHub repository and push**

Ask the user for their GitHub username and desired repository name (or confirm they want to run this step themselves). Then, using the `gh` CLI if available:

```bash
gh repo create <owner>/<repo> --public --source=. --remote=origin --push
```

If `gh` is not authenticated/available, give the user these manual steps instead:
1. Go to https://github.com/new, create a public repository (no README/gitignore/license — this repo already has its own history).
2. Run:
```bash
git remote add origin https://github.com/<owner>/<repo>.git
git branch -M main
git push -u origin main
```

- [ ] **Step 4: Enable GitHub Pages**

Tell the user: in the repository on GitHub, go to Settings → Pages → Build and deployment → Source: "Deploy from a branch" → Branch: `main` / `/ (root)` → Save. GitHub will publish the site at `https://<owner>.github.io/<repo>/` within a minute or two.

- [ ] **Step 5: Verify the live site**

Ask the user to open the published URL and confirm the KPI cards, filters, and table all render with real data (same checks as Task 8 Step 2, but on the live GitHub Pages URL).

---

## Updating the dashboard later

When any of the 3 source CSVs changes:
```bash
python build_data.py
git add Despesa_Orcamentaria_Fiscal_2027.csv Orcamento_Receita.csv repasse-recurso.csv data.json
git commit -m "Update source data and regenerate data.json"
git push
```
GitHub Pages republishes automatically within a minute or two of the push.
