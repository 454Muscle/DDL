import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { Terminal, Send, ArrowLeft, HelpCircle, AlertTriangle, RefreshCw, Tag, X, User } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const typeOptions = [
    { value: 'game', label: 'Game' },
    { value: 'software', label: 'Software' },
    { value: 'movie', label: 'Movie' },
    { value: 'tv_show', label: 'TV Show' }
];

export default function SubmitPage() {
    const navigate = useNavigate();
    const { user, isLoggedIn, logout } = useAuth();
    const [formData, setFormData] = useState({
        name: '',
        download_link: '',
        type: 'game',
        file_size: '',
        description: '',
        category: '',
        tags: [],
        submitter_email: '',
        captcha_answer: '',
        captcha_id: ''
    });
    const [submitting, setSubmitting] = useState(false);
    const [rateLimit, setRateLimit] = useState({ daily_limit: 10, used: 0, remaining: 10 });
    const [captcha, setCaptcha] = useState({ question: '', id: '' });
    const [categories, setCategories] = useState([]);
    const [popularTags, setPopularTags] = useState([]);
    const [tagInput, setTagInput] = useState('');

    useEffect(() => {
        fetchRateLimit();
        fetchCaptcha();
        fetchCategories();
        fetchPopularTags();
        if (user?.email) {
            setFormData(prev => ({ ...prev, submitter_email: user.email }));
        }
    }, [user]);

    const fetchRateLimit = async () => {
        try {
            const response = await axios.get(`${API}/submissions/remaining`);
            setRateLimit(response.data);
        } catch (error) {
            console.error('Error fetching rate limit:', error);
        }
    };

    const fetchCaptcha = async () => {
        try {
            const response = await axios.get(`${API}/captcha`);
            setCaptcha(response.data);
            setFormData(prev => ({ ...prev, captcha_id: response.data.id, captcha_answer: '' }));
        } catch (error) {
            console.error('Error fetching captcha:', error);
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
            const response = await axios.get(`${API}/tags?limit=20`);
            setPopularTags(response.data.items || []);
        } catch (error) {
            console.error('Error fetching tags:', error);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleAddTag = (tag) => {
        const cleanTag = tag.trim().toLowerCase();
        if (cleanTag && !formData.tags.includes(cleanTag) && formData.tags.length < 10) {
            setFormData(prev => ({ ...prev, tags: [...prev.tags, cleanTag] }));
            setTagInput('');
        }
    };

    const handleRemoveTag = (tagToRemove) => {
        setFormData(prev => ({ ...prev, tags: prev.tags.filter(t => t !== tagToRemove) }));
    };

    const handleTagInputKeyDown = (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            handleAddTag(tagInput);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.name.trim()) {
            toast.error('SYSTEM ERROR: Name is required');
            return;
        }
        if (!formData.download_link.trim()) {
            toast.error('SYSTEM ERROR: Download link is required');
            return;
        }
        if (!formData.captcha_answer) {
            toast.error('SYSTEM ERROR: Please solve the captcha');
            return;
        }

        if (rateLimit.remaining <= 0) {
            toast.error(`RATE LIMIT: Daily submission limit (${rateLimit.daily_limit}) reached. Try again tomorrow.`);
            return;
        }

        setSubmitting(true);
        try {
            const payload = {
                name: formData.name,
                download_link: formData.download_link,
                type: formData.type,
                captcha_answer: parseInt(formData.captcha_answer),
                captcha_id: formData.captcha_id
            };
            if (formData.file_size.trim()) {
                payload.file_size = formData.file_size.trim();
            }
            if (formData.description.trim()) {
                payload.description = formData.description.trim();
            }
            if (formData.category) {
                payload.category = formData.category;
            }
            if (formData.tags.length > 0) {
                payload.tags = formData.tags;
            }
            if (formData.submitter_email.trim()) {
                payload.submitter_email = formData.submitter_email.trim();
            }
            
            await axios.post(`${API}/submissions`, payload);
            toast.success('TRANSMISSION COMPLETE: Submission sent for approval');
            if (formData.submitter_email) {
                toast.info('Confirmation email sent!');
            }
            setFormData({ 
                name: '', 
                download_link: '', 
                type: 'game', 
                file_size: '', 
                description: '',
                category: '',
                tags: [],
                submitter_email: user?.email || '',
                captcha_answer: '',
                captcha_id: ''
            });
            fetchRateLimit();
            fetchCaptcha();
            setTimeout(() => navigate('/'), 2000);
        } catch (error) {
            console.error('Submission error:', error);
            const message = error.response?.data?.detail || 'Could not submit';
            toast.error(`TRANSMISSION FAILED: ${message}`);
            fetchCaptcha();
        } finally {
            setSubmitting(false);
        }
    };

    const filteredCategories = categories.filter(c => c.type === formData.type || c.type === 'all');

    return (
        <div className="main-content" data-testid="submit-page">
            <div className="retro-form">
                {/* Terminal Header */}
                <div style={{ 
                    borderBottom: '1px solid hsl(var(--border))', 
                    paddingBottom: '1rem', 
                    marginBottom: '1.5rem' 
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                        <div>
                            <h1 className="pixel-font neon-glow" style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>
                                <Terminal size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
                                SUBMIT NEW FILE
                            </h1>
                            <p style={{ fontSize: '0.875rem', opacity: 0.7 }}>
                                {'>'} Enter file details below.
                            </p>
                        </div>
                        {isLoggedIn ? (
                            <div style={{ 
                                padding: '0.5rem 1rem', 
                                border: '1px solid hsl(var(--primary))',
                                background: 'hsl(var(--primary) / 0.1)',
                                fontSize: '0.75rem'
                            }}>
                                <User size={12} style={{ display: 'inline', marginRight: '0.5rem' }} />
                                {user?.email}
                                <button 
                                    onClick={logout}
                                    style={{ marginLeft: '0.5rem', background: 'none', border: 'none', color: 'hsl(var(--destructive))', cursor: 'pointer', textDecoration: 'underline' }}
                                >
                                    Logout
                                </button>
                            </div>
                        ) : (
                            <Link to="/auth" className="filter-btn" data-testid="login-link">
                                <User size={12} style={{ display: 'inline', marginRight: '0.5rem' }} />
                                LOGIN / REGISTER
                            </Link>
                        )}
                    </div>
                </div>

                {/* Rate Limit Info */}
                <div style={{
                    padding: '0.75rem',
                    marginBottom: '1.5rem',
                    border: '1px solid',
                    borderColor: rateLimit.remaining > 0 ? 'hsl(var(--primary))' : 'hsl(var(--destructive))',
                    background: rateLimit.remaining > 0 ? 'hsl(var(--primary) / 0.1)' : 'hsl(var(--destructive) / 0.1)'
                }} data-testid="rate-limit-info">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
                        {rateLimit.remaining <= 0 ? (
                            <AlertTriangle size={16} style={{ color: 'hsl(var(--destructive))' }} />
                        ) : (
                            <Terminal size={16} />
                        )}
                        <span>
                            DAILY SUBMISSIONS: <strong>{rateLimit.used}</strong> / <strong>{rateLimit.daily_limit}</strong>
                            {' '} | {' '}
                            REMAINING: <strong style={{ color: rateLimit.remaining > 0 ? 'hsl(var(--primary))' : 'hsl(var(--destructive))' }}>
                                {rateLimit.remaining}
                            </strong>
                        </span>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    {/* Required Fields */}
                    <div className="form-group">
                        <label className="form-label" htmlFor="name">
                            {'>'} FILE_NAME: <span style={{ color: 'hsl(var(--destructive))' }}>*</span>
                        </label>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            className="form-input"
                            placeholder="Enter download name..."
                            disabled={rateLimit.remaining <= 0}
                            data-testid="submit-name-input"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="download_link">
                            {'>'} DOWNLOAD_LINK: <span style={{ color: 'hsl(var(--destructive))' }}>*</span>
                        </label>
                        <input
                            type="url"
                            id="download_link"
                            name="download_link"
                            value={formData.download_link}
                            onChange={handleChange}
                            className="form-input"
                            placeholder="https://..."
                            disabled={rateLimit.remaining <= 0}
                            data-testid="submit-link-input"
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div className="form-group">
                            <label className="form-label" htmlFor="type">
                                {'>'} FILE_TYPE: <span style={{ color: 'hsl(var(--destructive))' }}>*</span>
                            </label>
                            <select
                                id="type"
                                name="type"
                                value={formData.type}
                                onChange={handleChange}
                                className="form-select"
                                disabled={rateLimit.remaining <= 0}
                                data-testid="submit-type-select"
                            >
                                {typeOptions.map(option => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label className="form-label" htmlFor="category">
                                {'>'} CATEGORY:
                            </label>
                            <select
                                id="category"
                                name="category"
                                value={formData.category}
                                onChange={handleChange}
                                className="form-select"
                                disabled={rateLimit.remaining <= 0}
                                data-testid="submit-category-select"
                            >
                                <option value="">-- Select Category --</option>
                                {filteredCategories.map(cat => (
                                    <option key={cat.id} value={cat.name}>
                                        {cat.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Tags */}
                    <div className="form-group">
                        <label className="form-label">
                            <Tag size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                            TAGS (up to 10):
                        </label>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                            {formData.tags.map(tag => (
                                <span 
                                    key={tag} 
                                    style={{
                                        padding: '0.25rem 0.5rem',
                                        background: 'hsl(var(--primary) / 0.2)',
                                        border: '1px solid hsl(var(--primary))',
                                        fontSize: '0.75rem',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.25rem'
                                    }}
                                >
                                    {tag}
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveTag(tag)}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'inherit' }}
                                    >
                                        <X size={12} />
                                    </button>
                                </span>
                            ))}
                        </div>
                        <input
                            type="text"
                            value={tagInput}
                            onChange={(e) => setTagInput(e.target.value)}
                            onKeyDown={handleTagInputKeyDown}
                            className="form-input"
                            placeholder="Type tag and press Enter..."
                            disabled={rateLimit.remaining <= 0 || formData.tags.length >= 10}
                            data-testid="submit-tag-input"
                        />
                        {popularTags.length > 0 && (
                            <div style={{ marginTop: '0.5rem' }}>
                                <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>Popular: </span>
                                {popularTags.slice(0, 8).map(tag => (
                                    <button
                                        key={tag.name}
                                        type="button"
                                        onClick={() => handleAddTag(tag.name)}
                                        disabled={formData.tags.includes(tag.name)}
                                        style={{
                                            background: 'none',
                                            border: 'none',
                                            color: formData.tags.includes(tag.name) ? 'hsl(var(--muted-foreground))' : 'hsl(var(--primary))',
                                            cursor: formData.tags.includes(tag.name) ? 'default' : 'pointer',
                                            fontSize: '0.75rem',
                                            marginLeft: '0.5rem',
                                            textDecoration: formData.tags.includes(tag.name) ? 'none' : 'underline'
                                        }}
                                    >
                                        {tag.name}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Optional Fields */}
                    <div style={{ 
                        borderTop: '1px dashed hsl(var(--border))', 
                        marginTop: '1.5rem', 
                        paddingTop: '1.5rem' 
                    }}>
                        <p style={{ 
                            fontSize: '0.75rem', 
                            opacity: 0.7, 
                            marginBottom: '1rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}>
                            <HelpCircle size={14} />
                            OPTIONAL FIELDS
                        </p>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div className="form-group">
                                <label className="form-label" htmlFor="file_size">
                                    {'>'} FILE_SIZE:
                                </label>
                                <input
                                    type="text"
                                    id="file_size"
                                    name="file_size"
                                    value={formData.file_size}
                                    onChange={handleChange}
                                    className="form-input"
                                    placeholder="e.g., 4.5 GB, 500 MB"
                                    disabled={rateLimit.remaining <= 0}
                                    data-testid="submit-size-input"
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label" htmlFor="submitter_email">
                                    {'>'} YOUR_EMAIL:
                                </label>
                                <input
                                    type="email"
                                    id="submitter_email"
                                    name="submitter_email"
                                    value={formData.submitter_email}
                                    onChange={handleChange}
                                    className="form-input"
                                    placeholder="For confirmation email"
                                    disabled={rateLimit.remaining <= 0}
                                    data-testid="submit-email-input"
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label" htmlFor="description">
                                {'>'} DESCRIPTION:
                            </label>
                            <textarea
                                id="description"
                                name="description"
                                value={formData.description}
                                onChange={handleChange}
                                className="form-input"
                                placeholder="Brief description of the file..."
                                rows={3}
                                style={{ resize: 'vertical', minHeight: '80px' }}
                                disabled={rateLimit.remaining <= 0}
                                data-testid="submit-description-input"
                            />
                        </div>
                    </div>

                    {/* Captcha */}
                    <div className="form-group" style={{ 
                        padding: '1rem', 
                        border: '2px solid hsl(var(--border))',
                        background: 'hsl(var(--background))',
                        marginTop: '1.5rem'
                    }}>
                        <label className="form-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span>{'>'} CAPTCHA: <span style={{ color: 'hsl(var(--destructive))' }}>*</span></span>
                            <button 
                                type="button" 
                                onClick={fetchCaptcha}
                                className="action-btn approve"
                                style={{ padding: '0.25rem 0.5rem' }}
                                data-testid="refresh-captcha-btn"
                            >
                                <RefreshCw size={12} />
                            </button>
                        </label>
                        <div style={{ 
                            fontSize: '1.5rem', 
                            fontWeight: 'bold',
                            padding: '1rem',
                            textAlign: 'center',
                            marginBottom: '0.5rem',
                            background: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--primary))',
                            color: 'hsl(var(--primary))'
                        }}>
                            {captcha.question || 'Loading...'}
                        </div>
                        <input
                            type="number"
                            name="captcha_answer"
                            value={formData.captcha_answer}
                            onChange={handleChange}
                            className="form-input"
                            placeholder="Enter your answer..."
                            disabled={rateLimit.remaining <= 0}
                            data-testid="captcha-answer-input"
                        />
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                        <button
                            type="button"
                            onClick={() => navigate('/')}
                            className="submit-btn"
                            style={{ 
                                background: 'transparent', 
                                color: 'hsl(var(--foreground))',
                                flex: 1
                            }}
                            data-testid="submit-back-btn"
                        >
                            <ArrowLeft size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                            BACK
                        </button>
                        <button
                            type="submit"
                            className="submit-btn"
                            disabled={submitting || rateLimit.remaining <= 0}
                            style={{ flex: 2, opacity: rateLimit.remaining <= 0 ? 0.5 : 1 }}
                            data-testid="submit-btn"
                        >
                            {submitting ? (
                                <>TRANSMITTING...</>
                            ) : (
                                <>
                                    <Send size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                                    SUBMIT FILE
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
