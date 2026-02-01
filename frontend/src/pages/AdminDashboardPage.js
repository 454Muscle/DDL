import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useTheme } from '../context/ThemeContext';
import { 
    Shield, 
    Check, 
    X, 
    Trash2, 
    Palette, 
    Sun, 
    Moon,
    RefreshCw,
    LogOut,
    ExternalLink,
    Database,
    Loader2
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusColors = {
    pending: '#FFFF00',
    approved: '#00FF41',
    rejected: '#FF0000'
};

const accentPresets = [
    { name: 'Matrix Green', color: '#00FF41' },
    { name: 'Cyber Magenta', color: '#FF00FF' },
    { name: 'Electric Cyan', color: '#00FFFF' },
    { name: 'Warning Yellow', color: '#FFFF00' },
    { name: 'Neon Orange', color: '#FF6600' },
    { name: 'Classic Blue', color: '#0066FF' }
];

export default function AdminDashboardPage() {
    const navigate = useNavigate();
    const { theme, updateTheme } = useTheme();
    const [submissions, setSubmissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [statusFilter, setStatusFilter] = useState('pending');
    const [customAccent, setCustomAccent] = useState(theme.accent_color);
    const [seeding, setSeeding] = useState(false);
    const [stats, setStats] = useState(null);

    useEffect(() => {
        // Check auth
        if (!sessionStorage.getItem('admin_auth')) {
            navigate('/admin');
            return;
        }
        fetchSubmissions();
        fetchStats();
    }, [page, statusFilter, navigate]);

    const fetchSubmissions = async () => {
        setLoading(true);
        try {
            const params = { page, limit: 50 };
            if (statusFilter !== 'all') {
                params.status = statusFilter;
            }
            const response = await axios.get(`${API}/admin/submissions`, { params });
            setSubmissions(response.data.items);
            setTotalPages(response.data.pages);
        } catch (error) {
            console.error('Error fetching submissions:', error);
            toast.error('Failed to load submissions');
        } finally {
            setLoading(false);
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

    const handleApprove = async (id) => {
        try {
            await axios.post(`${API}/admin/submissions/${id}/approve`);
            toast.success('Submission approved and published!');
            fetchSubmissions();
            fetchStats();
        } catch (error) {
            console.error('Approve error:', error);
            toast.error('Failed to approve submission');
        }
    };

    const handleReject = async (id) => {
        try {
            await axios.post(`${API}/admin/submissions/${id}/reject`);
            toast.success('Submission rejected');
            fetchSubmissions();
        } catch (error) {
            console.error('Reject error:', error);
            toast.error('Failed to reject submission');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this submission?')) return;
        try {
            await axios.delete(`${API}/admin/submissions/${id}`);
            toast.success('Submission deleted');
            fetchSubmissions();
        } catch (error) {
            console.error('Delete error:', error);
            toast.error('Failed to delete submission');
        }
    };

    const handleThemeToggle = async () => {
        const newMode = theme.mode === 'dark' ? 'light' : 'dark';
        try {
            await updateTheme({ mode: newMode });
            toast.success(`Theme switched to ${newMode} mode`);
        } catch (error) {
            toast.error('Failed to update theme');
        }
    };

    const handleAccentChange = async (color) => {
        setCustomAccent(color);
        try {
            await updateTheme({ accent_color: color });
            toast.success('Accent color updated');
        } catch (error) {
            toast.error('Failed to update accent color');
        }
    };

    const handleSeedDatabase = async () => {
        if (!window.confirm('This will populate the database with 5000 sample downloads. Continue?')) return;
        setSeeding(true);
        try {
            const response = await axios.post(`${API}/admin/seed`);
            if (response.data.success) {
                toast.success(response.data.message);
                fetchStats();
            } else {
                toast.info(response.data.message);
            }
        } catch (error) {
            console.error('Seed error:', error);
            toast.error('Failed to seed database');
        } finally {
            setSeeding(false);
        }
    };

    const handleLogout = () => {
        sessionStorage.removeItem('admin_auth');
        toast.success('Logged out');
        navigate('/admin');
    };

    return (
        <div className="admin-container" data-testid="admin-dashboard">
            {/* Header */}
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '1.5rem',
                flexWrap: 'wrap',
                gap: '1rem'
            }}>
                <h1 className="pixel-font neon-glow" style={{ fontSize: '1rem' }}>
                    <Shield size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
                    ADMIN CONTROL PANEL
                </h1>
                <button 
                    onClick={handleLogout}
                    className="action-btn reject"
                    data-testid="admin-logout-btn"
                >
                    <LogOut size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                    LOGOUT
                </button>
            </div>

            {/* Stats Overview */}
            {stats && (
                <div className="admin-card" style={{ marginBottom: '1.5rem' }}>
                    <h2 className="admin-title">DATABASE STATISTICS</h2>
                    <div className="stats-bar" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                        <div className="stat-item">
                            <div className="stat-value">{stats.total}</div>
                            <div className="stat-label">Total Items</div>
                        </div>
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
                    </div>
                    
                    {/* Seed Button */}
                    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid hsl(var(--border))' }}>
                        <button
                            onClick={handleSeedDatabase}
                            disabled={seeding}
                            className="action-btn approve"
                            style={{ padding: '0.75rem 1.5rem' }}
                            data-testid="seed-database-btn"
                        >
                            {seeding ? (
                                <>
                                    <Loader2 size={14} style={{ display: 'inline', marginRight: '0.5rem', animation: 'spin 1s linear infinite' }} />
                                    SEEDING DATABASE...
                                </>
                            ) : (
                                <>
                                    <Database size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                                    SEED DATABASE (5000 ITEMS)
                                </>
                            )}
                        </button>
                        <p style={{ fontSize: '0.75rem', opacity: 0.6, marginTop: '0.5rem' }}>
                            Populates database with sample games, software, movies, and TV shows
                        </p>
                    </div>
                </div>
            )}

            {/* Theme Editor Card */}
            <div className="admin-card" data-testid="theme-editor">
                <h2 className="admin-title">
                    <Palette size={18} style={{ display: 'inline', marginRight: '0.5rem' }} />
                    THEME EDITOR
                </h2>
                
                <div className="theme-editor">
                    {/* Mode Toggle */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span>MODE:</span>
                        <button
                            onClick={handleThemeToggle}
                            className={`filter-btn ${theme.mode === 'dark' ? 'active' : ''}`}
                            data-testid="theme-dark-btn"
                        >
                            <Moon size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                            DARK
                        </button>
                        <button
                            onClick={handleThemeToggle}
                            className={`filter-btn ${theme.mode === 'light' ? 'active' : ''}`}
                            data-testid="theme-light-btn"
                        >
                            <Sun size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                            LIGHT
                        </button>
                    </div>

                    {/* Accent Color */}
                    <div>
                        <p style={{ marginBottom: '0.5rem' }}>ACCENT COLOR:</p>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                            {accentPresets.map(preset => (
                                <button
                                    key={preset.color}
                                    onClick={() => handleAccentChange(preset.color)}
                                    style={{
                                        width: '40px',
                                        height: '40px',
                                        background: preset.color,
                                        border: customAccent === preset.color ? '3px solid white' : '1px solid hsl(var(--border))',
                                        cursor: 'pointer'
                                    }}
                                    title={preset.name}
                                    data-testid={`accent-${preset.name.toLowerCase().replace(' ', '-')}`}
                                />
                            ))}
                            <div className="color-picker-group">
                                <input
                                    type="color"
                                    value={customAccent}
                                    onChange={(e) => handleAccentChange(e.target.value)}
                                    className="color-picker"
                                    data-testid="custom-accent-picker"
                                />
                                <span style={{ fontSize: '0.75rem' }}>CUSTOM</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Submissions Card */}
            <div className="admin-card" data-testid="submissions-manager">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    <h2 className="admin-title" style={{ margin: 0, border: 'none', padding: 0 }}>
                        PENDING SUBMISSIONS
                    </h2>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button 
                            onClick={fetchSubmissions}
                            className="action-btn approve"
                            data-testid="refresh-submissions-btn"
                        >
                            <RefreshCw size={14} />
                        </button>
                    </div>
                </div>

                {/* Status Filter */}
                <div className="filter-bar" style={{ marginTop: '1rem' }}>
                    <span style={{ opacity: 0.7 }}>STATUS:</span>
                    {['all', 'pending', 'approved', 'rejected'].map(status => (
                        <button
                            key={status}
                            className={`filter-btn ${statusFilter === status ? 'active' : ''}`}
                            onClick={() => { setStatusFilter(status); setPage(1); }}
                            data-testid={`status-filter-${status}`}
                        >
                            {status.toUpperCase()}
                        </button>
                    ))}
                </div>

                {/* Submissions Table */}
                {loading ? (
                    <div className="loading-state">
                        <p className="loading-text">LOADING...</p>
                    </div>
                ) : submissions.length === 0 ? (
                    <div className="empty-state">
                        <p>NO SUBMISSIONS FOUND</p>
                    </div>
                ) : (
                    <table className="downloads-table" style={{ marginTop: '1rem' }}>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Size</th>
                                <th>Link</th>
                                <th>Status</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {submissions.map((sub, index) => (
                                <tr key={sub.id} data-testid={`submission-row-${index}`}>
                                    <td>
                                        {sub.name}
                                        {sub.description && (
                                            <span style={{ 
                                                display: 'block', 
                                                fontSize: '0.75rem', 
                                                opacity: 0.6 
                                            }}>
                                                {sub.description}
                                            </span>
                                        )}
                                    </td>
                                    <td>
                                        <span className={`type-badge type-${sub.type}`}>
                                            {sub.type}
                                        </span>
                                    </td>
                                    <td style={{ fontSize: '0.875rem' }}>{sub.file_size || '-'}</td>
                                    <td>
                                        <a 
                                            href={sub.download_link} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                                        >
                                            <ExternalLink size={12} />
                                            View
                                        </a>
                                    </td>
                                    <td>
                                        <span style={{ color: statusColors[sub.status] || '#fff' }}>
                                            {sub.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>{sub.submission_date}</td>
                                    <td>
                                        {sub.status === 'pending' && (
                                            <>
                                                <button
                                                    onClick={() => handleApprove(sub.id)}
                                                    className="action-btn approve"
                                                    data-testid={`approve-btn-${index}`}
                                                >
                                                    <Check size={14} />
                                                </button>
                                                <button
                                                    onClick={() => handleReject(sub.id)}
                                                    className="action-btn reject"
                                                    data-testid={`reject-btn-${index}`}
                                                >
                                                    <X size={14} />
                                                </button>
                                            </>
                                        )}
                                        <button
                                            onClick={() => handleDelete(sub.id)}
                                            className="action-btn reject"
                                            data-testid={`delete-btn-${index}`}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="pagination">
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                            <button
                                key={p}
                                className={`page-btn ${page === p ? 'active' : ''}`}
                                onClick={() => setPage(p)}
                            >
                                [ {p} ]
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
