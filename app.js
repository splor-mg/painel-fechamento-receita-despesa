const formatterBRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

function formatBRL(value) {
  return formatterBRL.format(Number(value));
}

function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = String(value);
  return div.innerHTML;
}

function uniqueSorted(values) {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b, 'pt-BR', { numeric: true }));
}

function sumBy(registros, key) {
  return registros.reduce((total, r) => total + Number(r[key]), 0);
}

const erroEl = document.getElementById('erro-carregamento');

function mostrarErro(mensagem) {
  erroEl.textContent = mensagem;
  erroEl.hidden = false;
}

/**
 * Generic controller for one tab: KPI cards, any number of dropdown
 * filters, free-text search, an optional divergences-only toggle, a
 * sortable table and a filtered-totals footer row.
 *
 * opts.dropdownFilters: [{ key, el, label(record) }, ...]
 */
function createTabController(opts) {
  const state = { registros: [], sortKey: opts.defaultSortKey, sortDir: 1 };

  function populateFiltros(registros) {
    for (const filtro of opts.dropdownFilters) {
      const primeiroRegistroPorValor = new Map();
      for (const r of registros) {
        const valor = r[filtro.key];
        if (!primeiroRegistroPorValor.has(valor)) {
          primeiroRegistroPorValor.set(valor, r);
        }
      }
      const valores = uniqueSorted(Array.from(primeiroRegistroPorValor.keys()));
      const frag = document.createDocumentFragment();
      for (const valor of valores) {
        const option = document.createElement('option');
        option.value = valor;
        option.textContent = filtro.label(primeiroRegistroPorValor.get(valor));
        frag.appendChild(option);
      }
      filtro.el.appendChild(frag);
    }
  }

  function renderKpis(metadata) {
    for (const { key, el, format } of opts.kpiFields) {
      el.textContent = format ? format(metadata[key]) : metadata[key];
    }
  }

  function getFiltered() {
    const busca = opts.els.filtroBusca.value.trim().toLowerCase();
    const soDivergentes = opts.els.filtroDivergentes ? opts.els.filtroDivergentes.checked : false;

    return state.registros.filter((r) => {
      for (const filtro of opts.dropdownFilters) {
        const valor = filtro.el.value;
        if (valor && r[filtro.key] !== valor) return false;
      }
      if (soDivergentes && r.status !== 'Divergente') return false;
      if (busca) {
        const haystack = opts.searchFields.map((f) => r[f]).join(' ').toLowerCase();
        if (!haystack.includes(busca)) return false;
      }
      return true;
    });
  }

  function getSorted(registros) {
    const { sortKey, sortDir } = state;
    return [...registros].sort((a, b) => {
      let va = a[sortKey];
      let vb = b[sortKey];
      if (opts.numericSortKeys.has(sortKey)) {
        va = Number(va);
        vb = Number(vb);
        return (va - vb) * sortDir;
      }
      return String(va).localeCompare(String(vb), 'pt-BR', { numeric: true }) * sortDir;
    });
  }

  function renderTotais(filtrados) {
    for (const { key, el } of opts.sumFields) {
      el.textContent = formatBRL(sumBy(filtrados, key));
    }
  }

  function renderTabela() {
    const filtrados = getSorted(getFiltered());
    opts.els.tabelaCorpo.innerHTML = '';

    if (filtrados.length === 0) {
      opts.els.tabela.hidden = true;
      opts.els.tabelaVazia.hidden = false;
      return;
    }

    opts.els.tabela.hidden = false;
    opts.els.tabelaVazia.hidden = true;
    renderTotais(filtrados);

    const frag = document.createDocumentFragment();
    for (const r of filtrados) {
      const tr = document.createElement('tr');
      tr.innerHTML = opts.rowTemplate(r);
      frag.appendChild(tr);
    }
    opts.els.tabelaCorpo.appendChild(frag);
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
    for (const filtro of opts.dropdownFilters) {
      filtro.el.addEventListener('change', renderTabela);
    }
    opts.els.filtroBusca.addEventListener('input', renderTabela);
    if (opts.els.filtroDivergentes) {
      opts.els.filtroDivergentes.addEventListener('change', renderTabela);
    }
    opts.els.tabela.querySelector('thead').addEventListener('click', onSortClick);
  }

  return {
    load(data) {
      state.registros = data.registros;
      renderKpis(data.metadata);
      populateFiltros(state.registros);
      wireEvents();
      renderTabela();
    },
  };
}

