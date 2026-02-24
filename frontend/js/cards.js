/* PATSTAT Explorer — Landing Page Card Grid */

document.addEventListener('DOMContentLoaded', async () => {
  const data = await loadQueries();
  const { queries, meta } = data;

  const grid = document.getElementById('query-grid');
  const searchInput = document.getElementById('search');
  const categoriesEl = document.getElementById('categories');
  const tagsEl = document.getElementById('tags');
  const countEl = document.getElementById('query-count');

  let activeCategory = null;
  let activeTags = new Set();

  // Render category filter pills
  meta.categories.forEach(cat => {
    const pill = document.createElement('button');
    pill.className = 'pill';
    pill.dataset.category = cat;
    pill.textContent = cat;
    pill.addEventListener('click', () => {
      if (activeCategory === cat) {
        activeCategory = null;
        pill.classList.remove('active');
      } else {
        categoriesEl.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
        activeCategory = cat;
        pill.classList.add('active');
      }
      renderCards();
    });
    categoriesEl.appendChild(pill);
  });

  // Render stakeholder tag pills
  meta.stakeholder_tags.forEach(tag => {
    const pill = document.createElement('button');
    pill.className = 'pill';
    pill.textContent = tag;
    pill.addEventListener('click', () => {
      if (activeTags.has(tag)) {
        activeTags.delete(tag);
        pill.classList.remove('active');
      } else {
        activeTags.add(tag);
        pill.classList.add('active');
      }
      renderCards();
    });
    tagsEl.appendChild(pill);
  });

  // Search with debounce
  searchInput.addEventListener('input', debounce(renderCards, 200));

  function renderCards() {
    const search = searchInput.value.toLowerCase().trim();
    const queryList = Object.values(queries);

    const filtered = queryList.filter(q => {
      if (activeCategory && q.category !== activeCategory) return false;
      if (activeTags.size > 0 && !q.tags.some(t => activeTags.has(t))) return false;
      if (search) {
        const haystack = `${q.id} ${q.title} ${q.description} ${q.category} ${q.tags.join(' ')}`.toLowerCase();
        return haystack.includes(search);
      }
      return true;
    });

    // Natural sort by query ID number
    filtered.sort((a, b) => {
      const numA = parseInt(a.id.replace(/\D/g, ''), 10);
      const numB = parseInt(b.id.replace(/\D/g, ''), 10);
      return numA - numB;
    });

    countEl.textContent = `${filtered.length} ${filtered.length === 1 ? 'query' : 'queries'}`;

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <h3>No queries found</h3>
          <p>Try adjusting your search or filters</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = filtered.map(q => `
      <a href="/query.html?id=${q.id}" class="query-card">
        <div class="card-header">
          ${renderCategoryBadge(q.category)}
          <span class="card-id">${q.id}</span>
        </div>
        <h3>${escapeHtml(q.title)}</h3>
        <p class="card-description">${escapeHtml(q.description)}</p>
        <div class="card-footer">
          <div class="card-tags">
            ${q.tags.map(renderTag).join('')}
            ${q.platforms.includes('tip') ? '<span class="tag tag-tip">TIP</span>' : ''}
          </div>
          <span class="card-arrow">&rarr;</span>
        </div>
      </a>
    `).join('');
  }

  renderCards();
});
