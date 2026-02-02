import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Download, Gamepad2, Monitor, Film, Tv, Search, TrendingUp, SlidersHorizontal, X, ChevronDown, Trophy, Tag } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const typeIcons = {
    game: Gamepad2,
    software: Monitor,
    movie: Film,
    tv_show: Tv
};

const typeLabels = {
    game: 'Game',
    software: 'Software',
    movie: 'Movie',
    tv_show: 'TV Show'
};

const sortOptions = [
    { value: 'date_desc', label: 'Newest First' },
    { value: 'date_asc', label: 'Oldest First' },
    { value: 'downloads_desc', label: 'Most Downloaded' },
    { value: 'downloads_asc', label: 'Least Downloaded' },
    { value: 'name_asc', label: 'Name A-Z' },
    { value: 'name_desc', label: 'Name Z-A' },
    { value: 'size_desc', label: 'Largest First' },
    { value: 'size_asc', label: 'Smallest First' }
];

const sizePresets = [
    { label: 'Any', min: '', max: '' },
    { label: '< 100 MB', min: '', max: '100 MB' },
    { label: '100 MB - 1 GB', min: '100 MB', max: '1 GB' },
    { label: '1 GB - 5 GB', min: '1 GB', max: '5 GB' },
    { label: '5 GB - 20 GB', min: '5 GB', max: '20 GB' },
    { label: '> 20 GB', min: '20 GB', max: '' }
];

const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
};

