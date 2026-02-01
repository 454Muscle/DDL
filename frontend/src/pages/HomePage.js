import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Download, Gamepad2, Monitor, Film, Tv, Search, TrendingUp } from 'lucide-react';

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

const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
};

export default function HomePage() {
    const [downloads, setDownloads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);
    const [filter, setFilter] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [searchInput, setSearchInput] = useState('');
    const [stats, setStats] = useState(null);

    const fetchDownloads = useCallback(async () => {
        setLoading(true);
        try {
            const params = { page, limit: 50 };
            if (filter !== 'all') {
                params.type_filter = filter;
            }
            if (searchQuery.trim()) {
                params.search = searchQuery.trim();
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
    }, [page, filter, searchQuery]);

    const fetchStats = async () => {
        try {
            const response = await axios.get(`${API}/stats`);
            setStats(response.data);
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    useEffect(() => {
        fetchDownloads();
    }, [fetchDownloads]);

    useEffect(() => {
        fetchStats();
    }, []);

    const handleFilterChange = (newFilter) => {
        setFilter(newFilter);
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

    const handleDownloadClick = async (downloadId) => {
        try {
            await axios.post(`${API}/downloads/${downloadId}/increment`);
            // Update local state
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
                        {searchQuery && (
                            <button 
                                type="button" 
                                onClick={handleClearSearch} 
                                className="filter-btn"
                                data-testid="clear-search-btn"
                            >
                                CLEAR
                            </button>
                        )}
                    </div>
                    {searchQuery && (
                        <p style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.7 }}>
                            Showing results for: "{searchQuery}"
                        </p>
                    )}
                </form>

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
