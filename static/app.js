/**
 * phone_img_scraper - Minimalist Application Logic with Full Radius & Storage Filters
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const searchForm = document.getElementById('search-form');
  const queryInput = document.getElementById('query-input');
  const clearSearchBtn = document.getElementById('clear-search-btn');
  const searchSubmitBtn = document.getElementById('search-submit-btn');
  const btnText = searchSubmitBtn.querySelector('.btn-text');
  const btnSpinner = searchSubmitBtn.querySelector('.btn-spinner');

  const sourceSelect = document.getElementById('source-select');
  const limitSelect = document.getElementById('limit-select');
  const quickTags = document.getElementById('quick-tags');

  // Site Toggles Registry for Choosing Sites
  const SITE_CONFIGS = [
    { id: 'toggle-ecommerce', value: 'ecommerce', labelId: 'label-toggle-ecommerce', activeClass: 'active-ecommerce', name: 'Amazon & Flipkart' },
    { id: 'toggle-cashify', value: 'cashify', labelId: 'label-toggle-cashify', activeClass: 'active-cashify', name: 'Cashify' },
    { id: 'toggle-fonezone', value: 'fonezone', labelId: 'label-toggle-fonezone', activeClass: 'active-fonezone', name: 'FoneZone' },
    { id: 'toggle-gameloot', value: 'gameloot', labelId: 'label-toggle-gameloot', activeClass: 'active-gameloot', name: 'GameLoot' },
    { id: 'toggle-triveni', value: 'triveniworld', labelId: 'label-toggle-triveni', activeClass: 'active-triveni', name: 'Triveni World' },
    { id: 'toggle-vlebazaar', value: 'vlebazaar', labelId: 'label-toggle-vlebazaar', activeClass: 'active-vlebazaar', name: 'VleBazaar' },
    { id: 'toggle-refurbished', value: 'refurbished', labelId: 'label-toggle-refurbished', activeClass: 'active-refurbished', name: 'All Refurbished Sites' },
    { id: 'toggle-ebay', value: 'ebay', labelId: 'label-toggle-ebay', activeClass: 'active-ebay', name: 'eBay' },
    { id: 'toggle-alamy', value: 'alamy', labelId: 'label-toggle-alamy', activeClass: 'active-alamy', name: 'Alamy' },
    { id: 'toggle-indiamart', value: 'indiamart', labelId: 'label-toggle-indiamart', activeClass: 'active-indiamart', name: 'IndiaMART' },
  ];

  // Sidebar Elements
  const sidebarColorList = document.getElementById('sidebar-color-list');
  const sidebarStorageList = document.getElementById('sidebar-storage-list');
  const sidebarSizeList = document.getElementById('sidebar-size-list');
  const sidebarAngleList = document.getElementById('sidebar-angle-list');
  const resetFiltersBtn = document.getElementById('reset-filters-btn');
  const countColorAll = document.getElementById('count-color-all');
  const sidebarDownloadBox = document.getElementById('sidebar-download-box');
  const downloadZipBtn = document.getElementById('download-zip-btn');
  const zipBtnText = document.getElementById('zip-btn-text');
  const navDownloadZip = document.getElementById('nav-download-zip');

  const statsSection = document.getElementById('stats-section');
  const statCount = document.getElementById('stat-count');
  const statTime = document.getElementById('stat-time');
  const copyAllBtn = document.getElementById('copy-all-btn');
  const toggleGroupByModel = document.getElementById('toggle-group-by-model');
  const labelGroupByModel = document.getElementById('label-group-by-model');

  const loadingState = document.getElementById('loading-state');
  const resultsGrid = document.getElementById('results-grid');
  const emptyState = document.getElementById('empty-state');
  const emptyTitle = document.getElementById('empty-title');
  const emptyMsg = document.getElementById('empty-msg');

  // Modal Elements
  const modal = document.getElementById('lightbox-modal');
  const modalPhoneTitle = document.getElementById('modal-phone-title');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalImg = document.getElementById('modal-img');
  const modalFilenameDisplay = document.getElementById('modal-filename-display');
  const modalAngleBadge = document.getElementById('modal-angle-badge');
  const modalSourceBadge = document.getElementById('modal-source-badge');
  const modalColorBadge = document.getElementById('modal-color-badge');
  const modalStorageBadge = document.getElementById('modal-storage-badge');
  const modalCopyBtn = document.getElementById('modal-copy-btn');
  const modalDownloadSingleBtn = document.getElementById('modal-download-single-btn');
  const modalDownloadSelectedBtn = document.getElementById('modal-download-selected-btn');
  const modalDownloadSelectedText = document.getElementById('modal-download-selected-text');
  const modalSelectedCount = document.getElementById('modal-selected-count');
  const modalSelectAllBtn = document.getElementById('modal-select-all-btn');
  const modalDeselectAllBtn = document.getElementById('modal-deselect-all-btn');
  const modalThumbnailsStrip = document.getElementById('modal-thumbnails-strip');

  const toastContainer = document.getElementById('toast-container');

  // Backend Configuration Elements
  const backendConfigBtn = document.getElementById('backend-config-btn');
  const backendDot = document.getElementById('backend-dot');
  const backendStatusText = document.getElementById('backend-status-text');
  const backendModal = document.getElementById('backend-modal');
  const backendModalBackdrop = document.getElementById('backend-modal-backdrop');
  const backendModalClose = document.getElementById('backend-modal-close');
  const backendUrlInput = document.getElementById('backend-url-input');
  const backendPingResult = document.getElementById('backend-ping-result');
  const backendTestBtn = document.getElementById('backend-test-btn');
  const backendSaveBtn = document.getElementById('backend-save-btn');
  const backendResetBtn = document.getElementById('backend-reset-btn');

  function getApiBaseUrl() {
    const custom = localStorage.getItem('RENDER_BACKEND_URL');
    if (custom && custom.trim()) {
      return custom.trim().replace(/\/+$/, '');
    }
    if (window.RENDER_BACKEND_URL && window.RENDER_BACKEND_URL.trim()) {
      return window.RENDER_BACKEND_URL.trim().replace(/\/+$/, '');
    }
    // If running locally, use relative path so local server handles it
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return '';
    }
    // Production default: connect directly to Render backend (avoids Vercel proxy timeouts)
    return 'https://phone-image-scraper.onrender.com';
  }

  function updateBackendStatusUI() {
    const url = getApiBaseUrl();
    if (!backendStatusText) return;

    if (url) {
      try {
        const host = new URL(url).hostname;
        backendStatusText.textContent = `API: ${host}`;
      } catch {
        backendStatusText.textContent = 'API: Live';
      }
      if (backendDot) {
        backendDot.className = 'backend-dot checking';
      }
      fetch(`${url}/health`, { signal: AbortSignal.timeout ? AbortSignal.timeout(8000) : undefined })
        .then(r => r.json())
        .then(() => {
          if (backendDot) backendDot.className = 'backend-dot';
        })
        .catch(() => {
          if (backendDot) backendDot.className = 'backend-dot offline';
        });
    } else {
      backendStatusText.textContent = 'API: Local';
      if (backendDot) backendDot.className = 'backend-dot';
    }
  }

  if (backendConfigBtn && backendModal) {
    backendConfigBtn.addEventListener('click', () => {
      backendUrlInput.value = localStorage.getItem('RENDER_BACKEND_URL') || '';
      backendPingResult.textContent = '';
      backendPingResult.className = 'backend-ping-result';
      backendModal.style.display = 'flex';
    });

    const closeBackendModal = () => {
      backendModal.style.display = 'none';
    };

    if (backendModalClose) backendModalClose.addEventListener('click', closeBackendModal);
    if (backendModalBackdrop) backendModalBackdrop.addEventListener('click', closeBackendModal);

    if (backendTestBtn) {
      backendTestBtn.addEventListener('click', async () => {
        const targetUrl = (backendUrlInput.value || '').trim().replace(/\/+$/, '');
        if (!targetUrl) {
          backendPingResult.textContent = 'Enter a Render backend URL first.';
          backendPingResult.className = 'backend-ping-result error';
          return;
        }
        backendPingResult.textContent = 'Testing connection...';
        backendPingResult.className = 'backend-ping-result';
        try {
          const res = await fetch(`${targetUrl}/health`, { signal: AbortSignal.timeout ? AbortSignal.timeout(6000) : undefined });
          if (res.ok) {
            backendPingResult.textContent = '✓ Successfully connected to Render backend!';
            backendPingResult.className = 'backend-ping-result success';
          } else {
            backendPingResult.textContent = `Server responded with HTTP ${res.status}`;
            backendPingResult.className = 'backend-ping-result error';
          }
        } catch (e) {
          backendPingResult.textContent = '✕ Could not reach server. Verify URL and ensure service is active.';
          backendPingResult.className = 'backend-ping-result error';
        }
      });
    }

    if (backendSaveBtn) {
      backendSaveBtn.addEventListener('click', () => {
        const targetUrl = (backendUrlInput.value || '').trim().replace(/\/+$/, '');
        if (targetUrl) {
          localStorage.setItem('RENDER_BACKEND_URL', targetUrl);
          showToast('Render Backend URL saved!', 'success');
        } else {
          localStorage.removeItem('RENDER_BACKEND_URL');
          showToast('Reset to Auto/Proxy mode.', 'info');
        }
        updateBackendStatusUI();
        backendModal.style.display = 'none';
      });
    }

    if (backendResetBtn) {
      backendResetBtn.addEventListener('click', () => {
        localStorage.removeItem('RENDER_BACKEND_URL');
        backendUrlInput.value = '';
        backendPingResult.textContent = 'Reset to Auto/Proxy mode.';
        backendPingResult.className = 'backend-ping-result';
        updateBackendStatusUI();
        setTimeout(closeBackendModal, 500);
      });
    }
  }

  updateBackendStatusUI();

  // State
  let rawResults = [];
  let filteredResults = [];
  let currentQuery = '';
  let activeModalItem = null;
  let modalPhoneItems = [];
  let selectedModalUrls = new Set();

  let activeFilters = {
    color: 'all',
    storage: 'all',
    size: 'all',
    angle: 'all'
  };

  const COLOR_HEX_MAP = {
    'desert': '#d4b996',
    'titanium': '#8a8886',
    'natural': '#a8a39d',
    'black': '#1c1c1e',
    'dark': '#242426',
    'white': '#f2f2f7',
    'silver': '#e5e5ea',
    'blue': '#2c64a5',
    'ultramarine': '#2d46b9',
    'teal': '#2b7873',
    'green': '#34785c',
    'emerald': '#0e7054',
    'vintage': '#2e6f40',
    'racing': '#52525b',
    'pink': '#e5989b',
    'rose': '#d47278',
    'purple': '#805ad5',
    'violet': '#6b46c1',
    'yellow': '#e2b542',
    'gold': '#dfb15b',
    'obsidian': '#1a1a1a',
    'porcelain': '#f0eeea',
    'hazel': '#878377',
    'gray': '#71717a',
    'grey': '#71717a'
  };

  function getDotColor(colorName) {
    const lower = colorName.toLowerCase();
    for (const [key, hex] of Object.entries(COLOR_HEX_MAP)) {
      if (lower.includes(key)) return hex;
    }
    return '#94a3b8';
  }

  // Clear button on input
  queryInput.addEventListener('input', () => {
    clearSearchBtn.style.display = queryInput.value.trim() ? 'flex' : 'none';
  });

  clearSearchBtn.addEventListener('click', () => {
    queryInput.value = '';
    clearSearchBtn.style.display = 'none';
    queryInput.focus();
  });

  // Trending tags click
  if (quickTags) {
    quickTags.addEventListener('click', (e) => {
      const tag = e.target.closest('.tag-btn');
      if (!tag) return;
      const query = tag.getAttribute('data-query');
      queryInput.value = query;
      clearSearchBtn.style.display = 'flex';
      performSearch(query);
    });
  }

  // Quick Source Toggles Logic
  const toggleAll = document.getElementById('toggle-all');
  const labelToggleAll = document.getElementById('label-toggle-all');

  // Quick Source Toggles Logic (Multiselect with Master 'All Sites' toggle)
  function updateToggleUI() {
    const isAll = !toggleAll || toggleAll.checked;

    if (labelToggleAll) {
      labelToggleAll.classList.toggle('active-all', isAll);
    }

    SITE_CONFIGS.forEach(site => {
      const input = document.getElementById(site.id);
      const label = document.getElementById(site.labelId);
      if (!label) return;

      if (isAll) {
        // If All is active, individual site toggles are greyed out and unchecked
        if (input) input.checked = false;
        label.classList.remove(site.activeClass);
        label.classList.add('is-greyed-out');
      } else {
        // Multiselect mode: site toggles are active and colored according to their individual state
        label.classList.remove('is-greyed-out');
        const isChecked = input ? input.checked : false;
        label.classList.toggle(site.activeClass, isChecked);
      }
    });

    if (sourceSelect) {
      if (isAll) {
        sourceSelect.value = 'all';
      } else {
        const checkedSites = SITE_CONFIGS.filter(s => {
          const inp = document.getElementById(s.id);
          return inp && inp.checked;
        });
        if (checkedSites.length === 1) {
          sourceSelect.value = checkedSites[0].value;
        } else {
          sourceSelect.value = 'all';
        }
      }
    }
  }

  function getEffectiveSources() {
    if (toggleAll && toggleAll.checked) {
      return ['all'];
    }
    const selected = [];
    SITE_CONFIGS.forEach(site => {
      const input = document.getElementById(site.id);
      if (input && input.checked) {
        selected.push(site.value);
      }
    });
    if (selected.length === 0) {
      return ['all'];
    }
    return selected;
  }

  function getEffectiveSourceString() {
    const sources = getEffectiveSources();
    if (sources.includes('all')) return 'all';
    return sources.join(',');
  }

  function singleSourceMatch(itemSource, target) {
    if (target === 'ecommerce' || target === 'amazon_flipkart') {
      return itemSource.includes('flipkart') || itemSource.includes('amazon');
    }
    if (target === 'cashify') {
      return itemSource.includes('cashify');
    }
    if (target === 'fonezone') {
      return itemSource.includes('fonezone');
    }
    if (target === 'gameloot') {
      return itemSource.includes('gameloot');
    }
    if (target === 'triveniworld' || target === 'triveni') {
      return itemSource.includes('triveni');
    }
    if (target === 'vlebazaar') {
      return itemSource.includes('vlebazaar');
    }
    if (target === 'refurbished') {
      return itemSource.includes('cashify') || itemSource.includes('fonezone') || itemSource.includes('gameloot') || itemSource.includes('triveni') || itemSource.includes('vlebazaar');
    }
    if (target === 'flipkart') return itemSource.includes('flipkart');
    if (target === 'amazon') return itemSource.includes('amazon');
    if (target === 'official') {
      return itemSource.includes('official') || (!itemSource.includes('flipkart') && !itemSource.includes('amazon') && !itemSource.includes('cashify') && !itemSource.includes('fonezone') && !itemSource.includes('gameloot') && !itemSource.includes('triveni') && !itemSource.includes('vlebazaar') && !itemSource.includes('gsmarena'));
    }
    if (target === 'ebay') return itemSource.includes('ebay');
    if (target === 'alamy') return itemSource.includes('alamy');
    if (target === 'indiamart') return itemSource.includes('indiamart');
    if (target === 'gsmarena') return itemSource.includes('gsmarena');
    return true;
  }

  function itemMatchesSource(item, targetSources) {
    if (!targetSources || targetSources.length === 0 || targetSources.includes('all')) return true;
    const s = (item.source || '').toLowerCase();
    return targetSources.some(target => singleSourceMatch(s, target));
  }

  function onSourceChanged() {
    // Note: Absolutely NO toast popups on toggle click as requested!
    if (rawResults.length > 0) {
      const effectiveSources = getEffectiveSources();
      const matchCount = rawResults.filter(item => itemMatchesSource(item, effectiveSources)).length;
      if (matchCount > 0 || effectiveSources.includes('all')) {
        applyFilters();
      } else {
        // If no matching items exist in memory, silently trigger targeted scrape
        const q = currentQuery || queryInput.value.trim();
        if (q) {
          performSearch(q);
        } else {
          applyFilters();
        }
      }
    }
  }

  // Bind All Sites master toggle
  if (toggleAll) {
    toggleAll.addEventListener('change', () => {
      if (toggleAll.checked) {
        // Explicitly selected All Sites: uncheck specific site toggles
        SITE_CONFIGS.forEach(other => {
          const inp = document.getElementById(other.id);
          if (inp) inp.checked = false;
        });
      }
      updateToggleUI();
      onSourceChanged();
    });
  }

  // Bind individual site toggles (Multiselect)
  SITE_CONFIGS.forEach(site => {
    const input = document.getElementById(site.id);
    if (!input) return;

    input.addEventListener('change', () => {
      // If All was selected, turn it off now that user interacted with an individual site
      if (toggleAll && toggleAll.checked) {
        toggleAll.checked = false;
      }

      // Check if ANY individual site is still selected
      const anyChecked = SITE_CONFIGS.some(other => {
        const inp = document.getElementById(other.id);
        return inp && inp.checked;
      });

      // If user unchecked everything, revert back to All Sites being selected!
      if (!anyChecked && toggleAll) {
        toggleAll.checked = true;
      }

      updateToggleUI();
      onSourceChanged();
    });
  });

  if (sourceSelect) {
    sourceSelect.addEventListener('change', () => {
      const val = sourceSelect.value;
      if (val === 'all') {
        if (toggleAll) toggleAll.checked = true;
        SITE_CONFIGS.forEach(site => {
          const inp = document.getElementById(site.id);
          if (inp) inp.checked = false;
        });
      } else {
        if (toggleAll) toggleAll.checked = false;
        SITE_CONFIGS.forEach(site => {
          const inp = document.getElementById(site.id);
          if (inp) inp.checked = (site.value === val);
        });
      }
      updateToggleUI();
      onSourceChanged();
    });
  }

  // Initialize toggle UI state
  updateToggleUI();

  // Search form submit
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;
    performSearch(query);
  });

  /**
   * Main Search Function
   */
  async function performSearch(query) {
    currentQuery = query;
    const source = getEffectiveSourceString();
    const limit = limitSelect.value;

    setLoadingState(true);

    try {
      const apiBase = getApiBaseUrl();
      const url = `${apiBase}/api/scrape?q=${encodeURIComponent(query)}&source=${encodeURIComponent(source)}&limit=${limit}`;
      const res = await fetch(url);
      if (!res.ok) {
        let detail = '';
        try {
          const errData = await res.json();
          detail = errData.error || errData.detail || JSON.stringify(errData);
        } catch {
          detail = await res.text();
        }
        throw new Error(detail || `Server returned HTTP ${res.status}`);
      }
      const data = await res.json();

      setLoadingState(false);

      if (data.success && data.results && data.results.length > 0) {
        rawResults = data.results;
        populateSidebarOptions(rawResults);
        resetFilters();
        renderResults(data.duration);
      } else {
        rawResults = [];
        filteredResults = [];
        showEmptyState(
          data.error ? 'Scrape Error' : 'No images found',
          data.error || `No images found for "${query}". Try another query.`
        );
      }
    } catch (err) {
      setLoadingState(false);
      const isNetworkErr = err.name === 'AbortError' || (err.message && err.message.toLowerCase().includes('fetch'));
      const errorMsg = isNetworkErr
        ? 'Could not reach Render backend. On Render Free Tier, the backend service spins down after 15 min of inactivity and takes ~45 seconds to wake up. Please wait 15 seconds and click Scrape again.'
        : (err.message || 'Could not reach server.');
      showEmptyState('Connection / Scrape Error', errorMsg);
      showToast(isNetworkErr ? 'Backend waking up... please retry shortly' : `Scraping failed: ${err.message}`, 'error');
    }
  }

  function setLoadingState(isLoading) {
    searchSubmitBtn.disabled = isLoading;
    if (isLoading) {
      btnText.textContent = 'Scraping...';
      btnSpinner.style.display = 'inline-block';

      emptyState.style.display = 'none';
      resultsGrid.style.display = 'none';
      statsSection.style.display = 'none';

      renderSkeletons(parseInt(limitSelect.value, 10) || 24);
      loadingState.style.display = 'grid';
    } else {
      btnText.textContent = 'Scrape';
      btnSpinner.style.display = 'none';
      loadingState.style.display = 'none';
    }
  }

  function renderSkeletons(count) {
    loadingState.innerHTML = '';
    const renderCount = Math.min(count, 32);
    for (let i = 0; i < renderCount; i++) {
      const card = document.createElement('div');
      card.className = 'skeleton-card';
      card.innerHTML = `
        <div class="skeleton-media"></div>
        <div class="skeleton-body">
          <div class="skeleton-line w-75"></div>
          <div class="skeleton-line w-50"></div>
        </div>
      `;
      loadingState.appendChild(card);
    }
  }

  function showEmptyState(title, message) {
    resultsGrid.style.display = 'none';
    statsSection.style.display = 'none';
    emptyState.style.display = 'block';
    emptyTitle.textContent = title;
    emptyMsg.textContent = message;
  }

  /**
   * Populate Sidebar Options dynamically
   */
  function populateSidebarOptions(items) {
    // 1. Colours
    const colorCounts = {};
    const storageCounts = {};

    items.forEach(it => {
      const c = it.color || 'Standard / Official';
      colorCounts[c] = (colorCounts[c] || 0) + 1;

      if (it.storage && it.storage !== 'All') {
        storageCounts[it.storage] = (storageCounts[it.storage] || 0) + 1;
      }
    });

    countColorAll.textContent = items.length;

    sidebarColorList.innerHTML = `
      <button type="button" class="sidebar-pill active" data-color="all">
        <span class="pill-dot color-dot-all"></span>
        <span class="pill-name">All Colours</span>
        <span class="pill-count">${items.length}</span>
      </button>
    `;

    Object.entries(colorCounts).forEach(([colorName, count]) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'sidebar-pill';
      btn.setAttribute('data-color', colorName);
      const dotHex = getDotColor(colorName);
      btn.innerHTML = `
        <span class="pill-dot" style="background-color: ${dotHex}"></span>
        <span class="pill-name">${escapeHtml(colorName)}</span>
        <span class="pill-count">${count}</span>
      `;
      sidebarColorList.appendChild(btn);
    });

    // 2. Storage Sizes
    if (sidebarStorageList) {
      sidebarStorageList.innerHTML = `
        <button type="button" class="sidebar-pill active" data-storage="all">
          <span class="pill-name">All Storages</span>
          <span class="pill-count">${items.length}</span>
        </button>
      `;
      Object.entries(storageCounts).forEach(([storageName, count]) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'sidebar-pill';
        btn.setAttribute('data-storage', storageName);
        btn.innerHTML = `
          <span class="pill-name">${escapeHtml(storageName)}</span>
          <span class="pill-count">${count}</span>
        `;
        sidebarStorageList.appendChild(btn);
      });
    }

    sidebarDownloadBox.style.display = 'block';
    if (navDownloadZip) navDownloadZip.style.display = 'inline-flex';
  }

  /**
   * Filter handling
   */
  sidebarColorList.addEventListener('click', (e) => {
    const pill = e.target.closest('.sidebar-pill');
    if (!pill) return;
    sidebarColorList.querySelectorAll('.sidebar-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeFilters.color = pill.getAttribute('data-color') || 'all';
    applyFilters();
  });

  if (sidebarStorageList) {
    sidebarStorageList.addEventListener('click', (e) => {
      const pill = e.target.closest('.sidebar-pill');
      if (!pill) return;
      sidebarStorageList.querySelectorAll('.sidebar-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeFilters.storage = pill.getAttribute('data-storage') || 'all';
      applyFilters();
    });
  }

  sidebarSizeList.addEventListener('click', (e) => {
    const pill = e.target.closest('.sidebar-pill');
    if (!pill) return;
    sidebarSizeList.querySelectorAll('.sidebar-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeFilters.size = pill.getAttribute('data-size') || 'all';
    applyFilters();
  });

  sidebarAngleList.addEventListener('click', (e) => {
    const pill = e.target.closest('.sidebar-pill');
    if (!pill) return;
    sidebarAngleList.querySelectorAll('.sidebar-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeFilters.angle = pill.getAttribute('data-angle') || 'all';
    applyFilters();
  });

  resetFiltersBtn.addEventListener('click', () => {
    resetFilters();
    applyFilters();
  });

  function resetFilters() {
    activeFilters = { color: 'all', storage: 'all', size: 'all', angle: 'all' };
    sidebarColorList.querySelectorAll('.sidebar-pill').forEach(p => {
      p.classList.toggle('active', p.getAttribute('data-color') === 'all');
    });
    if (sidebarStorageList) {
      sidebarStorageList.querySelectorAll('.sidebar-pill').forEach(p => {
        p.classList.toggle('active', p.getAttribute('data-storage') === 'all');
      });
    }
    sidebarSizeList.querySelectorAll('.sidebar-pill').forEach(p => {
      p.classList.toggle('active', p.getAttribute('data-size') === 'all');
    });
    sidebarAngleList.querySelectorAll('.sidebar-pill').forEach(p => {
      p.classList.toggle('active', p.getAttribute('data-angle') === 'all');
    });
  }

  function applyFilters() {
    const effectiveSources = getEffectiveSources();

    filteredResults = rawResults.filter(item => {
      // Source filter (multiselect matching)
      if (!itemMatchesSource(item, effectiveSources)) {
        return false;
      }

      // Color
      if (activeFilters.color !== 'all') {
        const itemColor = (item.color || 'Standard').toLowerCase();
        if (itemColor !== activeFilters.color.toLowerCase()) {
          return false;
        }
      }

      // Storage
      if (activeFilters.storage !== 'all') {
        const itemStorage = (item.storage || '').toUpperCase();
        if (itemStorage !== activeFilters.storage.toUpperCase()) {
          return false;
        }
      }

      // Image Size
      if (activeFilters.size !== 'all') {
        const u = (item.url || '').toLowerCase();
        if (activeFilters.size === 'ultra') {
          const isUltra = u.includes('1200') || u.includes('1600') || u.includes('large') || u.includes('newsroom');
          if (!isUltra) return false;
        } else if (activeFilters.size === 'high') {
          const isHigh = u.includes('834') || u.includes('800') || u.includes('1200') || u.includes('large');
          if (!isHigh) return false;
        }
      }

      // Angle
      if (activeFilters.angle !== 'all') {
        const itemAngle = (item.angle || '').toLowerCase();
        const itemTitle = (item.title || '').toLowerCase();
        const targetAngle = activeFilters.angle.toLowerCase();
        if (!itemAngle.includes(targetAngle) && !itemTitle.includes(targetAngle)) {
          return false;
        }
      }

      return true;
    });

    // Ensure priority order
    filteredResults.sort((a, b) => {
      const getScore = (it) => {
        const s = (it.source || '').toLowerCase();
        if (s.includes('flipkart')) return 0;
        if (s.includes('amazon')) return 1;
        if (s.includes('cashify')) return 2;
        if (s.includes('fonezone')) return 3;
        if (s.includes('gameloot')) return 4;
        if (s.includes('triveni')) return 5;
        if (s.includes('vlebazaar')) return 6;
        if (s.includes('official')) return 7;
        if (s.includes('gsmarena')) return 8;
        return 9;
      };
      return getScore(a) - getScore(b);
    });

    renderGrid(filteredResults);
  }

  function renderResults(duration) {
    if (duration !== undefined) {
      statTime.textContent = `${duration}s`;
    }
    applyFilters();
  }

  function createImageCard(item, index) {
    const card = document.createElement('article');
    card.className = 'image-card';

    let sourceBadgeClass = 'badge';
    const s = (item.source || '').toLowerCase();
    if (s.includes('flipkart')) sourceBadgeClass = 'badge badge-flipkart';
    else if (s.includes('amazon')) sourceBadgeClass = 'badge badge-amazon';
    else if (s.includes('cashify')) sourceBadgeClass = 'badge badge-cashify';
    else if (s.includes('fonezone')) sourceBadgeClass = 'badge badge-fonezone';
    else if (s.includes('gameloot')) sourceBadgeClass = 'badge badge-gameloot';
    else if (s.includes('triveni')) sourceBadgeClass = 'badge badge-triveni';
    else if (s.includes('vlebazaar')) sourceBadgeClass = 'badge badge-vlebazaar';
    else if (s.includes('official')) sourceBadgeClass = 'badge badge-official';

    const colorText = item.color || 'Standard';
    const storageBadgeHtml = (item.storage && item.storage !== 'All') 
      ? `<span class="badge" title="Storage Size: ${escapeHtml(item.storage)}">💾 ${escapeHtml(item.storage)}</span>` 
      : '';
    const filenameText = item.filename || `phone_image_${index + 1}.jpg`;

    card.innerHTML = `
      <div class="card-media" title="View fullscreen">
        <img src="${item.url}" alt="${escapeHtml(item.title)}" loading="lazy">
        <div class="card-badges">
          <span class="${sourceBadgeClass}">${escapeHtml(item.source || 'Web')}</span>
          <span class="badge badge-color">${escapeHtml(colorText)}</span>
        </div>
        <div class="card-hover-overlay">
          <div class="overlay-btn">View</div>
        </div>
      </div>
      <div class="card-body">
        <h3 class="card-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</h3>
        <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
          ${storageBadgeHtml}
          <div class="card-filename-box" style="flex:1;" title="${escapeHtml(filenameText)}">
            ${escapeHtml(filenameText)}
          </div>
        </div>
        <div class="card-actions">
          <button class="card-btn card-btn-copy" data-url="${item.url}" title="Copy URL">
            Copy URL
          </button>
          <button class="card-btn card-btn-download" title="Download: ${escapeHtml(filenameText)}">
            Download
          </button>
        </div>
      </div>
    `;

    // Event: Click media to open modal
    const mediaEl = card.querySelector('.card-media');
    mediaEl.addEventListener('click', () => {
      openModal(item);
    });

    // Event: Copy button
    const copyBtn = card.querySelector('.card-btn-copy');
    copyBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      copyToClipboard(item.url, 'Copied URL');
    });

    // Event: Download button
    const downloadBtn = card.querySelector('.card-btn-download');
    downloadBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      downloadSingleImage(item.url, filenameText);
    });

    return card;
  }

  function groupItemsByModel(items) {
    const groups = new Map();
    items.forEach(item => {
      let m = (item.model || '').trim();
      if (!m) {
        m = currentQuery || item.title || 'Other Phone Models';
      }
      if (!groups.has(m)) {
        groups.set(m, []);
      }
      groups.get(m).push(item);
    });
    return groups;
  }

  async function downloadModelZip(modelName, modelItems, btnEl) {
    if (!modelItems || !modelItems.length) return;
    const origHtml = btnEl.innerHTML;
    btnEl.disabled = true;
    btnEl.innerHTML = `<span class="btn-spinner" style="display:inline-block; margin-right:4px;"></span> Archiving...`;

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/download-zip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: modelName,
          items: modelItems
        })
      });

      if (!response.ok) throw new Error('ZIP failed');

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      const cleanName = modelName.replace(/[^a-zA-Z0-9_\-]/g, '_');
      a.download = `${cleanName}_${modelItems.length}_jpg_images.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(blobUrl);
      document.body.removeChild(a);

      showToast(`Downloaded ${modelItems.length} images for ${modelName}!`, 'success');
    } catch (err) {
      showToast(`Download failed for ${modelName}`, 'error');
    } finally {
      btnEl.disabled = false;
      btnEl.innerHTML = origHtml;
    }
  }

  function renderGrid(items) {
    emptyState.style.display = 'none';

    statCount.textContent = items.length;
    statsSection.style.display = 'flex';
    resultsGrid.style.display = 'grid';
    resultsGrid.innerHTML = '';

    if (items.length === 0) {
      resultsGrid.style.display = 'none';
      const effectiveSource = getEffectiveSource();
      let msg = 'No images match the selected filters. Try resetting filters or toggling All Sources.';
      if (effectiveSource === 'ecommerce') {
        msg = 'No Amazon & Flipkart images match the current filters. Toggle back to All Sources or click "Scrape" to search directly.';
      } else if (effectiveSource === 'cashify') {
        msg = 'No Cashify images match the current filters. Toggle back to All Sources or click "Scrape" to search directly.';
      }
      showEmptyState('No matching images', msg);
      return;
    }

    const isGrouped = toggleGroupByModel ? toggleGroupByModel.checked : false;

    if (isGrouped) {
      resultsGrid.classList.add('grouped-view');
      const groups = groupItemsByModel(items);

      groups.forEach((groupItems, modelName) => {
        const groupCard = document.createElement('section');
        groupCard.className = 'model-group-card';

        // Extract unique colors, storages, and sources
        const uniqueColors = Array.from(new Set(groupItems.map(i => i.color).filter(c => c && c !== 'Standard' && c !== 'Standard / Official')));
        const uniqueStorages = Array.from(new Set(groupItems.map(i => i.storage).filter(s => s && s !== 'All')));
        const uniqueSources = Array.from(new Set(groupItems.map(i => i.source).filter(Boolean)));

        const colorsText = uniqueColors.length > 0 ? uniqueColors.slice(0, 4).join(', ') : '';
        const storagesText = uniqueStorages.length > 0 ? uniqueStorages.join(', ') : '';
        const sourcesText = uniqueSources.length > 0 ? uniqueSources.join(' • ') : '';

        groupCard.innerHTML = `
          <div class="model-group-header">
            <div class="model-group-title-row">
              <div class="model-icon-avatar">📱</div>
              <div class="model-meta">
                <div class="model-title-line">
                  <h2 class="model-name">${escapeHtml(modelName)}</h2>
                  <span class="model-count-badge">${groupItems.length} ${groupItems.length === 1 ? 'image' : 'images'}</span>
                </div>
                <div class="model-sub-details">
                  ${colorsText ? `<span class="model-detail-pill" title="Colors">🎨 ${escapeHtml(colorsText)}</span>` : ''}
                  ${storagesText ? `<span class="model-detail-pill" title="Storage Options">💾 ${escapeHtml(storagesText)}</span>` : ''}
                  ${sourcesText ? `<span class="model-detail-pill" title="Sources">🏷️ ${escapeHtml(sourcesText)}</span>` : ''}
                </div>
              </div>
            </div>
            <div class="model-group-actions">
              <button type="button" class="btn-download-group-zip" title="Download all ${groupItems.length} images for ${escapeHtml(modelName)} as ZIP">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Download Model (${groupItems.length} JPGs)
              </button>
            </div>
          </div>
          <div class="gallery-grid"></div>
        `;

        const subGrid = groupCard.querySelector('.gallery-grid');
        groupItems.forEach((it, idx) => {
          subGrid.appendChild(createImageCard(it, idx));
        });

        // Wire download model button
        const dlBtn = groupCard.querySelector('.btn-download-group-zip');
        if (dlBtn) {
          dlBtn.addEventListener('click', () => {
            downloadModelZip(modelName, groupItems, dlBtn);
          });
        }

        resultsGrid.appendChild(groupCard);
      });
    } else {
      resultsGrid.classList.remove('grouped-view');
      items.forEach((item, index) => {
        resultsGrid.appendChild(createImageCard(item, index));
      });
    }
  }

  if (toggleGroupByModel) {
    toggleGroupByModel.addEventListener('change', () => {
      const isChecked = toggleGroupByModel.checked;
      if (labelGroupByModel) {
        labelGroupByModel.classList.toggle('is-active', isChecked);
      }
      const currentList = filteredResults.length > 0 ? filteredResults : rawResults;
      if (currentList.length > 0) {
        renderGrid(currentList);
      }
      showToast(isChecked ? 'Grouped by Phone Model' : 'Standard Grid View', 'info');
    });
  }

  /**
   * Modal Lightbox with Multi-Image Selection & JPG Download
   */
  function updateModalMeta(item) {
    if (!item) return;
    modalFilenameDisplay.textContent = item.filename || 'phone_image.jpg';
    modalSourceBadge.textContent = item.source || 'Web';
    modalColorBadge.textContent = item.color || 'Standard';

    if (modalAngleBadge) {
      modalAngleBadge.textContent = item.angle || 'Front';
    }

    if (modalStorageBadge) {
      if (item.storage && item.storage !== 'All') {
        modalStorageBadge.textContent = item.storage;
        modalStorageBadge.style.display = 'inline-block';
      } else {
        modalStorageBadge.style.display = 'none';
      }
    }
  }

  function updateModalSelectionCount() {
    const count = selectedModalUrls.size;
    const total = modalPhoneItems.length;
    modalSelectedCount.textContent = `${count} of ${total} selected`;

    if (count === 0) {
      modalDownloadSelectedText.textContent = 'Select Images to Download';
      modalDownloadSelectedBtn.disabled = true;
    } else if (count === 1) {
      modalDownloadSelectedText.textContent = 'Download 1 Selected (.jpg)';
      modalDownloadSelectedBtn.disabled = false;
    } else {
      modalDownloadSelectedText.textContent = `Download ${count} Selected (JPG)`;
      modalDownloadSelectedBtn.disabled = false;
    }
  }

  function openModal(item) {
    activeModalItem = item;
    modalImg.src = item.url;
    modalPhoneTitle.textContent = item.model || item.title || 'Phone Views';
    updateModalMeta(item);

    // Identify all images belonging to this specific phone
    const targetModel = (item.model || '').toLowerCase().trim();
    const targetColor = (item.color || '').toLowerCase().trim();

    // 1. Group exact variant faces first (Front, Back, Camera, Side, Angles of this color)
    const exactVariantFaces = rawResults.filter(r => {
      const rModel = (r.model || '').toLowerCase().trim();
      const rColor = (r.color || '').toLowerCase().trim();
      return rModel === targetModel && (targetColor === '' || targetColor === 'standard / official' || rColor === targetColor);
    });

    // 2. Also find all other colorways and faces of this model
    const otherVariantFaces = rawResults.filter(r => {
      const rModel = (r.model || '').toLowerCase().trim();
      return rModel === targetModel && !exactVariantFaces.includes(r);
    });

    modalPhoneItems = [...exactVariantFaces, ...otherVariantFaces];

    // Fallback if model was not cleanly isolated
    if (modalPhoneItems.length <= 1 && rawResults.length > 1) {
      const targetBrand = (item.brand || '').toLowerCase().trim();
      if (targetBrand) {
        modalPhoneItems = rawResults.filter(r => (r.brand || '').toLowerCase().trim() === targetBrand);
      }
      if (modalPhoneItems.length <= 1) {
        modalPhoneItems = rawResults;
      }
    }

    // Default: select all views of this specific phone
    selectedModalUrls = new Set(modalPhoneItems.map(x => x.url));

    // Populate thumbnail strip
    modalThumbnailsStrip.innerHTML = '';
    modalPhoneItems.forEach((thumbItem, idx) => {
      const card = document.createElement('div');
      card.className = `modal-thumb-card ${thumbItem.url === item.url ? 'active-preview' : ''} selected-for-download`;
      card.dataset.url = thumbItem.url;

      // Checkbox wrapper
      const cbWrapper = document.createElement('div');
      cbWrapper.className = 'thumb-checkbox-wrapper';
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'thumb-checkbox';
      checkbox.checked = selectedModalUrls.has(thumbItem.url);

      checkbox.addEventListener('change', (e) => {
        e.stopPropagation();
        if (checkbox.checked) {
          selectedModalUrls.add(thumbItem.url);
          card.classList.add('selected-for-download');
        } else {
          selectedModalUrls.delete(thumbItem.url);
          card.classList.remove('selected-for-download');
        }
        updateModalSelectionCount();
      });

      cbWrapper.appendChild(checkbox);

      // Thumbnail Image
      const imgWrapper = document.createElement('div');
      imgWrapper.className = 'thumb-img-wrapper';
      const thumbImg = document.createElement('img');
      thumbImg.src = thumbItem.url;
      thumbImg.alt = thumbItem.angle || `View ${idx + 1}`;
      thumbImg.loading = 'lazy';
      imgWrapper.appendChild(thumbImg);

      // Label (Angle + Color)
      const label = document.createElement('div');
      label.className = 'thumb-label';
      const angle = thumbItem.angle || `View ${idx + 1}`;
      label.textContent = angle;
      label.title = `${angle} • ${thumbItem.color || 'Standard'}`;

      card.appendChild(cbWrapper);
      card.appendChild(imgWrapper);
      card.appendChild(label);

      // Click card to switch active preview
      card.addEventListener('click', (e) => {
        if (e.target === checkbox) return;
        activeModalItem = thumbItem;
        modalImg.src = thumbItem.url;
        updateModalMeta(thumbItem);

        modalThumbnailsStrip.querySelectorAll('.modal-thumb-card').forEach(el => {
          el.classList.toggle('active-preview', el.dataset.url === thumbItem.url);
        });
      });

      modalThumbnailsStrip.appendChild(card);
    });

    updateModalSelectionCount();
    modal.style.display = 'flex';
  }

  function closeModal() {
    modal.style.display = 'none';
    modalImg.src = '';
    activeModalItem = null;
    modalPhoneItems = [];
    selectedModalUrls.clear();
  }

  modalCloseBtn.addEventListener('click', closeModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.style.display === 'flex') {
      closeModal();
    }
  });

  // Select All button
  modalSelectAllBtn.addEventListener('click', () => {
    modalPhoneItems.forEach(it => selectedModalUrls.add(it.url));
    modalThumbnailsStrip.querySelectorAll('.thumb-checkbox').forEach(cb => {
      cb.checked = true;
    });
    modalThumbnailsStrip.querySelectorAll('.modal-thumb-card').forEach(card => {
      card.classList.add('selected-for-download');
    });
    updateModalSelectionCount();
  });

  // Deselect All button
  modalDeselectAllBtn.addEventListener('click', () => {
    selectedModalUrls.clear();
    modalThumbnailsStrip.querySelectorAll('.thumb-checkbox').forEach(cb => {
      cb.checked = false;
    });
    modalThumbnailsStrip.querySelectorAll('.modal-thumb-card').forEach(card => {
      card.classList.remove('selected-for-download');
    });
    updateModalSelectionCount();
  });

  // Copy Link button
  modalCopyBtn.addEventListener('click', () => {
    if (activeModalItem) {
      copyToClipboard(activeModalItem.url, 'Copied URL');
    }
  });

  // Download Single (Viewed) Image as .jpg
  modalDownloadSingleBtn.addEventListener('click', () => {
    if (activeModalItem) {
      let filename = activeModalItem.filename || 'phone_image.jpg';
      if (!filename.toLowerCase().endsWith('.jpg')) {
        filename = filename.replace(/\.[a-zA-Z0-9]+$/, '') + '.jpg';
      }
      downloadSingleImage(activeModalItem.url, filename);
    }
  });

  // Download Selected Views as JPG / ZIP
  modalDownloadSelectedBtn.addEventListener('click', async () => {
    if (selectedModalUrls.size === 0) {
      showToast('Please select at least one image to download.', 'error');
      return;
    }

    const selectedItems = modalPhoneItems.filter(it => selectedModalUrls.has(it.url));

    // If only 1 image selected, download directly as .jpg
    if (selectedItems.length === 1) {
      let fn = selectedItems[0].filename || 'phone_image.jpg';
      if (!fn.toLowerCase().endsWith('.jpg')) {
        fn = fn.replace(/\.[a-zA-Z0-9]+$/, '') + '.jpg';
      }
      downloadSingleImage(selectedItems[0].url, fn);
      return;
    }

    // Multiple images: package into ZIP with server-side JPG conversion
    modalDownloadSelectedBtn.disabled = true;
    const originalText = modalDownloadSelectedText.textContent;
    modalDownloadSelectedText.textContent = 'Archiving JPGs...';

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/download-zip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: (activeModalItem && activeModalItem.model) || currentQuery || 'phone_images',
          items: selectedItems
        })
      });

      if (!response.ok) throw new Error('ZIP creation failed');

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      const cleanModel = ((activeModalItem && activeModalItem.model) || currentQuery || 'phone')
        .replace(/[^a-zA-Z0-9_\-]/g, '_');
      a.download = `${cleanModel}_selected_${selectedItems.length}_jpg_images.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(blobUrl);
      document.body.removeChild(a);

      showToast(`Downloaded ${selectedItems.length} selected JPG images!`, 'success');
    } catch (err) {
      showToast('Download failed. Please try again.', 'error');
    } finally {
      modalDownloadSelectedBtn.disabled = false;
      modalDownloadSelectedText.textContent = originalText;
    }
  });

  /**
   * Copy All Filtered URLs
   */
  copyAllBtn.addEventListener('click', () => {
    const list = filteredResults.length ? filteredResults : rawResults;
    if (!list.length) return;
    const allUrls = list.map(r => `${r.filename}\t${r.url}`).join('\n');
    copyToClipboard(allUrls, `Copied ${list.length} URLs`);
  });

  /**
   * Download All Views, Colours & Sizes as ZIP
   */
  async function downloadFilteredZip() {
    const list = filteredResults.length ? filteredResults : rawResults;
    if (!list.length) return;

    downloadZipBtn.disabled = true;
    zipBtnText.textContent = 'Archiving ZIP...';

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/download-zip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: currentQuery || 'phones',
          items: list
        })
      });

      if (!response.ok) throw new Error('ZIP failed');

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      const cleanQ = (currentQuery || 'export').replace(/[^a-zA-Z0-9_\-]/g, '_');
      const filterSuffix = activeFilters.color !== 'all' ? `_${activeFilters.color.replace(/\s+/g, '_')}` : '';
      a.download = `phone_img_scraper_${cleanQ}${filterSuffix}_all_variants.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(blobUrl);
      document.body.removeChild(a);

      showToast(`Downloaded ${list.length} images as ZIP!`, 'success');
    } catch (err) {
      showToast('ZIP download failed', 'error');
    } finally {
      downloadZipBtn.disabled = false;
      zipBtnText.textContent = 'Download All (ZIP)';
    }
  }

  downloadZipBtn.addEventListener('click', downloadFilteredZip);
  if (navDownloadZip) navDownloadZip.addEventListener('click', downloadFilteredZip);

  /**
   * Helpers
   */
  async function downloadSingleImage(url, filename) {
    let cleanFilename = filename || 'phone_image.jpg';
    if (!cleanFilename.toLowerCase().endsWith('.jpg') && !cleanFilename.toLowerCase().endsWith('.jpeg')) {
      cleanFilename = cleanFilename.replace(/\.[a-zA-Z0-9]+$/, '') + '.jpg';
    } else if (cleanFilename.toLowerCase().endsWith('.jpeg')) {
      cleanFilename = cleanFilename.slice(0, -5) + '.jpg';
    }

    try {
      const proxyUrl = `${getApiBaseUrl()}/api/proxy-image?url=${encodeURIComponent(url)}&filename=${encodeURIComponent(cleanFilename)}`;
      const resp = await fetch(proxyUrl);
      if (!resp.ok) {
        throw new Error(`Proxy status ${resp.status}`);
      }

      const rawBlob = await resp.blob();
      // Enforce image/jpeg MIME type on the Blob so Chrome / Windows downloads it strictly as .jpg
      const jpgBlob = new Blob([rawBlob], { type: 'image/jpeg' });
      const blobUrl = window.URL.createObjectURL(jpgBlob);

      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = cleanFilename;
      document.body.appendChild(a);
      a.click();

      setTimeout(() => {
        window.URL.revokeObjectURL(blobUrl);
        if (a.parentNode) document.body.removeChild(a);
      }, 1000);

      showToast(`Downloaded ${cleanFilename}`, 'success');
    } catch (err) {
      console.warn('Proxy download failed, falling back to Canvas JPG conversion:', err);
      downloadViaCanvasFallback(url, cleanFilename);
    }
  }

  function downloadViaCanvasFallback(url, filename) {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth || img.width;
        canvas.height = img.naturalHeight || img.height;
        const ctx = canvas.getContext('2d');
        // Pure white background behind any transparency
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);

        canvas.toBlob((blob) => {
          if (!blob) throw new Error('Canvas conversion failed');
          const blobUrl = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = blobUrl;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          setTimeout(() => {
            window.URL.revokeObjectURL(blobUrl);
            if (a.parentNode) document.body.removeChild(a);
          }, 1000);
          showToast(`Downloaded ${filename}`, 'success');
        }, 'image/jpeg', 0.95);
      } catch (e) {
        showToast(`Download failed for ${filename}`, 'error');
      }
    };
    img.onerror = () => {
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.target = '_blank';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    };
    img.src = url;
  }

  function copyToClipboard(text, successMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg, 'success');
      }).catch(() => {
        fallbackCopyTextToClipboard(text, successMsg);
      });
    } else {
      fallbackCopyTextToClipboard(text, successMsg);
    }
  }

  function fallbackCopyTextToClipboard(text, successMsg) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      showToast(successMsg, 'success');
    } catch (err) {
      showToast('Could not copy', 'error');
    }
    document.body.removeChild(textArea);
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
        if (toast.parentNode) {
          toastContainer.removeChild(toast);
        }
      }, 200);
    }, 2500);
  }
});