export default function HomePage() {
    const [downloads, setDownloads] = useState([]);
    const [topDownloads, setTopDownloads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);
    const [filter, setFilter] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [searchInput, setSearchInput] = useState('');
    const [stats, setStats] = useState(null);
    const [sortBy, setSortBy] = useState('date_desc');
    const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [sizeMin, setSizeMin] = useState('');
    const [sizeMax, setSizeMax] = useState('');
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState('');
    const [popularTags, setPopularTags] = useState([]);
    const [selectedTags, setSelectedTags] = useState([]);

    const fetchDownloads = useCallback(async () => {
        setLoading(true);
        try {
            const params = { page, limit: 50, sort_by: sortBy };
            if (filter !== 'all') {
                params.type_filter = filter;
            }
            if (searchQuery.trim()) {
                params.search = searchQuery.trim();
            }
            if (dateFrom) {
                params.date_from = dateFrom;
            }
            if (dateTo) {
                params.date_to = dateTo;
            }
            if (sizeMin) {
                params.size_min = sizeMin;
            }
            if (sizeMax) {
                params.size_max = sizeMax;
            }
            if (selectedCategory) {
                params.category = selectedCategory;
            }
            if (selectedTags.length > 0) {
                params.tags = selectedTags.join(',');
            }
            const response = await axios.get(`${API}/downloads`, { params });
            setDownloads(response.data.items);
            setTotalPages(response.data.pages);
            setTotal(response.data.total);
        } catch (error) {
            console.error('Error fetching downloads:', error);
        } finally {
            setLoading(false);
        }
    }, [page, filter, searchQuery, sortBy, dateFrom, dateTo, sizeMin, sizeMax, selectedCategory, selectedTags]);

    const fetchTopDownloads = async () => {
        try {
            const response = await axios.get(`${API}/downloads/top`);
            if (response.data.enabled) {
                const sponsored = (response.data.sponsored || []).map(item => ({ ...item, isSponsored: true }));
                const regular = (response.data.items || []).map(item => ({ ...item, isSponsored: false }));
                setTopDownloads([...sponsored, ...regular]);
            } else {
                setTopDownloads([]);
            }
        } catch (error) {
            console.error('Error fetching top downloads:', error);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await axios.get(`${API}/stats`);
            setStats(response.data);
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    const fetchCategories = async () => {
        try {
            const response = await axios.get(`${API}/categories`);
            setCategories(response.data.items || []);
        } catch (error) {
            console.error('Error fetching categories:', error);
        }
    };

    const fetchPopularTags = async () => {
        try {
            const response = await axios.get(`${API}/tags?limit=30`);
            setPopularTags(response.data.items || []);
        } catch (error) {
            console.error('Error fetching tags:', error);
        }
    };

    useEffect(() => {
        fetchDownloads();
    }, [fetchDownloads]);

    useEffect(() => {
        fetchStats();
        fetchTopDownloads();
        fetchCategories();
        fetchPopularTags();
    }, []);

    const handleFilterChange = (newFilter) => {
        setFilter(newFilter);
        setSelectedCategory('');
        setPage(1);
    };

    const handleSearch = (e) => {
        e.preventDefault();
        setSearchQuery(searchInput);
        setPage(1);
    };

    const handleClearSearch = () => {
        setSearchInput('');
        setSearchQuery('');
        setPage(1);
    };

    const handleClearFilters = () => {
        setDateFrom('');
        setDateTo('');
        setSizeMin('');
        setSizeMax('');
        setSelectedCategory('');
        setSelectedTags([]);
        setSearchInput('');
        setSearchQuery('');
        setFilter('all');
        setSortBy('date_desc');
        setPage(1);
    };

    const handleDownloadClick = async (downloadId) => {
        try {
            await axios.post(`${API}/downloads/${downloadId}/increment`);
            setDownloads(prev => prev.map(d => 
                d.id === downloadId ? { ...d, download_count: (d.download_count || 0) + 1 } : d
            ));
        } catch (error) {
            console.error('Error incrementing download:', error);
        }
    };

    const renderPagination = () => {
        const pages = [];
        const maxVisible = 5;
        let start = Math.max(1, page - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);
        
        if (end - start < maxVisible - 1) {
            start = Math.max(1, end - maxVisible + 1);
        }

        if (page > 1) {
            pages.push(
                <button 
                    key="prev" 
                    className="page-btn" 
                    onClick={() => setPage(page - 1)}
                    data-testid="pagination-prev"
                >
                    {'<'}
                </button>
            );
        }

        if (start > 1) {
            pages.push(
                <button key={1} className="page-btn" onClick={() => setPage(1)} data-testid="pagination-1">
                    [ 1 ]
                </button>
            );
            if (start > 2) {
                pages.push(<span key="dots1" className="page-btn">...</span>);
            }
        }

        for (let i = start; i <= end; i++) {
            pages.push(
                <button
                    key={i}
                    className={`page-btn ${page === i ? 'active' : ''}`}
                    onClick={() => setPage(i)}
                    data-testid={`pagination-${i}`}
                >
                    [ {i} ]
                </button>
            );
        }

        if (end < totalPages) {
            if (end < totalPages - 1) {
                pages.push(<span key="dots2" className="page-btn">...</span>);
            }
            pages.push(
                <button 
                    key={totalPages} 
                    className="page-btn" 
                    onClick={() => setPage(totalPages)}
                    data-testid={`pagination-${totalPages}`}
                >
                    [ {totalPages} ]
                </button>
            );
        }

        if (page < totalPages) {
            pages.push(
                <button 
                    key="next" 
                    className="page-btn" 
                    onClick={() => setPage(page + 1)}
                    data-testid="pagination-next"
                >
                    {'>'}
                </button>
            );
        }

        return pages;
    };

    return (
        <div data-testid="home-page">
            {/* Marquee Banner */}
            <div className="marquee-container">
                <div className="marquee-content pixel-font" style={{ fontSize: '0.625rem' }}>
                    <span className="marquee-item neon-glow">*** WELCOME TO THE DOWNLOAD ZONE ***</span>
                    <span className="marquee-item">LATEST RELEASES AVAILABLE</span>
                    <span className="marquee-item neon-glow">*** SUBMIT YOUR FILES ***</span>
                    <span className="marquee-item">GAMES - SOFTWARE - MOVIES - TV SHOWS</span>
                    <span className="marquee-item neon-glow">*** WELCOME TO THE DOWNLOAD ZONE ***</span>
                    <span className="marquee-item">LATEST RELEASES AVAILABLE</span>
                </div>
            </div>

            <div className="main-content">
                {/* Top Downloads Section */}
                {topDownloads.length > 0 && (
                    <div className="top-downloads-section" style={{ marginBottom: '2rem' }} data-testid="top-downloads-section">
                        <h2 className="pixel-font neon-glow" style={{ fontSize: '0.875rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Trophy size={18} />
                            TOP DOWNLOADS
                        </h2>
                        <div style={{ 
                            display: 'grid', 
                            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', 
                            gap: '0.75rem'
                        }}>
                            {topDownloads.map((item, index) => {
                                const TypeIcon = typeIcons[item.type] || Download;
                                const isSponsored = item.isSponsored;
                                return (
                                    <div 
                                        key={item.id || `sponsored-${index}`} 
                                        className="top-download-card"
                                        style={{
                                            border: isSponsored ? '2px solid #FFD700' : '1px solid hsl(var(--border))',
                                            padding: '0.75rem',
                                            background: isSponsored ? 'rgba(255, 215, 0, 0.1)' : 'hsl(var(--card))',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.75rem',
                                            position: 'relative'
                                        }}
                                        data-testid={`top-download-${index}`}
                                    >
                                        {isSponsored && (
                                            <div style={{
                                                position: 'absolute',
                                                top: '-8px',
                                                right: '8px',
                                                background: '#FFD700',
                                                color: '#000',
                                                fontSize: '0.625rem',
                                                padding: '2px 6px',
                                                fontWeight: 'bold',
                                                textTransform: 'uppercase'
                                            }}>
                                                SPONSORED
                                            </div>
                                        )}
                                        <div style={{
                                            width: '32px',
                                            height: '32px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            background: isSponsored ? 'rgba(255, 215, 0, 0.3)' : 'hsl(var(--primary) / 0.2)',
                                            border: isSponsored ? '1px solid #FFD700' : '1px solid hsl(var(--primary))',
                                            fontWeight: 'bold',
                                            fontSize: '0.875rem',
                                            color: isSponsored ? '#FFD700' : 'inherit'
                                        }}>
                                            #{index + 1}
                                        </div>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <a 
                                                href={item.download_link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                onClick={() => !isSponsored && item.id && handleDownloadClick(item.id)}
                                                style={{ 
                                                    display: 'block',
                                                    whiteSpace: 'nowrap',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    fontSize: '0.875rem'
                                                }}
                                            >
                                                {item.name}
                                            </a>
                                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem', fontSize: '0.75rem', opacity: 0.7, flexWrap: 'wrap' }}>
                                                <span className={`type-${item.type}`}>
                                                    <TypeIcon size={10} style={{ display: 'inline', marginRight: '0.25rem' }} />
                                                    {typeLabels[item.type] || item.type}
                                                </span>
                                                {!isSponsored && (
                                                    <span style={{ color: 'hsl(var(--accent))' }}>
                                                        {formatNumber(item.download_count || 0)} downloads
                                                    </span>
                                                )}
                                                {isSponsored && item.description && (
                                                    <span>{item.description}</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Stats Bar */}
                <div className="stats-bar">
                    <div className="stat-item">
                        <div className="stat-value" data-testid="total-downloads">{total}</div>
                        <div className="stat-label">Total Downloads</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{page}/{totalPages || 1}</div>
                        <div className="stat-label">Current Page</div>
                    </div>
                    {stats && (
                        <>
                            <div className="stat-item">
                                <div className="stat-value" style={{ color: '#FF00FF' }}>{stats.by_type?.game || 0}</div>
                                <div className="stat-label">Games</div>
                            </div>
                            <div className="stat-item">
                                <div className="stat-value" style={{ color: '#00FFFF' }}>{stats.by_type?.software || 0}</div>
                                <div className="stat-label">Software</div>
                            </div>
                            <div className="stat-item">
                                <div className="stat-value" style={{ color: '#FFFF00' }}>{stats.by_type?.movie || 0}</div>
                                <div className="stat-label">Movies</div>
                            </div>
                            <div className="stat-item">
                                <div className="stat-value" style={{ color: '#FF6600' }}>{stats.by_type?.tv_show || 0}</div>
                                <div className="stat-label">TV Shows</div>
                            </div>
                        </>
                    )}
                </div>

                {/* Search Bar */}
                <form onSubmit={handleSearch} className="search-bar" style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
                            <Search size={16} style={{ 
                                position: 'absolute', 
                                left: '0.75rem', 
                                top: '50%', 
                                transform: 'translateY(-50%)',
                                opacity: 0.5
                            }} />
                            <input
                                type="text"
                                value={searchInput}
                                onChange={(e) => setSearchInput(e.target.value)}
                                placeholder="Search downloads..."
                                className="form-input"
                                style={{ paddingLeft: '2.5rem' }}
                                data-testid="search-input"
                            />
                        </div>
                        <button type="submit" className="filter-btn active" data-testid="search-btn">
                            SEARCH
                        </button>
                        <button 
                            type="button" 
                            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                            className={`filter-btn ${showAdvancedFilters ? 'active' : ''}`}
                            data-testid="advanced-filters-btn"
                        >
                            <SlidersHorizontal size={14} style={{ marginRight: '0.25rem' }} />
                            FILTERS
                        </button>
                        {(searchQuery || dateFrom || dateTo || sizeMin || sizeMax || selectedCategory || selectedTags.length > 0) && (
                            <button 
                                type="button" 
                                onClick={handleClearFilters} 
                                className="filter-btn"
                                data-testid="clear-all-btn"
                            >
                                <X size={14} style={{ marginRight: '0.25rem' }} />
                                CLEAR ALL
                            </button>
                        )}
                    </div>
                    {searchQuery && (
                        <p style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.7 }}>
                            Showing results for: &quot;{searchQuery}&quot;
                        </p>
                    )}
                </form>

                {/* Advanced Filters Panel */}
                {showAdvancedFilters && (
                    <div className="advanced-filters-panel" style={{
                        border: '1px solid hsl(var(--border))',
                        padding: '1rem',
                        marginBottom: '1rem',
                        background: 'hsl(var(--card))'
                    }} data-testid="advanced-filters-panel">
                        <h3 style={{ fontSize: '0.875rem', marginBottom: '1rem', textTransform: 'uppercase' }}>
                            Advanced Filters
                        </h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                            {/* Sort By */}
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>SORT BY:</label>
                                <div style={{ position: 'relative' }}>
                                    <select
                                        value={sortBy}
                                        onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
                                        className="form-select"
                                        data-testid="sort-select"
                                    >
                                        {sortOptions.map(opt => (
                                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                                        ))}
                                    </select>
                                    <ChevronDown size={16} style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', opacity: 0.5 }} />
                                </div>
                            </div>

                            {/* Category */}
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>CATEGORY:</label>
                                <select
                                    value={selectedCategory}
                                    onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
                                    className="form-select"
                                    data-testid="category-select"
                                >
                                    <option value="">All Categories</option>
                                    {categories
                                        .filter(c => filter === 'all' || c.type === filter || c.type === 'all')
                                        .map(cat => (
                                            <option key={cat.id} value={cat.name}>{cat.name}</option>
                                        ))}
                                </select>
                            </div>

                            {/* File Size */}
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>FILE SIZE:</label>
                                <select
                                    value={`${sizeMin}|${sizeMax}`}
                                    onChange={(e) => { 
                                        const [min, max] = e.target.value.split('|');
                                        setSizeMin(min); 
                                        setSizeMax(max); 
                                        setPage(1); 
                                    }}
                                    className="form-select"
                                    data-testid="size-select"
                                >
                                    {sizePresets.map((preset, idx) => (
                                        <option key={idx} value={`${preset.min}|${preset.max}`}>{preset.label}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Date From */}
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>DATE FROM:</label>
                                <input
                                    type="date"
                                    value={dateFrom}
                                    onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
                                    className="form-input"
                                    data-testid="date-from-input"
                                />
                            </div>

                            {/* Date To */}
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>DATE TO:</label>
                                <input
                                    type="date"
                                    value={dateTo}
                                    onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
                                    className="form-input"
                                    data-testid="date-to-input"
                                />
                            </div>
                        </div>

                        {/* Tags Section */}
                        {popularTags.length > 0 && (
                            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid hsl(var(--border))' }}>
                                <label className="form-label" style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <Tag size={14} />
                                    FILTER BY TAGS:
                                </label>
                                {selectedTags.length > 0 && (
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                        {selectedTags.map(tag => (
                                            <span 
                                                key={tag}
                                                style={{
                                                    padding: '0.25rem 0.5rem',
                                                    background: 'hsl(var(--primary))',
                                                    color: 'hsl(var(--primary-foreground))',
                                                    fontSize: '0.75rem',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.25rem'
                                                }}
                                            >
                                                {tag}
                                                <button
                                                    onClick={() => { setSelectedTags(selectedTags.filter(t => t !== tag)); setPage(1); }}
                                                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'inherit' }}
                                                >
                                                    <X size={12} />
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                )}
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {popularTags.slice(0, 15).map(tag => (
                                        <button
                                            key={tag.name}
                                            onClick={() => {
                                                if (selectedTags.includes(tag.name)) {
                                                    setSelectedTags(selectedTags.filter(t => t !== tag.name));
                                                } else {
                                                    setSelectedTags([...selectedTags, tag.name]);
                                                }
                                                setPage(1);
                                            }}
                                            className={`filter-btn ${selectedTags.includes(tag.name) ? 'active' : ''}`}
                                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                                            data-testid={`tag-${tag.name}`}
                                        >
                                            {tag.name} ({tag.count})
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Filter Bar */}
                <div className="filter-bar">
                    <span style={{ opacity: 0.7 }}>FILTER BY TYPE:</span>
                    {['all', 'game', 'software', 'movie', 'tv_show'].map((type) => (
                        <button
                            key={type}
                            className={`filter-btn ${filter === type ? 'active' : ''}`}
                            onClick={() => handleFilterChange(type)}
                            data-testid={`filter-${type}`}
                        >
                            {type === 'all' ? 'ALL' : typeLabels[type]}
                        </button>
                    ))}
                </div>

                {/* Downloads Table */}
                {loading ? (
                    <div className="loading-state">
                        <p className="loading-text pixel-font" style={{ fontSize: '0.75rem' }}>
                            LOADING DATA...
                        </p>
                    </div>
                ) : downloads.length === 0 ? (
                    <div className="empty-state">
                        <p className="pixel-font" style={{ fontSize: '0.75rem' }}>NO DOWNLOADS AVAILABLE</p>
                        <p style={{ marginTop: '1rem' }}>
                            {searchQuery ? 'Try a different search term' : 'Be the first to submit!'}
                        </p>
                    </div>
                ) : (
                    <>
                        <table className="downloads-table" data-testid="downloads-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '40%' }}>
                                        <Download size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                                        Download Name
                                    </th>
                                    <th style={{ width: '12%' }}>Date</th>
                                    <th style={{ width: '12%' }}>Type</th>
                                    <th style={{ width: '12%' }}>Size</th>
                                    <th style={{ width: '12%' }}>Site</th>
                                    <th style={{ width: '12%' }}>
                                        <TrendingUp size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                                        Downloads
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {downloads.map((download, index) => {
                                    const TypeIcon = typeIcons[download.type] || Download;
                                    return (
                                        <tr key={download.id} className="table-row-hover" data-testid={`download-row-${index}`}>
                                            <td>
                                                <a 
                                                    href={download.download_link} 
                                                    target="_blank" 
                                                    rel="noopener noreferrer"
                                                    onClick={() => handleDownloadClick(download.id)}
                                                    data-testid={`download-link-${index}`}
                                                    title={download.description || download.name}
                                                >
                                                    {download.name}
                                                </a>
                                                {download.description && (
                                                    <span style={{ 
                                                        display: 'block', 
                                                        fontSize: '0.75rem', 
                                                        opacity: 0.6,
                                                        marginTop: '0.25rem'
                                                    }}>
                                                        {download.description}
                                                    </span>
                                                )}
                                            </td>
                                            <td>{download.submission_date}</td>
                                            <td>
                                                <span className={`type-badge type-${download.type}`}>
                                                    <TypeIcon size={12} style={{ display: 'inline', marginRight: '0.25rem' }} />
                                                    {typeLabels[download.type] || download.type}
                                                </span>
                                            </td>
                                            <td style={{ fontSize: '0.875rem' }}>
                                                {download.file_size || '-'}
                                            </td>
                                            <td>
                                                <span className="download-count" style={{ 
                                                    color: 'hsl(var(--accent))',
                                                    fontWeight: 'bold'
                                                }}>
                                                    {formatNumber(download.download_count || 0)}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="pagination" data-testid="pagination">
                                {renderPagination()}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
