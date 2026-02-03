/**
 * Download Portal - Main JavaScript
 */

const API_BASE = 'api';

// State
let currentPage = 1;
let totalPages = 1;
let currentType = 'all';
let currentSearch = '';
let currentSort = 'date_desc';
// Theme is set from PHP/database, not localStorage
let theme = document.body.classList.contains('light-theme') ? 'light' : 'dark';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateThemeButton();
    loadStats();
    loadTopDownloads();
    loadTrendingDownloads();
    loadDownloads();
    loadSettings();
    setupEventListeners();
});

// Theme
function toggleTheme() {
    theme = theme === 'dark' ? 'light' : 'dark';
    document.body.classList.toggle('light-theme');
    updateThemeButton();
    
    // Save to server
    fetch(`${API_BASE}/theme.php`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: theme })
    }).then(response => response.json())
      .then(data => {
          if (data.error) {
              console.error('Failed to save theme:', data.error);
          }
      });
}

function updateThemeButton() {
    const btn = document.getElementById('themeToggle');
    if (btn) {
        btn.textContent = theme === 'dark' ? '☀ LIGHT' : '☾ DARK';
    }
}

// Event Listeners
function setupEventListeners() {
    // Search
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') doSearch();
        });
    }
    if (searchBtn) {
        searchBtn.addEventListener('click', doSearch);
    }
    
    // Type filter
    const typeFilter = document.getElementById('typeFilter');
    if (typeFilter) {
        typeFilter.addEventListener('change', () => {
            currentType = typeFilter.value;
            currentPage = 1;
            loadDownloads();
        });
    }
    
    // Sort
    const sortFilter = document.getElementById('sortFilter');
    if (sortFilter) {
        sortFilter.addEventListener('change', () => {
            currentSort = sortFilter.value;
            currentPage = 1;
            loadDownloads();
        });
    }
    
    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function doSearch() {
    const searchInput = document.getElementById('searchInput');
    currentSearch = searchInput ? searchInput.value.trim() : '';
    currentPage = 1;
    loadDownloads();
}

// API Calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}/${endpoint}`, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { error: error.message };
    }
}

// Load Stats
async function loadStats() {
    const data = await apiCall('settings.php?action=stats');
    if (data.error) return;
    
    updateElement('statTotal', formatNumber(data.total));
    updateElement('statGames', formatNumber(data.games));
    updateElement('statSoftware', formatNumber(data.software));
    updateElement('statMovies', formatNumber(data.movies));
    updateElement('statTvShows', formatNumber(data.tv_shows));
    updateElement('statDownloads', formatNumber(data.total_downloads));
}

// Load Settings
async function loadSettings() {
    const data = await apiCall('settings.php?action=get');
    if (data.error) return;
    
    // Update site name
    const logo = document.querySelector('.logo');
    if (logo && data.site_name) {
        logo.textContent = data.site_name;
    }
    
    // Update footer
    updateFooter(data);
}

function updateFooter(settings) {
    const footer1 = document.getElementById('footerLine1');
    const footer2 = document.getElementById('footerLine2');
    
    if (footer1 && settings.footer_line1_template) {
        footer1.textContent = settings.footer_line1_template
            .replace('{admin_email}', settings.admin_email || 'admin@example.com');
    }
    
    if (footer2 && settings.footer_line2_template) {
        footer2.textContent = settings.footer_line2_template
            .replace('{site_name}', settings.site_name || 'DOWNLOAD ZONE')
            .replace('{year}', new Date().getFullYear());
    }
}

// Load Top Downloads
async function loadTopDownloads() {
    const container = document.getElementById('topDownloads');
    if (!container) return;
    
    const data = await apiCall('downloads.php?action=top');
    
    if (!data.enabled || (!data.sponsored?.length && !data.items?.length)) {
        container.closest('.top-section')?.classList.add('hidden');
        return;
    }
    
    let html = '';
    
    // Sponsored first
    if (data.sponsored?.length) {
        data.sponsored.forEach(item => {
            html += renderDownloadCard(item, true);
        });
    }
    
    // Regular top downloads
    if (data.items?.length) {
        data.items.forEach(item => {
            html += renderDownloadCard(item, false);
        });
    }
    
    container.innerHTML = html;
    
    // Track sponsored clicks
    container.querySelectorAll('.download-card.sponsored .download-link').forEach(link => {
        link.addEventListener('click', () => {
            const id = link.dataset.sponsoredId;
            if (id) trackSponsoredClick(id);
        });
    });
}

// Load Trending Downloads
async function loadTrendingDownloads() {
    const container = document.getElementById('trendingDownloads');
    if (!container) return;
    
    const data = await apiCall('downloads.php?action=trending');
    
    if (!data.enabled || !data.items?.length) {
        container.closest('.top-section')?.classList.add('hidden');
        return;
    }
    
    let html = '';
    data.items.forEach(item => {
        html += renderDownloadCard(item, false);
    });
    
    container.innerHTML = html;
}

