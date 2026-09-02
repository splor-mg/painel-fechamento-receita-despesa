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
