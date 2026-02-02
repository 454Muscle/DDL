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
    Loader2,
    Settings,
    Clock,
    Trophy,
    Plus,
    Star
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

const typeOptions = ['game', 'software', 'movie', 'tv_show'];

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
    const [siteSettings, setSiteSettings] = useState({ 
        daily_submission_limit: 10,
        top_downloads_enabled: true,
        top_downloads_count: 5,
        sponsored_downloads: []
    });
    const [newLimit, setNewLimit] = useState(10);
    const [topEnabled, setTopEnabled] = useState(true);
    const [topCount, setTopCount] = useState(5);
    const [sponsoredDownloads, setSponsoredDownloads] = useState([]);
    const [newSponsored, setNewSponsored] = useState({ name: '', download_link: '', type: 'software', description: '' });

    const [recaptchaSiteKey, setRecaptchaSiteKey] = useState('');
    const [recaptchaSecretKey, setRecaptchaSecretKey] = useState('');
    const [recaptchaEnableSubmit, setRecaptchaEnableSubmit] = useState(false);
    const [recaptchaEnableAuth, setRecaptchaEnableAuth] = useState(false);

    const [resendApiKey, setResendApiKey] = useState('');
    const [resendSenderEmail, setResendSenderEmail] = useState('');
    const [adminEmail, setAdminEmail] = useState('');
    const [adminInitPassword, setAdminInitPassword] = useState('');
    const [adminCurrentPassword, setAdminCurrentPassword] = useState('');
    const [adminNewPassword, setAdminNewPassword] = useState('');

    useEffect(() => {
        if (!sessionStorage.getItem('admin_auth')) {
            navigate('/admin');
            return;
        }
        fetchSubmissions();
        fetchStats();
        fetchSiteSettings();
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

    const fetchSiteSettings = async () => {
        try {
            const response = await axios.get(`${API}/settings`);
            setSiteSettings(response.data);
            setNewLimit(response.data.daily_submission_limit || 10);
            setTopEnabled(response.data.top_downloads_enabled !== false);
            setTopCount(response.data.top_downloads_count || 5);
            setSponsoredDownloads(response.data.sponsored_downloads || []);
            setRecaptchaSiteKey(response.data.recaptcha_site_key || '');
            // secret key is not returned from /api/settings; keep current input value
            setRecaptchaEnableSubmit(!!response.data.recaptcha_enable_submit);
            setRecaptchaEnableAuth(!!response.data.recaptcha_enable_auth);
            setAdminEmail(response.data.admin_email || '');
            setResendSenderEmail(response.data.resend_sender_email || '');
        } catch (error) {
            console.error('Error fetching settings:', error);
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

    const handleUpdateRateLimit = async () => {
        const limitValue = Math.max(5, Math.min(100, parseInt(newLimit) || 10));
        try {
            const response = await axios.put(`${API}/admin/settings`, {
                daily_submission_limit: limitValue
            });
            setSiteSettings(response.data);
            setNewLimit(response.data.daily_submission_limit);
            toast.success(`Daily submission limit updated to ${response.data.daily_submission_limit}`);
        } catch (error) {
            console.error('Update settings error:', error);
            toast.error('Failed to update settings');
        }
    };

    const handleUpdateTopDownloads = async () => {
        const countValue = Math.max(5, Math.min(20, parseInt(topCount) || 5));
        try {
            const response = await axios.put(`${API}/admin/settings`, {
                top_downloads_enabled: topEnabled,
                top_downloads_count: countValue
            });
            setSiteSettings(response.data);
            setTopEnabled(response.data.top_downloads_enabled);
            setTopCount(response.data.top_downloads_count);
            toast.success('Top downloads settings updated');
        } catch (error) {
            console.error('Update settings error:', error);
            toast.error('Failed to update settings');
        }
    };

    const handleAddSponsored = async () => {
        if (!newSponsored.name.trim() || !newSponsored.download_link.trim()) {
            toast.error('Name and download link are required');
            return;
        }
        if (sponsoredDownloads.length >= 5) {
            toast.error('Maximum 5 sponsored downloads allowed');
            return;
        }
        
        const updatedSponsored = [...sponsoredDownloads, { ...newSponsored, id: `sponsored-${Date.now()}` }];
        try {
            const response = await axios.put(`${API}/admin/settings`, {
                sponsored_downloads: updatedSponsored
            });
            setSponsoredDownloads(response.data.sponsored_downloads || []);
            setNewSponsored({ name: '', download_link: '', type: 'software', description: '' });
            toast.success('Sponsored download added');
        } catch (error) {
            console.error('Add sponsored error:', error);
            toast.error('Failed to add sponsored download');
        }
    };

    const handleRemoveSponsored = async (index) => {
        const updatedSponsored = sponsoredDownloads.filter((_, i) => i !== index);
        try {
            const response = await axios.put(`${API}/admin/settings`, {
                sponsored_downloads: updatedSponsored
            });
            setSponsoredDownloads(response.data.sponsored_downloads || []);
            toast.success('Sponsored download removed');
        } catch (error) {
            console.error('Remove sponsored error:', error);
            toast.error('Failed to remove sponsored download');
        }
    };


    const handleUpdateRecaptcha = async () => {
        try {
            const payload = {
                recaptcha_site_key: recaptchaSiteKey,
                recaptcha_secret_key: recaptchaSecretKey,
                recaptcha_enable_submit: recaptchaEnableSubmit,
                recaptcha_enable_auth: recaptchaEnableAuth
            };
            const response = await axios.put(`${API}/admin/settings`, payload);
            setSiteSettings(response.data);
            setRecaptchaSiteKey(response.data.recaptcha_site_key || '');
            setRecaptchaSecretKey(response.data.recaptcha_secret_key || '');
            setRecaptchaEnableSubmit(!!response.data.recaptcha_enable_submit);
            setRecaptchaEnableAuth(!!response.data.recaptcha_enable_auth);
            toast.success('reCAPTCHA settings updated');
        } catch (error) {
            console.error('Update reCAPTCHA error:', error);
            const message = error.response?.data?.detail || 'Failed to update reCAPTCHA settings';
            toast.error(message);
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
                                    <Loader2 size={14} className="animate-spin" style={{ display: 'inline', marginRight: '0.5rem' }} />
                                    SEEDING DATABASE...
                                </>
                            ) : (
                                <>
                                    <Database size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                                    SEED DATABASE (5000 ITEMS)
                                </>
                            )}
                        </button>
                    </div>
                </div>
            )}

            {/* Site Settings Card */}
            <div className="admin-card" data-testid="site-settings">
                <h2 className="admin-title">
                    <Settings size={18} style={{ display: 'inline', marginRight: '0.5rem' }} />
                    SITE SETTINGS
                </h2>
                
                {/* Rate Limit */}
                <div style={{ marginBottom: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1rem', flexWrap: 'wrap' }}>
                        <div style={{ flex: 1, minWidth: '200px' }}>
                            <label className="form-label" style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <Clock size={14} />
                                DAILY SUBMISSION LIMIT (5-100):
                            </label>
                            <input
                                type="number"
                                min="5"
                                max="100"
                                value={newLimit}
                                onChange={(e) => setNewLimit(e.target.value)}
                                className="form-input"
                                style={{ width: '100%' }}
                                data-testid="rate-limit-input"
                            />
                        </div>
                        <button
                            onClick={handleUpdateRateLimit}
                            className="action-btn approve"
                            style={{ padding: '0.75rem 1.5rem', marginBottom: '0.25rem' }}
                            data-testid="update-rate-limit-btn"
                        >
                            UPDATE
                        </button>
                    </div>
                </div>

                {/* Top Downloads Settings */}
                <div style={{ borderTop: '1px solid hsl(var(--border))', paddingTop: '1.5rem' }}>
                    <h3 style={{ fontSize: '0.875rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Trophy size={16} />
                        TOP DOWNLOADS SETTINGS
                    </h3>
                    
                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                        <div>
                            <label className="form-label" style={{ fontSize: '0.75rem' }}>DISPLAY:</label>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button
                                    onClick={() => setTopEnabled(true)}
                                    className={`filter-btn ${topEnabled ? 'active' : ''}`}
                                    data-testid="top-enabled-btn"
                                >
                                    ENABLED
                                </button>
                                <button
                                    onClick={() => setTopEnabled(false)}
                                    className={`filter-btn ${!topEnabled ? 'active' : ''}`}
                                    data-testid="top-disabled-btn"
                                >
                                    DISABLED
                                </button>
                            </div>
                        </div>
                        <div style={{ minWidth: '150px' }}>
                            <label className="form-label" style={{ fontSize: '0.75rem' }}>COUNT (5-20):</label>
                            <input
                                type="number"
                                min="5"
                                max="20"
                                value={topCount}
                                onChange={(e) => setTopCount(e.target.value)}
                                className="form-input"
                                style={{ width: '100%' }}
                                data-testid="top-count-input"
                            />
                        </div>
                        <button
                            onClick={handleUpdateTopDownloads}
                            className="action-btn approve"
                            style={{ padding: '0.75rem 1.5rem', marginBottom: '0.25rem' }}
                            data-testid="update-top-downloads-btn"
                        >
                            UPDATE
                        </button>
                    </div>
                </div>
            </div>

            {/* Sponsored Downloads Card */}
            <div className="admin-card" data-testid="sponsored-downloads">
                <h2 className="admin-title">
                    <Star size={18} style={{ display: 'inline', marginRight: '0.5rem', color: '#FFD700' }} />
                    SPONSORED DOWNLOADS (1-5)
                </h2>
                <p style={{ fontSize: '0.75rem', opacity: 0.7, marginBottom: '1rem' }}>
                    Sponsored downloads appear first in the Top Downloads section
                </p>

                {/* Current Sponsored List */}
                {sponsoredDownloads.length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                        <table className="downloads-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Name</th>
                                    <th>Type</th>
                                    <th>Link</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sponsoredDownloads.map((item, index) => (
                                    <tr key={index} data-testid={`sponsored-row-${index}`}>
                                        <td style={{ color: '#FFD700', fontWeight: 'bold' }}>#{index + 1}</td>
                                        <td>
                                            {item.name}
                                            {item.description && (
                                                <span style={{ display: 'block', fontSize: '0.75rem', opacity: 0.6 }}>
                                                    {item.description}
                                                </span>
                                            )}
                                        </td>
                                        <td>
                                            <span className={`type-badge type-${item.type}`}>{item.type}</span>
                                        </td>
                                        <td>
                                            <a href={item.download_link} target="_blank" rel="noopener noreferrer">
                                                <ExternalLink size={12} /> View
                                            </a>
                                        </td>
                                        <td>
                                            <button
                                                onClick={() => handleRemoveSponsored(index)}
                                                className="action-btn reject"
                                                data-testid={`remove-sponsored-${index}`}
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Add New Sponsored */}
                {sponsoredDownloads.length < 5 && (
                    <div style={{ 
                        border: '1px dashed hsl(var(--border))', 
                        padding: '1rem',
                        background: 'hsl(var(--background))'
                    }}>
                        <h4 style={{ fontSize: '0.75rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Plus size={14} />
                            ADD SPONSORED DOWNLOAD ({sponsoredDownloads.length}/5)
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>NAME *</label>
                                <input
                                    type="text"
                                    value={newSponsored.name}
                                    onChange={(e) => setNewSponsored({ ...newSponsored, name: e.target.value })}
                                    className="form-input"
                                    placeholder="Download name"
                                    data-testid="sponsored-name-input"
                                />
                            </div>
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>DOWNLOAD LINK *</label>
                                <input
                                    type="url"
                                    value={newSponsored.download_link}
                                    onChange={(e) => setNewSponsored({ ...newSponsored, download_link: e.target.value })}
                                    className="form-input"
                                    placeholder="https://..."
                                    data-testid="sponsored-link-input"
                                />
                            </div>
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>TYPE</label>
                                <select
                                    value={newSponsored.type}
                                    onChange={(e) => setNewSponsored({ ...newSponsored, type: e.target.value })}
                                    className="form-select"
                                    data-testid="sponsored-type-select"
                                >
                                    {typeOptions.map(t => (
                                        <option key={t} value={t}>{t}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="form-label" style={{ fontSize: '0.75rem' }}>DESCRIPTION</label>
                                <input
                                    type="text"
                                    value={newSponsored.description}
                                    onChange={(e) => setNewSponsored({ ...newSponsored, description: e.target.value })}
                                    className="form-input"
                                    placeholder="Optional description"
                                    data-testid="sponsored-description-input"
                                />
                            </div>
                        </div>
                        <button
                            onClick={handleAddSponsored}
                            className="action-btn approve"
                            style={{ marginTop: '1rem', padding: '0.75rem 1.5rem' }}
                            data-testid="add-sponsored-btn"

            {/* Resend Email Settings Card */}
            <div className="admin-card" data-testid="resend-settings">
                <h2 className="admin-title">Resend Email</h2>
                <p style={{ fontSize: '0.75rem', opacity: 0.7, marginBottom: '1rem' }}>
                    Create an API key at https://resend.com/api-keys (Dashboard → API Keys). In test mode, Resend may require verifying your sender domain/email.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>RESEND API KEY</label>
                        <input
                            type="password"
                            value={resendApiKey}
                            onChange={(e) => setResendApiKey(e.target.value)}
                            className="form-input"
                            placeholder="re_..."
                            data-testid="resend-api-key-input"
                        />
                    </div>
                    <div>
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>SENDER EMAIL (FROM)</label>
                        <input
                            type="email"
                            value={resendSenderEmail}
                            onChange={(e) => setResendSenderEmail(e.target.value)}
                            className="form-input"
                            placeholder="onboarding@resend.dev"
                            data-testid="resend-sender-email-input"
                        />
                    </div>
                </div>

                <button
                    onClick={handleUpdateResend}
                    className="action-btn approve"
                    style={{ padding: '0.75rem 1.5rem', marginTop: '1rem' }}
                    data-testid="update-resend-btn"
                >
                    UPDATE RESEND
                </button>
            </div>

            {/* Admin Credentials Card */}
            <div className="admin-card" data-testid="admin-credentials">
                <h2 className="admin-title">Admin Credentials</h2>
                <p style={{ fontSize: '0.75rem', opacity: 0.7, marginBottom: '1rem' }}>
                    Set the admin email (required). Password changes require current password and are confirmed via a magic link sent to the admin email.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>ADMIN EMAIL</label>
                        <input
                            type="email"
                            value={adminEmail}
                            onChange={(e) => setAdminEmail(e.target.value)}
                            className="form-input"
                            placeholder="admin@example.com"
                            data-testid="admin-email-input"
                        />
                    </div>
                    <div>
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>INITIAL ADMIN PASSWORD (FIRST TIME ONLY)</label>
                        <input
                            type="password"
                            value={adminInitPassword}
                            onChange={(e) => setAdminInitPassword(e.target.value)}
                            className="form-input"
                            placeholder="••••••••"
                            data-testid="admin-init-password-input"
                        />
                    </div>
                </div>

                <button
                    onClick={handleInitAdmin}
                    className="action-btn approve"
                    style={{ padding: '0.75rem 1.5rem', marginTop: '1rem' }}
                    data-testid="admin-init-btn"
                >
                    INITIALIZE ADMIN
                </button>

                <div style={{ borderTop: '1px solid hsl(var(--border))', marginTop: '1.5rem', paddingTop: '1.5rem' }}>
                    <h3 style={{ fontSize: '0.875rem', marginBottom: '0.75rem' }}>Request Password Change</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div>
                            <label className="form-label" style={{ fontSize: '0.75rem' }}>CURRENT PASSWORD</label>
                            <input
                                type="password"
                                value={adminCurrentPassword}
                                onChange={(e) => setAdminCurrentPassword(e.target.value)}
                                className="form-input"
                                placeholder="••••••••"
                                data-testid="admin-current-password-input"
                            />
                        </div>
                        <div>
                            <label className="form-label" style={{ fontSize: '0.75rem' }}>NEW PASSWORD</label>
                            <input
                                type="password"
                                value={adminNewPassword}
                                onChange={(e) => setAdminNewPassword(e.target.value)}
                                className="form-input"
                                placeholder="••••••••"
                                data-testid="admin-new-password-input"
                            />
                        </div>
                    </div>

                    <button
                        onClick={handleRequestAdminPasswordChange}
                        className="action-btn approve"
                        style={{ padding: '0.75rem 1.5rem', marginTop: '1rem' }}
                        data-testid="admin-request-password-change-btn"
                    >
                        SEND CONFIRMATION EMAIL
                    </button>
                </div>
            </div>

                        >
                            <Plus size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                            ADD SPONSORED
                        </button>
                    </div>
                )}
            </div>


            {/* Google reCAPTCHA Settings Card */}
            <div className="admin-card" data-testid="recaptcha-settings">
                <h2 className="admin-title">Google reCAPTCHA 2.0</h2>
                <p style={{ fontSize: '0.75rem', opacity: 0.7, marginBottom: '1rem' }}>
                    Create keys at https://www.google.com/recaptcha/admin/create and choose reCAPTCHA v2 “I’m not a robot”. Add your site domain(s) + localhost for testing.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>SITE KEY (PUBLIC)</label>
                        <input
                            type="text"
                            value={recaptchaSiteKey}
                            onChange={(e) => setRecaptchaSiteKey(e.target.value)}
                            className="form-input"
                            placeholder="6Le..."
                            data-testid="recaptcha-site-key-input"
                        />
                    </div>
                    <div>
                        <label className="form-label" style={{ fontSize: '0.75rem' }}>SECRET KEY (PRIVATE)</label>
                        <input
                            type="password"
                            value={recaptchaSecretKey}
                            onChange={(e) => setRecaptchaSecretKey(e.target.value)}
                            className="form-input"
                            placeholder="6Le..."
                            data-testid="recaptcha-secret-key-input"
                        />
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem' }}>
                        <input
                            type="checkbox"
                            checked={recaptchaEnableSubmit}
                            onChange={(e) => setRecaptchaEnableSubmit(e.target.checked)}
                            data-testid="recaptcha-enable-submit"
                        />
                        Enable on Submit page
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem' }}>
                        <input
                            type="checkbox"
                            checked={recaptchaEnableAuth}
                            onChange={(e) => setRecaptchaEnableAuth(e.target.checked)}
                            data-testid="recaptcha-enable-auth"
                        />
                        Enable on Login/Register
                    </label>
                </div>

                <button
                    onClick={handleUpdateRecaptcha}
                    className="action-btn approve"
                    style={{ padding: '0.75rem 1.5rem', marginTop: '1rem' }}
                    data-testid="update-recaptcha-btn"
                >
                    UPDATE reCAPTCHA
                </button>
            </div>

            {/* Theme Editor Card */}
            <div className="admin-card" data-testid="theme-editor">
                <h2 className="admin-title">
                    <Palette size={18} style={{ display: 'inline', marginRight: '0.5rem' }} />
                    THEME EDITOR
                </h2>
                
                <div className="theme-editor">
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
                    <button 
                        onClick={fetchSubmissions}
                        className="action-btn approve"
                        data-testid="refresh-submissions-btn"
                    >
                        <RefreshCw size={14} />
                    </button>
                </div>

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
                                            <span style={{ display: 'block', fontSize: '0.75rem', opacity: 0.6 }}>
                                                {sub.description}
                                            </span>
                                        )}
                                    </td>
                                    <td><span className={`type-badge type-${sub.type}`}>{sub.type}</span></td>
                                    <td style={{ fontSize: '0.875rem' }}>{sub.file_size || '-'}</td>
                                    <td>
                                        <a href={sub.download_link} target="_blank" rel="noopener noreferrer">
                                            <ExternalLink size={12} /> View
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
                                                <button onClick={() => handleApprove(sub.id)} className="action-btn approve" data-testid={`approve-btn-${index}`}>
                                                    <Check size={14} />
                                                </button>
                                                <button onClick={() => handleReject(sub.id)} className="action-btn reject" data-testid={`reject-btn-${index}`}>
                                                    <X size={14} />
                                                </button>
                                            </>
                                        )}
                                        <button onClick={() => handleDelete(sub.id)} className="action-btn reject" data-testid={`delete-btn-${index}`}>
                                            <Trash2 size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                {totalPages > 1 && (
                    <div className="pagination">
                        {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => i + 1).map(p => (
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
