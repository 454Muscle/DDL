import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { UserPlus, LogIn, RefreshCw } from 'lucide-react';
import ReCAPTCHA from 'react-google-recaptcha';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AuthPage() {
    const navigate = useNavigate();
    const { login, isLoggedIn } = useAuth();
    const [mode, setMode] = useState('login'); // login or register
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        captcha_answer: '',
        captcha_id: ''
    });
    const [captcha, setCaptcha] = useState({ question: '', id: '' });
    const [loading, setLoading] = useState(false);
    const [recaptchaSettings, setRecaptchaSettings] = useState({ site_key: null, enable_submit: false, enable_auth: false });
    const [recaptchaToken, setRecaptchaToken] = useState('');

    useEffect(() => {
        if (isLoggedIn) {
            navigate('/submit');
        }
        fetchCaptcha();
        fetchRecaptchaSettings();
    }, [isLoggedIn, navigate]);

    const fetchCaptcha = async () => {
        try {
            const response = await axios.get(`${API}/captcha`);
            setCaptcha(response.data);
            setFormData(prev => ({ ...prev, captcha_id: response.data.id, captcha_answer: '' }));

    const fetchRecaptchaSettings = async () => {
        try {
            const response = await axios.get(`${API}/recaptcha/settings`);
            setRecaptchaSettings(response.data || { site_key: null, enable_submit: false, enable_auth: false });
            setRecaptchaToken('');
        } catch (error) {
            console.error('Error fetching recaptcha settings:', error);
        }
    };

        } catch (error) {
            console.error('Error fetching captcha:', error);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.email.trim() || !formData.password.trim()) {
            toast.error('Email and password are required');
            return;
        }

        if (mode === 'register') {
            if (formData.password !== formData.confirmPassword) {
                toast.error('Passwords do not match');
                return;
            }
            if (formData.password.length < 6) {
                toast.error('Password must be at least 6 characters');
                return;
            }
        }

        setLoading(true);
        try {
            if (mode === 'register') {
                const payload = {
                    email: formData.email,
                    password: formData.password
                };
                if (recaptchaSettings.enable_auth) {
                    payload.recaptcha_token = recaptchaToken;
                } else {
                    payload.captcha_answer = parseInt(formData.captcha_answer);
                    payload.captcha_id = formData.captcha_id;
                }
                await axios.post(`${API}/auth/register`, payload);
                toast.success('Registration successful! Please login.');
                setMode('login');
                fetchCaptcha();
            } else {
                const response = await axios.post(`${API}/auth/login`, {
                    email: formData.email,
                    password: formData.password
                });
                login(response.data);
                toast.success('Login successful!');
                navigate('/submit');
            }
        } catch (error) {
            console.error('Auth error:', error);
            const message = error.response?.data?.detail || 'Authentication failed';
            toast.error(message);
            if (mode === 'register') {
                fetchCaptcha();
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="main-content" data-testid="auth-page">
            <div className="retro-form" style={{ maxWidth: '450px' }}>
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <h1 className="pixel-font neon-glow" style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>
                        {mode === 'login' ? (
                            <><LogIn size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />USER LOGIN</>
                        ) : (
                            <><UserPlus size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />REGISTER</>
                        )}
                    </h1>
                    <p style={{ fontSize: '0.875rem', opacity: 0.7 }}>
                        {mode === 'login' ? 'Login to track your submissions' : 'Create an account to get started'}
                    </p>
                </div>

                {/* Tab Switcher */}
                <div style={{ display: 'flex', marginBottom: '1.5rem', borderBottom: '1px solid hsl(var(--border))' }}>
                    <button
                        onClick={() => setMode('login')}
                        className={`filter-btn ${mode === 'login' ? 'active' : ''}`}
                        style={{ flex: 1, borderRadius: 0 }}
                        data-testid="login-tab"
                    >
                        LOGIN
                    </button>
                    <button
                        onClick={() => { setMode('register'); fetchCaptcha(); }}
                        className={`filter-btn ${mode === 'register' ? 'active' : ''}`}
                        style={{ flex: 1, borderRadius: 0 }}
                        data-testid="register-tab"
                    >
                        REGISTER
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="email">
                            {'>'} EMAIL:
                        </label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            className="form-input"
                            placeholder="your@email.com"
                            data-testid="auth-email-input"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="password">
                            {'>'} PASSWORD:
                        </label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            className="form-input"
                            placeholder="••••••••"
                            data-testid="auth-password-input"
                        />
                    </div>

                    {mode === 'register' && (
                        <>
                            <div className="form-group">
                                <label className="form-label" htmlFor="confirmPassword">
                                    {'>'} CONFIRM PASSWORD:
                                </label>
                                <input
                                    type="password"
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    className="form-input"
                                    placeholder="••••••••"
                                    data-testid="auth-confirm-password-input"
                                />
                            </div>

                            {/* Captcha */}
                            <div className="form-group" style={{ 
                                padding: '1rem', 
                                border: '1px dashed hsl(var(--border))',
                                background: 'hsl(var(--background))'
                            }}>
                                <label className="form-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                    <span>{'>'} CAPTCHA:</span>
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
                                    fontSize: '1.25rem', 
                                    fontWeight: 'bold',
                                    padding: '0.5rem',
                                    textAlign: 'center',
                                    marginBottom: '0.5rem',
                                    background: 'hsl(var(--card))',
                                    border: '1px solid hsl(var(--border))'
                                }}>
                                    {captcha.question || 'Loading...'}
                                </div>
                                <input
                                    type="number"
                                    name="captcha_answer"
                                    value={formData.captcha_answer}
                                    onChange={handleChange}
                                    className="form-input"
                                    placeholder="Enter answer"
                                    data-testid="captcha-answer-input"
                                />
                            </div>
                        </>
                    )}

                    <button
                        type="submit"
                        className="submit-btn"
                        disabled={loading}
                        style={{ marginTop: '1.5rem' }}
                        data-testid="auth-submit-btn"
                    >
                        {loading ? 'PROCESSING...' : (mode === 'login' ? 'LOGIN' : 'REGISTER')}
                    </button>
                </form>

                {/* Links */}
                <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.875rem' }}>
                    <p style={{ opacity: 0.7 }}>
                        {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
                        <button
                            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); if (mode === 'login') fetchCaptcha(); }}
                            style={{ background: 'none', border: 'none', color: 'hsl(var(--primary))', cursor: 'pointer', textDecoration: 'underline' }}
                        >
                            {mode === 'login' ? 'Register' : 'Login'}
                        </button>
                    </p>
                    <p style={{ marginTop: '0.5rem' }}>
                        <Link to="/submit" style={{ opacity: 0.7 }}>
                            Or submit without an account →
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
