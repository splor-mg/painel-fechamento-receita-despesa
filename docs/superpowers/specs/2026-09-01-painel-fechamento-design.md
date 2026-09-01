# Painel de Fechamento Receita x Despesa — Design

## Contexto e objetivo

A CAMG precisa conferir, por Unidade Orçamentária (UO) e Fonte de Recursos, se o
orçamento de despesa proposto para 2027 está batendo com o orçamento de receita
previsto (LOA), considerando também os repasses de recursos entre UOs.

A regra de conferência, por UO+Fonte, é:

```
Valor Proposto Ano (despesa) + Valor Repassado (saída, UO como Cedente)
    = Valor LOA (receita prevista) + Valor Recebido (entrada, UO como Beneficiada)
```

Quando a igualdade não se verifica exatamente, há uma divergência que precisa ser
identificada e investigada.

## Fontes de dados

Três CSVs, sempre no mesmo layout, `;` como separador, BOM UTF-8, ano fiscal 2027:

1. **Despesa_Orcamentaria_Fiscal_2027.csv** (~8.350 linhas)
   - Colunas usadas: `Unidade Orçamentária`, `Nome da UO`, `Fonte de Recursos`,
     `Valor Proposto Ano` (formato `"1000000,00"`, vírgula decimal, entre aspas).
2. **Orcamento_Receita.csv** (~1.426 linhas)
   - Colunas usadas: `Unidade Orçamentária`, `Nome da UO`, `Fonte`, `Valor LOA`
     (inteiro, sem separador decimal).
3. **repasse-recurso.csv** (~28 linhas)
   - Colunas usadas: `U.O. Cedente`, `Nome da U.O. Cedente`, `U.O. Beneficiada`,
     `Nome U.O. Beneficiada`, `Fonte`, `Nome da Fonte`, `Valor Repassado`.
   - Semântica: a UO Cedente "manda" o valor para a UO Beneficiada. Se X repassou
     100 para Y, X tem 100 de **saída** e Y tem 100 de **entrada**, na mesma Fonte.

Nota: a planilha de Despesa também tem uma coluna `Órgão` (nível mais agregado,
31 valores distintos) além de `Unidade Orçamentária` (nível mais granular, 93
valores distintos, mesma granularidade usada em Receita e Repasse). A conferência
usa **Unidade Orçamentária** em todas as três planilhas, para não mascarar
divergências entre UOs de um mesmo Órgão.

Nomes de Fonte só existem na planilha de Repasse (cobre ~8 códigos); nos demais
casos exibimos apenas o código da Fonte.

## Pipeline de dados (`build_data.py`)

Script Python, sem dependências externas além da lib padrão (`csv`, `json`,
`decimal`), executado manualmente quando os CSVs são atualizados:

1. Lê os 3 CSVs (parseando `;`, BOM, e vírgula decimal → `Decimal`).
2. Agrupa Despesa por (UO, Fonte), somando `Valor Proposto Ano`.
3. Agrupa Receita por (UO, Fonte), somando `Valor LOA`.
4. Agrupa Repasse duas vezes: saída por (UO Cedente, Fonte) e entrada por
   (UO Beneficiada, Fonte), somando `Valor Repassado`.
5. Monta a união de todas as chaves (UO, Fonte) que aparecem em qualquer uma
   das quatro agregações acima; chaves ausentes em alguma agregação entram
   com valor 0.
6. Para cada chave (UO, Fonte), calcula:
   - `lado_despesa = valor_despesa + valor_repassado_saida`
   - `lado_receita = valor_loa + valor_repassado_entrada`
   - `diferenca = lado_despesa - lado_receita`
   - `status = "OK"` se `diferenca == 0`, senão `"Divergente"`
7. Resolve nome/sigla da UO (a partir de Despesa/Receita) e nome da Fonte
   (a partir de Repasse, quando existir).
8. Escreve `data.json` com a lista de registros e um bloco de metadados
   (data de geração, totais agregados para os KPIs).

Critério de "bate": igualdade exata (diferença = 0), sem tolerância de
arredondamento.

## Interface web (`index.html` + `app.js` + `style.css`)

Página única, sem framework, carrega `data.json` via `fetch`.

- **KPIs no topo**: nº de combinações UO+Fonte, nº/percentual OK vs Divergente,
  soma dos valores absolutos das divergências.
- **Filtros**: dois campos de seleção (dropdown) dedicados — **UO** e **Fonte**
  — combináveis entre si (ex.: filtrar só por UO, só por Fonte, ou os dois ao
  mesmo tempo), mais busca por texto livre e um toggle "mostrar só
  divergências". (Filtro por Órgão fica fora de escopo desta versão: a
  conferência é 100% baseada em UO, e Órgão só existe na planilha de Despesa,
  o que deixaria o filtro incompleto para UOs vindas só de Receita/Repasse.)
- **Tabela principal**, uma linha por UO+Fonte, colunas: UO (código + nome),
  Fonte (código + nome, se disponível), Valor Proposto Ano, Valor Repassado
  (saída), Valor LOA, Valor Recebido (entrada), Diferença, Status (badge
  verde=OK / vermelho=Divergente). Ordenável por qualquer coluna.
- Valores formatados em R$, padrão brasileiro (milhar com ponto, decimal com
  vírgula).

## Deploy

Repositório Git público, publicado via GitHub Pages (branch principal). Conteúdo
do repositório: os 3 CSVs de origem, `build_data.py`, `data.json` (gerado),
`index.html`, `app.js`, `style.css`.

Fluxo de atualização quando novas versões dos CSVs chegarem:
1. Substituir os CSVs no repositório.
2. Rodar `python build_data.py` para regenerar `data.json`.
3. `git add`, `git commit`, `git push` — o GitHub Pages republica automaticamente.

## Fora de escopo (por ora)

- Gráficos (ex.: divergências por Órgão) — não incluídos nesta primeira versão,
  só tabela + KPIs.
- Tolerância de arredondamento na conferência.
- Autenticação/controle de acesso (o site fica público, sem dados sensíveis
  além do orçamento público do estado).