// Load Downloads
async function loadDownloads() {
    const tbody = document.getElementById('downloadsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading downloads</td></tr>';
    
    let url = `downloads.php?action=list&page=${currentPage}&limit=50`;
    if (currentType !== 'all') url += `&type_filter=${currentType}`;
    if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;
    if (currentSort) url += `&sort_by=${currentSort}`;
    
    const data = await apiCall(url);
    
    if (data.error) {
        tbody.innerHTML = '<tr><td colspan="6" class="alert alert-error">Failed to load downloads</td></tr>';
        return;
    }
    
    totalPages = data.pages || 1;
    
    if (!data.items?.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No downloads found</td></tr>';
        renderPagination();
        return;
    }
    
    let html = '';
    data.items.forEach(item => {
        html += renderDownloadRow(item);
    });
    
    tbody.innerHTML = html;
    renderPagination();
    
    // Track download clicks
    tbody.querySelectorAll('.download-name-link').forEach(link => {
        link.addEventListener('click', () => {
            const id = link.dataset.downloadId;
            if (id) trackDownload(id);
        });
    });
}

// Render Download Row for Table
function renderDownloadRow(item) {
    const typeLabels = {
        'game': 'Game',
        'software': 'Software', 
        'movie': 'Movie',
        'tv_show': 'TV Show'
    };
    
    const typeLabel = typeLabels[item.type] || item.type;
    const siteName = item.site_name || '---';
    const siteUrl = item.site_url || '#';
    
    return `
        <tr class="download-row" data-id="${item.id || ''}">
            <td>
                <a href="${escapeHtml(item.download_link)}" 
                   class="download-name-link" 
                   target="_blank"
                   data-download-id="${item.id || ''}"
                   title="${escapeHtml(item.description || item.name)}">
                    ${escapeHtml(item.name)}
                </a>
                ${item.description ? `<span class="download-description">${escapeHtml(item.description)}</span>` : ''}
            </td>
            <td>${escapeHtml(item.submission_date || '')}</td>
            <td><span class="type-badge type-${item.type}">${escapeHtml(typeLabel)}</span></td>
            <td>${escapeHtml(item.file_size || '-')}</td>
            <td>${item.site_url ? `<a href="${escapeHtml(siteUrl)}" target="_blank">${escapeHtml(siteName)}</a>` : '---'}</td>
            <td class="download-count-cell">${formatNumber(item.download_count || 0)}</td>
        </tr>
    `;
}

// Render Download Card
function renderDownloadCard(item, isSponsored) {
    const tags = item.tags || [];
    const tagsHtml = tags.slice(0, 3).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('');
    
    return `
        <div class="download-card${isSponsored ? ' sponsored' : ''}" data-id="${item.id || ''}">
            <div class="download-name">${escapeHtml(item.name)}</div>
            <div class="download-meta">
                <span class="download-type">${escapeHtml(item.type)}</span>
                ${item.file_size ? `<span>${escapeHtml(item.file_size)}</span>` : ''}
                ${item.category ? `<span>${escapeHtml(item.category)}</span>` : ''}
                <span>${formatNumber(item.download_count || 0)} downloads</span>
            </div>
            ${tagsHtml ? `<div class="download-tags">${tagsHtml}</div>` : ''}
            <a href="${escapeHtml(item.download_link)}" 
               class="download-link" 
               target="_blank"
               data-download-id="${item.id || ''}"
               ${isSponsored ? `data-sponsored-id="${item.id || ''}"` : ''}>
                DOWNLOAD
            </a>
            ${item.site_name ? `
                <div class="download-meta mt-20">
                    <a href="${escapeHtml(item.site_url || '#')}" target="_blank" style="color: var(--accent);">
                        ${escapeHtml(item.site_name)}
                    </a>
                </div>
            ` : ''}
        </div>
    `;
}

// Pagination
function renderPagination() {
    const container = document.getElementById('pagination');
    if (!container) return;
    
    let html = '';
    
    html += `<button onclick="goToPage(${currentPage - 1})" ${currentPage <= 1 ? 'disabled' : ''}>← PREV</button>`;
    
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);
    
    if (start > 1) {
        html += `<button onclick="goToPage(1)">1</button>`;
        if (start > 2) html += `<span class="page-info">...</span>`;
    }
    
    for (let i = start; i <= end; i++) {
        html += `<button onclick="goToPage(${i})" class="${i === currentPage ? 'active' : ''}">${i}</button>`;
    }
    
    if (end < totalPages) {
        if (end < totalPages - 1) html += `<span class="page-info">...</span>`;
        html += `<button onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }
    
    html += `<button onclick="goToPage(${currentPage + 1})" ${currentPage >= totalPages ? 'disabled' : ''}>NEXT →</button>`;
    
    container.innerHTML = html;
}

function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadDownloads();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Track Downloads
async function trackDownload(id) {
    await apiCall(`downloads.php?action=track&id=${id}`, { method: 'POST' });
}

async function trackSponsoredClick(id) {
    await apiCall(`admin.php?action=sponsored-click&id=${id}`, { method: 'POST' });
}

// Utilities
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateElement(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// Toast notifications
function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
}
