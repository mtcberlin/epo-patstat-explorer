/* PATSTAT Explorer — Query Detail Page */

document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const queryId = urlParams.get('id');

  if (!queryId) { window.location.href = '/'; return; }

  const data = await loadQueries();
  const query = data.queries[queryId];

  if (!query) { window.location.href = '/'; return; }

  // ============================================================
  // Populate page header
  // ============================================================
  document.title = `${queryId}: ${query.title} — PATSTAT Explorer`;
  document.getElementById('query-id').textContent = queryId;
  document.getElementById('query-title').textContent = query.title;
  document.getElementById('query-description').textContent = query.description;

  const metaEl = document.getElementById('query-meta');
  metaEl.innerHTML = [
    renderCategoryBadge(query.category),
    ...query.tags.map(renderTag),
    query.platforms.includes('tip') ? '<span class="tag tag-tip">TIP</span>' : '',
  ].join('');

  // ============================================================
  // Explanation section
  // ============================================================
  const explEl = document.getElementById('query-explanation');
  const lines = query.explanation.split('\n').filter(l => l.trim());
  const listItems = [];
  const paragraphs = [];

  lines.forEach(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ')) {
      listItems.push(trimmed.slice(2));
    } else {
      paragraphs.push(trimmed);
    }
  });

  let explHTML = '<h3>About this query</h3>';
  explHTML += paragraphs.map(p => `<p>${escapeHtml(p)}</p>`).join('');
  if (listItems.length > 0) {
    explHTML += '<ul>' + listItems.map(li => `<li>${escapeHtml(li)}</li>`).join('') + '</ul>';
  }
  if (query.key_outputs.length > 0) {
    explHTML += `
      <div class="key-outputs">
        <p class="key-outputs-title">Key Outputs</p>
        <ul>${query.key_outputs.map(o => `<li>${escapeHtml(o)}</li>`).join('')}</ul>
      </div>
    `;
  }
  explEl.innerHTML = explHTML;

  // ============================================================
  // SQL display with highlighting
  // ============================================================
  const sqlText = query.sql_template || query.sql;
  const sqlCodeEl = document.getElementById('sql-code');
  sqlCodeEl.innerHTML = highlightSQL(sqlText);

  document.getElementById('btn-copy').addEventListener('click', function () {
    copyToClipboard(sqlText, this);
  });

  // ============================================================
  // Timing hint
  // ============================================================
  const timingEl = document.getElementById('timing-hint');
  const firstRun = query.estimated_seconds_first_run;
  const cached = query.estimated_seconds_cached;
  if (firstRun) {
    timingEl.textContent = `~${firstRun}s first run, ~${cached}s cached`;
  }

  // ============================================================
  // Parameters panel
  // ============================================================
  const paramsPanel = document.getElementById('params-panel');
  const paramValues = {};

  if (Object.keys(query.parameters).length > 0) {
    buildParameterControls(query.parameters, paramsPanel, paramValues, data.meta);
  } else {
    paramsPanel.innerHTML += '<p class="params-empty">No parameters for this query</p>';
  }

  // ============================================================
  // Run button
  // ============================================================
  const btnRun = document.getElementById('btn-run');
  const resultsSection = document.getElementById('results');

  btnRun.addEventListener('click', async () => {
    btnRun.disabled = true;
    btnRun.classList.add('loading');
    btnRun.textContent = 'Running';
    resultsSection.className = 'results visible';
    resultsSection.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';

    try {
      const resp = await fetch(`${API_BASE}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_id: queryId, parameters: paramValues }),
      });
      const result = await resp.json();

      if (result.error) {
        resultsSection.innerHTML = `<div class="alert alert-error">${escapeHtml(result.error)}</div>`;
      } else {
        renderResults(result, query, resultsSection);
      }
    } catch (err) {
      resultsSection.innerHTML = `<div class="alert alert-error">Connection error: ${escapeHtml(err.message)}</div>`;
    } finally {
      btnRun.disabled = false;
      btnRun.classList.remove('loading');
      btnRun.textContent = 'Run Query';
    }
  });
});

// ============================================================
// Parameter Controls Builder
// ============================================================
function buildParameterControls(params, container, paramValues, meta) {
  for (const [name, param] of Object.entries(params)) {
    const group = document.createElement('div');
    group.className = 'param-group';

    const label = document.createElement('label');
    label.textContent = param.label || name;
    group.appendChild(label);

    switch (param.type) {
      case 'year_range':
        buildYearRange(group, param, paramValues);
        break;
      case 'multiselect':
        buildMultiselect(group, name, param, paramValues);
        break;
      case 'select':
        buildSelect(group, name, param, paramValues);
        break;
      case 'text':
        buildTextInput(group, name, param, paramValues);
        break;
    }

    container.appendChild(group);
  }
}

function buildYearRange(group, param, paramValues) {
  paramValues.year_start = param.default_start;
  paramValues.year_end = param.default_end;

  const valuesEl = document.createElement('div');
  valuesEl.className = 'range-values';
  valuesEl.innerHTML = `<span>${param.default_start}</span><span>${param.default_end}</span>`;

  // From slider
  const fromRow = document.createElement('div');
  fromRow.className = 'range-row';
  fromRow.innerHTML = '<span class="range-label">From</span>';
  const fromInput = document.createElement('input');
  fromInput.type = 'range';
  fromInput.min = 1782;
  fromInput.max = 2024;
  fromInput.value = param.default_start;
  fromInput.addEventListener('input', () => {
    paramValues.year_start = parseInt(fromInput.value, 10);
    valuesEl.querySelector('span:first-child').textContent = fromInput.value;
  });
  fromRow.appendChild(fromInput);

  // To slider
  const toRow = document.createElement('div');
  toRow.className = 'range-row';
  toRow.innerHTML = '<span class="range-label">To</span>';
  const toInput = document.createElement('input');
  toInput.type = 'range';
  toInput.min = 1782;
  toInput.max = 2024;
  toInput.value = param.default_end;
  toInput.addEventListener('input', () => {
    paramValues.year_end = parseInt(toInput.value, 10);
    valuesEl.querySelector('span:last-child').textContent = toInput.value;
  });
  toRow.appendChild(toInput);

  group.appendChild(fromRow);
  group.appendChild(toRow);
  group.appendChild(valuesEl);
}

function buildMultiselect(group, name, param, paramValues) {
  const options = param.options || [];
  const defaults = param.defaults || [];
  paramValues[name] = [...defaults];

  const container = document.createElement('div');
  container.className = 'multiselect-container';

  options.forEach(opt => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `multiselect-option${defaults.includes(opt) ? ' selected' : ''}`;
    btn.textContent = opt;
    btn.addEventListener('click', () => {
      btn.classList.toggle('selected');
      if (paramValues[name].includes(opt)) {
        paramValues[name] = paramValues[name].filter(v => v !== opt);
      } else {
        paramValues[name].push(opt);
      }
    });
    container.appendChild(btn);
  });

  group.appendChild(container);
}

function buildSelect(group, name, param, paramValues) {
  paramValues[name] = param.defaults;
  const select = document.createElement('select');

  (param.options || []).forEach(opt => {
    const option = document.createElement('option');
    option.value = opt;
    option.textContent = opt;
    if (String(opt) === String(param.defaults)) option.selected = true;
    select.appendChild(option);
  });

  select.addEventListener('change', () => {
    paramValues[name] = select.value;
  });
  group.appendChild(select);
}

function buildTextInput(group, name, param, paramValues) {
  paramValues[name] = param.defaults || '';
  const input = document.createElement('input');
  input.type = 'text';
  input.value = param.defaults || '';
  input.placeholder = param.placeholder || '';
  input.addEventListener('input', () => {
    paramValues[name] = input.value;
  });
  group.appendChild(input);
}

// ============================================================
// Results Renderer
// ============================================================
function renderResults(result, query, container) {
  const { data: rows, columns, execution_time, row_count } = result;

  let html = `
    <div class="results-header">
      <h2>Results</h2>
      <span class="results-meta">${formatNumber(row_count)} rows &middot; ${execution_time}s</span>
    </div>
  `;

  // Metrics grid display (e.g., Q01)
  if (query.display_mode === 'metrics_grid' && rows.length > 0 && columns.includes('metric') && columns.includes('value')) {
    html += '<div class="metrics-grid">';
    rows.forEach(row => {
      const val = row.value != null ? formatNumber(Number(row.value)) || row.value : '—';
      html += `
        <div class="metric-card">
          <div class="metric-value">${val}</div>
          <div class="metric-label">${escapeHtml(String(row.metric))}</div>
        </div>
      `;
    });
    html += '</div>';
  }

  // Chart
  if (query.visualization && rows.length > 0) {
    html += '<div class="chart-container" id="chart"></div>';
  }

  // Data table
  if (rows.length > 0) {
    const displayRows = rows.slice(0, 200);
    html += `
      <div class="table-container">
        <div class="table-scroll">
          <table class="results-table">
            <thead>
              <tr>${columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>
            </thead>
            <tbody>
              ${displayRows.map(row => `
                <tr>${columns.map(c => {
                  const val = row[c];
                  const isNum = typeof val === 'number';
                  const display = val != null ? (isNum ? formatNumber(val) : escapeHtml(String(val))) : '';
                  return `<td${isNum ? ' class="num"' : ''}>${display}</td>`;
                }).join('')}</tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
    if (row_count > 200) {
      html += `<p style="text-align:center;margin-top:0.75rem;font-size:0.8125rem;color:var(--color-gray-400)">Showing 200 of ${formatNumber(row_count)} rows</p>`;
    }
  }

  container.innerHTML = html;

  // Render chart after DOM update
  if (query.visualization && rows.length > 0) {
    setTimeout(() => renderChart('chart', rows, query.visualization, columns), 50);
  }
}

// ============================================================
// Chart Rendering (ECharts)
// ============================================================
const CHART_COLORS = ['#14b8a6', '#3b82f6', '#f59e0b', '#e63946', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'];

function renderChart(containerId, data, vizConfig, columns) {
  const el = document.getElementById(containerId);
  if (!el || typeof echarts === 'undefined') return;

  const chart = echarts.init(el, null, { renderer: 'canvas' });
  const { x, y, color, type, stacked_columns } = vizConfig;

  const baseTheme = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
    textStyle: { fontFamily: 'Inter, sans-serif' },
  };

  let option;

  switch (type) {
    case 'bar':
      option = buildBarChart(data, x, y, color, baseTheme);
      break;
    case 'line':
      option = buildLineChart(data, x, y, color, baseTheme);
      break;
    case 'pie':
      option = buildPieChart(data, x, y);
      break;
    case 'stacked_bar':
      option = buildStackedBarChart(data, x, y, color, stacked_columns, baseTheme);
      break;
    default:
      option = buildBarChart(data, x, y, color, baseTheme);
  }

  if (option) {
    chart.setOption(option);
    window.addEventListener('resize', () => chart.resize());
  }
}

function buildBarChart(data, x, y, color, base) {
  if (color) {
    // Grouped/colored bars
    const groups = [...new Set(data.map(d => d[color]))];
    const categories = [...new Set(data.map(d => d[x]))];
    return {
      ...base,
      legend: { data: groups, bottom: 0 },
      xAxis: { type: 'category', data: categories, axisLabel: { rotate: 45, interval: 0, fontSize: 11 } },
      yAxis: { type: 'value' },
      series: groups.map((g, i) => ({
        name: g,
        type: 'bar',
        data: categories.map(cat => {
          const row = data.find(d => d[x] === cat && d[color] === g);
          return row ? row[y] : 0;
        }),
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
        barMaxWidth: 40,
      })),
    };
  }
  return {
    ...base,
    xAxis: { type: 'category', data: data.map(d => d[x]), axisLabel: { rotate: data.length > 10 ? 45 : 0, interval: 0, fontSize: 11 } },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: data.map(d => d[y]), itemStyle: { color: CHART_COLORS[0] }, barMaxWidth: 50 }],
  };
}

function buildLineChart(data, x, y, color, base) {
  if (color) {
    const groups = [...new Set(data.map(d => d[color]))];
    const categories = [...new Set(data.map(d => d[x]))];
    return {
      ...base,
      legend: { data: groups, bottom: 0 },
      xAxis: { type: 'category', data: categories },
      yAxis: { type: 'value' },
      series: groups.map((g, i) => ({
        name: g,
        type: 'line',
        smooth: true,
        data: categories.map(cat => {
          const row = data.find(d => d[x] === cat && d[color] === g);
          return row ? row[y] : 0;
        }),
        lineStyle: { color: CHART_COLORS[i % CHART_COLORS.length], width: 2 },
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
      })),
    };
  }
  return {
    ...base,
    xAxis: { type: 'category', data: data.map(d => d[x]) },
    yAxis: { type: 'value' },
    series: [{
      type: 'line',
      smooth: true,
      data: data.map(d => d[y]),
      lineStyle: { color: CHART_COLORS[0], width: 2 },
      itemStyle: { color: CHART_COLORS[0] },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(20,184,166,0.2)' }, { offset: 1, color: 'rgba(20,184,166,0)' }] } },
    }],
  };
}

function buildPieChart(data, x, y) {
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {d}%' },
      data: data.map((d, i) => ({
        name: d[x],
        value: d[y],
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
      })),
    }],
  };
}

function buildStackedBarChart(data, x, y, color, stacked_columns, base) {
  const categories = [...new Set(data.map(d => d[x]))];

  // Wide format: stacked_columns are actual column names in the data
  if (stacked_columns && stacked_columns.length > 0 && data.length > 0 && stacked_columns[0] in data[0]) {
    return {
      ...base,
      legend: { data: stacked_columns, bottom: 0 },
      xAxis: { type: 'category', data: categories, axisLabel: { rotate: categories.length > 10 ? 45 : 0, fontSize: 11 } },
      yAxis: { type: 'value' },
      series: stacked_columns.map((col, i) => ({
        name: col,
        type: 'bar',
        stack: 'total',
        data: categories.map(cat => {
          const row = data.find(d => d[x] === cat);
          return row ? row[col] : 0;
        }),
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
      })),
    };
  }

  // Long format: group by color column
  if (color) {
    const seriesNames = stacked_columns || [...new Set(data.map(d => d[color]))];
    return {
      ...base,
      legend: { data: seriesNames, bottom: 0 },
      xAxis: { type: 'category', data: categories, axisLabel: { rotate: categories.length > 10 ? 45 : 0, fontSize: 11 } },
      yAxis: { type: 'value' },
      series: seriesNames.map((sn, i) => ({
        name: sn,
        type: 'bar',
        stack: 'total',
        data: categories.map(cat => {
          const row = data.find(d => d[x] === cat && d[color] === sn);
          return row ? row[y] : 0;
        }),
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
      })),
    };
  }

  // Fallback: simple bar
  return buildBarChart(data, x, y, null, base);
}