const receitaDespesaController = createTabController({
  els: {
    filtroBusca: document.getElementById('filtro-busca'),
    filtroDivergentes: document.getElementById('filtro-divergentes'),
    tabelaCorpo: document.getElementById('tabela-corpo'),
    tabelaVazia: document.getElementById('tabela-vazia'),
    tabela: document.getElementById('tabela-reconciliacao'),
  },
  kpiFields: [
    { key: 'total_combinacoes', el: document.getElementById('kpi-total') },
    { key: 'total_ok', el: document.getElementById('kpi-ok') },
    { key: 'total_divergente', el: document.getElementById('kpi-divergente') },
    { key: 'soma_divergencias_abs', el: document.getElementById('kpi-soma-divergencias'), format: formatBRL },
  ],
  defaultSortKey: 'uo',
  dropdownFilters: [
    { key: 'uo', el: document.getElementById('filtro-uo'), label: (r) => (r.sigla_uo ? `${r.uo} - ${r.sigla_uo}` : r.uo) },
    { key: 'fonte', el: document.getElementById('filtro-fonte'), label: (r) => (r.nome_fonte ? `${r.fonte} - ${r.nome_fonte}` : r.fonte) },
  ],
  searchFields: ['uo', 'nome_uo', 'sigla_uo', 'fonte', 'nome_fonte'],
  numericSortKeys: new Set(['valor_despesa', 'valor_repassado_saida', 'valor_loa', 'valor_repassado_entrada', 'diferenca']),
  sumFields: [
    { key: 'valor_loa', el: document.getElementById('total-loa') },
    { key: 'valor_repassado_entrada', el: document.getElementById('total-entrada') },
    { key: 'valor_despesa', el: document.getElementById('total-despesa') },
    { key: 'valor_repassado_saida', el: document.getElementById('total-saida') },
    { key: 'diferenca', el: document.getElementById('total-diferenca') },
  ],
  rowTemplate: (r) => {
    const uoLabel = escapeHtml(r.uo) + (r.sigla_uo ? ` - ${escapeHtml(r.sigla_uo)}` : '');
    const fonteLabel = escapeHtml(r.fonte) + (r.nome_fonte ? ` - ${escapeHtml(r.nome_fonte)}` : '');
    const statusClass = r.status === 'OK' ? 'status-ok' : 'status-divergente';
    return `
      <td>${uoLabel}</td>
      <td>${fonteLabel}</td>
      <td>${formatBRL(r.valor_loa)}</td>
      <td>${formatBRL(r.valor_repassado_entrada)}</td>
      <td>${formatBRL(r.valor_despesa)}</td>
      <td>${formatBRL(r.valor_repassado_saida)}</td>
      <td>${formatBRL(r.diferenca)}</td>
      <td><span class="status-badge ${statusClass}">${escapeHtml(r.status)}</span></td>
    `;
  },
});

const intraPatronalController = createTabController({
  els: {
    filtroBusca: document.getElementById('intra-filtro-busca'),
    filtroDivergentes: document.getElementById('intra-filtro-divergentes'),
    tabelaCorpo: document.getElementById('intra-tabela-corpo'),
    tabelaVazia: document.getElementById('intra-tabela-vazia'),
    tabela: document.getElementById('intra-tabela'),
  },
  kpiFields: [
    { key: 'total_combinacoes', el: document.getElementById('intra-kpi-total') },
    { key: 'total_ok', el: document.getElementById('intra-kpi-ok') },
    { key: 'total_divergente', el: document.getElementById('intra-kpi-divergente') },
    { key: 'soma_divergencias_abs', el: document.getElementById('intra-kpi-soma-divergencias'), format: formatBRL },
  ],
  defaultSortKey: 'uo',
  dropdownFilters: [
    { key: 'uo', el: document.getElementById('intra-filtro-uo'), label: (r) => (r.sigla_uo ? `${r.uo} - ${r.sigla_uo}` : r.uo) },
    { key: 'credor', el: document.getElementById('intra-filtro-credor'), label: (r) => r.credor },
  ],
  searchFields: ['uo', 'sigla_uo', 'credor'],
  numericSortKeys: new Set(['valor_projetado', 'valor_repassado', 'diferenca']),
  sumFields: [
    { key: 'valor_projetado', el: document.getElementById('intra-total-projetado') },
    { key: 'valor_repassado', el: document.getElementById('intra-total-repassado') },
    { key: 'diferenca', el: document.getElementById('intra-total-diferenca') },
  ],
  rowTemplate: (r) => {
    const uoLabel = escapeHtml(r.uo) + (r.sigla_uo ? ` - ${escapeHtml(r.sigla_uo)}` : '');
    const statusClass = r.status === 'OK' ? 'status-ok' : 'status-divergente';
    return `
      <td>${uoLabel}</td>
      <td>${escapeHtml(r.credor)}</td>
      <td>${formatBRL(r.valor_projetado)}</td>
      <td>${formatBRL(r.valor_repassado)}</td>
      <td>${formatBRL(r.diferenca)}</td>
      <td><span class="status-badge ${statusClass}">${escapeHtml(r.status)}</span></td>
    `;
  },
});

