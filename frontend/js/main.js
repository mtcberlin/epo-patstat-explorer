/* PATSTAT Explorer — Shared Utilities */

// In production, nginx proxies /api/ to the backend.
// For local dev, point directly to the FastAPI server.
const API_BASE = window.location.port === '8080' ? 'http://localhost:8000/api' : '/api';

// ============================================================
// Data Loading
// ============================================================
let _queryData = null;

async function loadQueries() {
  if (_queryData) return _queryData;
  const resp = await fetch('/data/queries.json');
  _queryData = await resp.json();
  return _queryData;
}

// ============================================================
// Rendering Helpers
// ============================================================
function renderTag(tag) {
  return `<span class="tag tag-${tag}">${tag}</span>`;
}

function renderCategoryBadge(category) {
  return `<span class="category-badge category-${category}">${category}</span>`;
}

function formatNumber(n) {
  if (n == null) return '';
  return new Intl.NumberFormat().format(n);
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ============================================================
// SQL Syntax Highlighting
// ============================================================
function highlightSQL(sql) {
  const KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS', 'FULL',
    'ON', 'AND', 'OR', 'NOT', 'IN', 'AS', 'GROUP', 'BY', 'ORDER', 'LIMIT', 'OFFSET',
    'HAVING', 'UNION', 'ALL', 'BETWEEN', 'LIKE', 'IS', 'NULL', 'DISTINCT', 'CASE', 'WHEN',
    'THEN', 'ELSE', 'END', 'WITH', 'OVER', 'PARTITION', 'DESC', 'ASC', 'CAST', 'EXISTS',
    'IF', 'EXCEPT', 'INTERSECT', 'TRUE', 'FALSE', 'CREATE', 'INSERT', 'UPDATE', 'DELETE',
    'SET', 'INTO', 'VALUES', 'TABLE', 'INDEX', 'VIEW', 'TEMP', 'TEMPORARY', 'RECURSIVE',
    'UNNEST', 'ARRAY', 'STRUCT', 'INT64', 'FLOAT64', 'STRING', 'BOOL', 'DATE', 'TIMESTAMP',
    'WINDOW', 'ROWS', 'RANGE', 'UNBOUNDED', 'PRECEDING', 'FOLLOWING', 'CURRENT', 'ROW',
  ];

  const FUNCTIONS = [
    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'CONCAT', 'LENGTH', 'SUBSTR', 'TRIM',
    'UPPER', 'LOWER', 'EXTRACT', 'FORMAT_DATE', 'PARSE_DATE', 'DATE_DIFF', 'CURRENT_DATE',
    'STRING_AGG', 'ARRAY_AGG', 'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'LAG', 'LEAD',
    'FIRST_VALUE', 'LAST_VALUE', 'NTILE', 'SAFE_DIVIDE', 'APPROX_COUNT_DISTINCT',
    'ANY_VALUE', 'COALESCE', 'IFNULL', 'NULLIF', 'COUNTIF', 'ARRAY_LENGTH', 'GENERATE_ARRAY',
    'FORMAT', 'REGEXP_CONTAINS', 'REGEXP_EXTRACT', 'STARTS_WITH', 'ENDS_WITH', 'CONTAINS_SUBSTR',
    'APPROX_QUANTILES', 'FLOOR', 'CEIL', 'CEILING', 'ABS', 'MOD', 'SIGN', 'SQRT', 'POW', 'POWER',
  ];

  // Step 1: Escape HTML
  let html = escapeHtml(sql);

  // Step 2: Extract and protect strings and comments from further processing
  const tokens = [];
  let tokenId = 0;

  // Protect single-quoted strings
  html = html.replace(/'([^']*)'/g, (m) => {
    const id = `__TOK${tokenId++}__`;
    tokens.push({ id, html: `<span class="sql-string">${m}</span>` });
    return id;
  });

  // Protect line comments
  html = html.replace(/--(.*?)$/gm, (m, content) => {
    const id = `__TOK${tokenId++}__`;
    tokens.push({ id, html: `<span class="sql-comment">--${content}</span>` });
    return id;
  });

  // Step 3: Highlight parameters (@param_name) — most important for this app
  html = html.replace(/@(\w+)/g, '<span class="sql-param">@$1</span>');

  // Step 4: Highlight backtick-quoted table/column names
  html = html.replace(/`([^`]*)`/g, '<span class="sql-table">`$1`</span>');

  // Step 5: Highlight keywords (word boundary, case-insensitive)
  for (const kw of KEYWORDS) {
    html = html.replace(new RegExp(`\\b(${kw})\\b`, 'gi'), '<span class="sql-keyword">$1</span>');
  }

  // Step 6: Highlight functions (word followed by parenthesis)
  for (const fn of FUNCTIONS) {
    html = html.replace(new RegExp(`\\b(${fn})(\\s*\\()`, 'gi'), '<span class="sql-function">$1</span>$2');
  }

  // Step 7: Highlight standalone numbers
  html = html.replace(/\b(\d+\.?\d*)\b/g, '<span class="sql-number">$1</span>');

  // Step 8: Restore protected tokens
  for (const tok of tokens) {
    html = html.replace(tok.id, tok.html);
  }

  return html;
}

// ============================================================
// Clipboard
// ============================================================
async function copyToClipboard(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    const original = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => (btn.textContent = original), 1500);
  } catch {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    const original = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => (btn.textContent = original), 1500);
  }
}

// ============================================================
// Debounce
// ============================================================
function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}
