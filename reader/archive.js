/* The collection can be explored by reading cycle without changing its lead study. */
(() => {
  'use strict';
  const year = document.querySelector('#cycle-year');
  if (!year) return;
  const search = document.querySelector('#search');
  const category = document.querySelector('#category');
  const cards = [...document.querySelectorAll('.edition-card')];
  const count = document.querySelector('.collection-count');
  const empty = document.querySelector('#no-results');
  const status = document.querySelector('#search-status');
  const normalize = text => text.normalize('NFKD').replace(/[\u0591-\u05c7]/g, '').toLowerCase();
  const url = new URL(location.href);
  const requested = url.searchParams.get('year');
  const choices = new Set([...year.options].map(option => option.value));
  year.value = choices.has(requested) ? requested : year.dataset.defaultYear;
  function filter() {
    const tokens = normalize(search.value).split(/\s+/).filter(Boolean);
    let found = 0;
    for (const card of cards) {
      const shown = (year.value === 'all' || card.dataset.cycleYear === year.value)
        && (category.value === 'all' || card.dataset.category === category.value)
        && tokens.every(token => normalize(card.dataset.search || '').includes(token));
      card.hidden = !shown;
      if (shown) found++;
    }
    if (empty) empty.hidden = found !== 0;
    const english = `${found} ${found === 1 ? 'study' : 'studies'} · ${year.value === 'all' ? 'All cycles' : year.value}`;
    const hebrew = `${found} שיעורים · ${year.value === 'all' ? 'כל המחזורים' : year.value}`;
    if (count) {
      count.querySelector('.l-en').textContent = english;
      count.querySelector('.l-he').textContent = hebrew;
    }
    if (status) status.textContent = document.documentElement.dataset.mode === 'he' ? hebrew : english;
  }
  year.addEventListener('change', () => {
    const current = new URL(location.href);
    current.searchParams.set('year', year.value);
    history.replaceState(null, '', current);
    filter();
  });
  search.addEventListener('input', filter);
  category.addEventListener('change', filter);
  document.querySelectorAll('[data-mode-set]').forEach(button => button.addEventListener('click', filter));
  window.addEventListener('pageshow', filter);
  filter();
})();