const despesaDetalhadaController = createTabController({
  els: {
    filtroBusca: document.getElementById('detalhada-filtro-busca'),
    tabelaCorpo: document.getElementById('detalhada-tabela-corpo'),
    tabelaVazia: document.getElementById('detalhada-tabela-vazia'),
    tabela: document.getElementById('detalhada-tabela'),
  },
  kpiFields: [
    { key: 'total_registros', el: document.getElementById('detalhada-kpi-total') },
    { key: 'valor_total', el: document.getElementById('detalhada-kpi-valor-total'), format: formatBRL },
  ],
  defaultSortKey: 'uo',
  dropdownFilters: [
    { key: 'uo', el: document.getElementById('detalhada-filtro-uo'), label: (r) => (r.sigla_uo ? `${r.uo} - ${r.sigla_uo}` : r.uo) },
    { key: 'fonte', el: document.getElementById('detalhada-filtro-fonte'), label: (r) => r.fonte },
    { key: 'grupo', el: document.getElementById('detalhada-filtro-grupo'), label: (r) => r.grupo },
    { key: 'elemento', el: document.getElementById('detalhada-filtro-elemento'), label: (r) => r.elemento },
    { key: 'item', el: document.getElementById('detalhada-filtro-item'), label: (r) => r.item },
    { key: 'ipu', el: document.getElementById('detalhada-filtro-ipu'), label: (r) => r.ipu },
    { key: 'acao', el: document.getElementById('detalhada-filtro-acao'), label: (r) => (r.nome_acao ? `${r.acao} - ${r.nome_acao}` : r.acao) },
  ],
  searchFields: ['uo', 'nome_uo', 'sigla_uo', 'funcao', 'acao', 'nome_acao', 'grupo', 'modalidade', 'elemento', 'item', 'fonte', 'ipu'],
  numericSortKeys: new Set(['valor']),
  sumFields: [
    { key: 'valor', el: document.getElementById('detalhada-total-valor') },
  ],
  rowTemplate: (r) => {
    const uoLabel = escapeHtml(r.uo) + (r.sigla_uo ? ` - ${escapeHtml(r.sigla_uo)}` : '');
    const acaoLabel = escapeHtml(r.acao) + (r.nome_acao ? ` - ${escapeHtml(r.nome_acao)}` : '');
    return `
      <td>${uoLabel}</td>
      <td>${escapeHtml(r.funcao)}</td>
      <td>${acaoLabel}</td>
      <td>${escapeHtml(r.grupo)}</td>
      <td>${escapeHtml(r.modalidade)}</td>
      <td>${escapeHtml(r.elemento)}</td>
      <td>${escapeHtml(r.item)}</td>
      <td>${escapeHtml(r.fonte)}</td>
      <td>${escapeHtml(r.ipu)}</td>
      <td>${formatBRL(r.valor)}</td>
    `;
  },
});

function updateTabsHeightVar() {
  const tabsEl = document.querySelector('.tabs');
  if (tabsEl) {
    document.documentElement.style.setProperty('--tabs-height', `${tabsEl.offsetHeight}px`);
  }
}

function wireTabs() {
  updateTabsHeightVar();
  window.addEventListener('resize', updateTabsHeightVar);

  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      buttons.forEach((b) => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');

      document.querySelectorAll('.view').forEach((view) => {
        view.hidden = true;
      });
      const target = document.getElementById(btn.getAttribute('aria-controls'));
      target.hidden = false;
    });
  });
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} ao buscar ${url}`);
  }
  return response.json();
}

async function init() {
  wireTabs();

  const geradoEmEl = document.getElementById('gerado-em');
  const erros = [];

  try {
    const data = await fetchJson('data.json');
    receitaDespesaController.load(data);
    if (data.metadata.gerado_em) {
      geradoEmEl.textContent = `Gerado em ${new Date(data.metadata.gerado_em).toLocaleString('pt-BR')}`;
    }
  } catch (err) {
    erros.push(`Fechamento Receita x Despesa (data.json): ${err.message}`);
  }

  try {
    const data = await fetchJson('data_intra_patronal.json');
    intraPatronalController.load(data);
  } catch (err) {
    erros.push(`Despesa Intraorçamentária (data_intra_patronal.json): ${err.message}`);
  }

  try {
    const data = await fetchJson('data_despesa_detalhada.json');
    despesaDetalhadaController.load(data);
  } catch (err) {
    erros.push(`Despesa Detalhada (data_despesa_detalhada.json): ${err.message}`);
  }

  if (erros.length > 0) {
    mostrarErro(`Não foi possível carregar todos os dados: ${erros.join(' | ')}`);
  }
}

init();
