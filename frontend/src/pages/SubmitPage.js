import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { Terminal, Send, ArrowLeft, HelpCircle, AlertTriangle, RefreshCw, Tag, X, User } from 'lucide-react';
import ReCAPTCHA from 'react-google-recaptcha';


const API = process.env.REACT_APP_BACKEND_URL + '/api';

const typeOptions = [
    { value: 'game', label: 'Game' },
    { value: 'software', label: 'Software' },
    { value: 'movie', label: 'Movie' },
    { value: 'tv_show', label: 'TV Show' }
];

function SubmitPage() {
    const navigate = useNavigate();
    const auth = useAuth();
    const user = auth.user;
    const isLoggedIn = auth.isLoggedIn;
    const logout = auth.logout;

    const [name, setName] = useState('');
    const [downloadLink, setDownloadLink] = useState('');
    const [siteName, setSiteName] = useState('');
    const [siteUrl, setSiteUrl] = useState('');
    const [fileType, setFileType] = useState('game');
    const [fileSize, setFileSize] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('');
    const [tags, setTags] = useState([]);
    const [submitterEmail, setSubmitterEmail] = useState('');
    const [captchaAnswer, setCaptchaAnswer] = useState('');
    const [captchaId, setCaptchaId] = useState('');

    const [recaptchaSettings, setRecaptchaSettings] = useState({ site_key: null, enable_submit: false, enable_auth: false });
    const [recaptchaToken, setRecaptchaToken] = useState('');

    const [submitting, setSubmitting] = useState(false);
    const [rateLimit, setRateLimit] = useState({ daily_limit: 10, used: 0, remaining: 10 });
    const [captcha, setCaptcha] = useState({ question: '', id: '' });
    const [categories, setCategories] = useState([]);
    const [popularTags, setPopularTags] = useState([]);
    const [tagInput, setTagInput] = useState('');

    useEffect(function() {
        fetchRateLimit();
        fetchCaptcha();
        fetchCategories();
        fetchPopularTags();
        fetchRecaptchaSettings();
        if (user && user.email) {
            setSubmitterEmail(user.email);
        }
    }, [user]);

    function fetchRateLimit() {
        axios.get(API + '/submissions/remaining')
            .then(function(response) {
                setRateLimit(response.data);
            })
            .catch(function(error) {
                console.error('Error fetching rate limit:', error);
            });
    }

    function fetchCaptcha() {
        axios.get(API + '/captcha')
            .then(function(response) {
                setCaptcha(response.data);
                setCaptchaId(response.data.id);
                setCaptchaAnswer('');
            })
            .catch(function(error) {
                console.error('Error fetching captcha:', error);
            });
    }

    function fetchCategories() {
        axios.get(API + '/categories')
            .then(function(response) {
                setCategories(response.data.items || []);
            })
            .catch(function(error) {
                console.error('Error fetching categories:', error);
            });
    }

    function fetchPopularTags() {

    function fetchRecaptchaSettings() {
        axios.get(API + '/recaptcha/settings')
            .then(function(response) {
                setRecaptchaSettings(response.data || { site_key: null, enable_submit: false, enable_auth: false });
                setRecaptchaToken('');
            })
            .catch(function(error) {
                console.error('Error fetching recaptcha settings:', error);
            });
    }

        axios.get(API + '/tags?limit=20')
            .then(function(response) {
                setPopularTags(response.data.items || []);
            })
            .catch(function(error) {
                console.error('Error fetching tags:', error);
            });
    }

    function handleAddTag(tag) {
        var cleanTag = tag.trim().toLowerCase();
        if (cleanTag && !tags.includes(cleanTag) && tags.length < 10) {
            setTags([...tags, cleanTag]);
            setTagInput('');
        }
    }

    function handleRemoveTag(tagToRemove) {
        setTags(tags.filter(function(t) { return t !== tagToRemove; }));
    }

    function handleTagInputKeyDown(e) {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            handleAddTag(tagInput);
        }
    }

    function handleSubmit(e) {
        e.preventDefault();
        
        if (!name.trim()) {
            toast.error('SYSTEM ERROR: Name is required');
            return;
        }
        if (!downloadLink.trim()) {
            toast.error('SYSTEM ERROR: Download link is required');
            return;
        }
        if (recaptchaSettings.enable_submit) {
            if (!recaptchaToken) {
                toast.error('SYSTEM ERROR: Please complete the reCAPTCHA');
                return;
            }
        } else {
            if (!captchaAnswer) {
                toast.error('SYSTEM ERROR: Please solve the captcha');
                return;
            }
        }

        if (rateLimit.remaining <= 0) {
            toast.error('RATE LIMIT: Daily submission limit reached');
            return;
        }

        setSubmitting(true);
        var payload = {
            name: name,
            download_link: downloadLink,
            type: fileType,
            site_name: siteName,
            site_url: siteUrl
        };

        if (recaptchaSettings.enable_submit) {
            payload.recaptcha_token = recaptchaToken;
        } else {
            payload.captcha_answer = parseInt(captchaAnswer);
            payload.captcha_id = captchaId;
        }
        if (fileSize.trim()) {
            payload.file_size = fileSize.trim();
        }
        if (description.trim()) {
            payload.description = description.trim();
        }
        if (category) {
            payload.category = category;
        }
        if (tags.length > 0) {
            payload.tags = tags;
        }
        if (submitterEmail.trim()) {
            payload.submitter_email = submitterEmail.trim();
        }
        
        axios.post(API + '/submissions', payload)
            .then(function() {
                toast.success('TRANSMISSION COMPLETE: Submission sent for approval');
                if (submitterEmail) {
                    toast.info('Confirmation email sent!');
                }
                setName('');
                setDownloadLink('');
                setSiteName('');
                setSiteUrl('');
                setRecaptchaToken('');
                setFileType('game');
                setFileSize('');
                setDescription('');
                setCategory('');
                setTags([]);
                setSubmitterEmail(user && user.email ? user.email : '');
                setCaptchaAnswer('');
                fetchRateLimit();
                fetchCaptcha();
                setTimeout(function() { navigate('/'); }, 2000);
            })
            .catch(function(error) {
                console.error('Submission error:', error);
                var message = 'Could not submit';
                if (error.response && error.response.data && error.response.data.detail) {
                    message = error.response.data.detail;
                }
                toast.error('TRANSMISSION FAILED: ' + message);
                fetchCaptcha();
            })
            .finally(function() {
                setSubmitting(false);
            });
    }

    var filteredCategories = categories.filter(function(c) { 
        return c.type === fileType || c.type === 'all'; 
    });

    return (
        <div className="main-content" data-testid="submit-page">
            <div className="retro-form">
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
                                Enter file details below.
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
                                {user && user.email}
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
                    <div className="form-group">
                        <label className="form-label">
                            FILE NAME: <span style={{ color: 'hsl(var(--destructive))' }}>*</span>
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={function(e) { setName(e.target.value); }}
                            className="form-input"
                            placeholder="Enter download name..."
                            disabled={rateLimit.remaining <= 0}
                            data-testid="submit-name-input"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">
                            DOWNLOAD LINK: <span style={{ color: 'hsl(var(--destructive))' }}>*</span>
                        </label>
                        <input
                            type="url"
                            value={downloadLink}
                            onChange={function(e) { setDownloadLink(e.target.value); }}
                            className="form-input"
                            placeholder="https://..."
                            disabled={rateLimit.remaining <= 0}
                            data-testid="submit-link-input"
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div className="form-group">
                            <label className="form-label">
                                FILE TYPE: <span style={{ color: 'hsl(var(--destructive))' }}>*</span>
                            </label>
                            <select
                                value={fileType}
                                onChange={function(e) { setFileType(e.target.value); }}
                                className="form-select"
                                disabled={rateLimit.remaining <= 0}
                                data-testid="submit-type-select"
                            >
                                {typeOptions.map(function(option) {
                                    return (
                                        <option key={option.value} value={option.value}>
                                            {option.label}
                                        </option>
                                    );
                                })}
                            </select>
                        </div>

                        <div className="form-group">
                            <label className="form-label">
                                CATEGORY:
                            </label>
                            <select
                                value={category}
                                onChange={function(e) { setCategory(e.target.value); }}
                                className="form-select"
                                disabled={rateLimit.remaining <= 0}
                                data-testid="submit-category-select"
                            >
                                <option value="">-- Select Category --</option>
                                {filteredCategories.map(function(cat) {
                                    return (
                                        <option key={cat.id} value={cat.name}>
                                            {cat.name}
                                        </option>
                                    );
                                })}
                            </select>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">
                            <Tag size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                            TAGS (up to 10):
                        </label>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                            {tags.map(function(tag) {
                                return (
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
                                            onClick={function() { handleRemoveTag(tag); }}
                                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'inherit' }}
                                        >
                                            <X size={12} />
                                        </button>
                                    </span>
                                );
                            })}
                        </div>
                        <input
                            type="text"
                            value={tagInput}
                            onChange={function(e) { setTagInput(e.target.value); }}
                            onKeyDown={handleTagInputKeyDown}
                            className="form-input"
                            placeholder="Type tag and press Enter..."
                            disabled={rateLimit.remaining <= 0 || tags.length >= 10}
                            data-testid="submit-tag-input"
                        />
                        {popularTags.length > 0 && (
                            <div style={{ marginTop: '0.5rem' }}>
                                <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>Popular: </span>
                                {popularTags.slice(0, 8).map(function(tag) {
                                    return (
                                        <button
                                            key={tag.name}
                                            type="button"
                                            onClick={function() { handleAddTag(tag.name); }}
                                            disabled={tags.includes(tag.name)}
                                            style={{
                                                background: 'none',
                                                border: 'none',
                                                color: tags.includes(tag.name) ? 'hsl(var(--muted-foreground))' : 'hsl(var(--primary))',
                                                cursor: tags.includes(tag.name) ? 'default' : 'pointer',
                                                fontSize: '0.75rem',
                                                marginLeft: '0.5rem',
                                                textDecoration: tags.includes(tag.name) ? 'none' : 'underline'
                                            }}
                                        >
                                            {tag.name}
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </div>

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
                                <label className="form-label">
                                    FILE SIZE:
                                </label>
                                <input
                                    type="text"
                                    value={fileSize}
                                    onChange={function(e) { setFileSize(e.target.value); }}
                                    className="form-input"
                                    placeholder="e.g., 4.5 GB, 500 MB"
                                    disabled={rateLimit.remaining <= 0}
                                    data-testid="submit-size-input"
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">
                                    YOUR EMAIL:
                                </label>
                                <input
                                    type="email"
                                    value={submitterEmail}
                                    onChange={function(e) { setSubmitterEmail(e.target.value); }}
                                    className="form-input"
                                    placeholder="For confirmation email"
                                    disabled={rateLimit.remaining <= 0}
                                    data-testid="submit-email-input"
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label">
                                DESCRIPTION:
                            </label>
                            <textarea
                                value={description}
                                onChange={function(e) { setDescription(e.target.value); }}
                                className="form-input"
                                placeholder="Brief description of the file..."
                                rows={3}
                                style={{ resize: 'vertical', minHeight: '80px' }}
                                disabled={rateLimit.remaining <= 0}
                                data-testid="submit-description-input"
                            />
                        </div>
                    </div>

                    <div className="form-group" style={{ 
                        padding: '1rem', 
                        border: '2px solid hsl(var(--border))',
                        background: 'hsl(var(--background))',
                        marginTop: '1.5rem'
                    }}>
                        <label className="form-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span>CAPTCHA: <span style={{ color: 'hsl(var(--destructive))' }}>*</span></span>
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
                            value={captchaAnswer}
                            onChange={function(e) { setCaptchaAnswer(e.target.value); }}
                            className="form-input"
                            placeholder="Enter your answer..."
                            disabled={rateLimit.remaining <= 0}
                            data-testid="captcha-answer-input"
                        />
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                        <button
                            type="button"
                            onClick={function() { navigate('/'); }}
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
                            {submitting ? 'TRANSMITTING...' : (
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

export default SubmitPage;
