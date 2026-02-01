import { useState, useEffect } from 'react';
import axios from 'axios';
import { Download, Gamepad2, Monitor, Film, Tv } from 'lucide-react';

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

export default function HomePage() {
    const [downloads, setDownloads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);
    const [filter, setFilter] = useState('all');

    const fetchDownloads = async () => {
        setLoading(true);
        try {
            const params = { page, limit: 50 };
            if (filter !== 'all') {
                params.type_filter = filter;
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
    };

    useEffect(() => {
        fetchDownloads();
    }, [page, filter]);

    const handleFilterChange = (newFilter) => {
        setFilter(newFilter);
        setPage(1);
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
                </div>

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
                        <p style={{ marginTop: '1rem' }}>Be the first to submit!</p>
                    </div>
                ) : (
                    <>
                        <table className="downloads-table" data-testid="downloads-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '50%' }}>
                                        <Download size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                                        Download Name
                                    </th>
                                    <th style={{ width: '25%' }}>Submission Date</th>
                                    <th style={{ width: '25%' }}>Type</th>
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
                                                    data-testid={`download-link-${index}`}
                                                >
                                                    {download.name}
                                                </a>
                                            </td>
                                            <td>{download.submission_date}</td>
                                            <td>
                                                <span className={`type-badge type-${download.type}`}>
                                                    <TypeIcon size={12} style={{ display: 'inline', marginRight: '0.25rem' }} />
                                                    {typeLabels[download.type] || download.type}
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
