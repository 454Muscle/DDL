import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Lock, KeyRound } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminLoginPage() {
    const navigate = useNavigate();
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!password.trim()) {
            toast.error('ACCESS DENIED: Password required');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(`${API}/admin/login`, { password });
            if (response.data.success) {
                sessionStorage.setItem('admin_auth', 'true');
                toast.success('ACCESS GRANTED: Welcome, Admin');
                navigate('/admin/dashboard');
            }
        } catch (error) {
            console.error('Login error:', error);
            toast.error('ACCESS DENIED: Invalid credentials');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container" data-testid="admin-login-page">
            <div className="login-box">
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{ 
                        width: '80px', 
                        height: '80px', 
                        border: '2px solid hsl(var(--primary))',
                        margin: '0 auto 1rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <Lock size={40} />
                    </div>
                    <h1 className="pixel-font neon-glow" style={{ fontSize: '0.875rem' }}>
                        SYSTEM ROOT ACCESS
                    </h1>
                    <p style={{ fontSize: '0.875rem', opacity: 0.7, marginTop: '0.5rem' }}>
                        ENTER ADMIN PASSWORD
                    </p>
                </div>

                {/* Terminal Style */}
                <div style={{ 
                    background: 'hsl(var(--background))', 
                    border: '1px solid hsl(var(--border))',
                    padding: '1rem',
                    marginBottom: '1.5rem',
                    fontSize: '0.875rem'
                }}>
                    <p style={{ opacity: 0.7 }}>root@download-portal:~$</p>
                    <p>sudo authenticate --admin</p>
                    <p style={{ opacity: 0.7 }}>[sudo] password for admin:</p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="password">
                            <KeyRound size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                            PASSWORD:
                        </label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="form-input"
                            placeholder="••••••••"
                            autoFocus
                            data-testid="admin-password-input"
                        />
                    </div>

                    <button
                        type="submit"
                        className="submit-btn"
                        disabled={loading}
                        data-testid="admin-login-btn"
                    >
                        {loading ? 'AUTHENTICATING...' : 'AUTHENTICATE'}
                    </button>
                </form>

                {/* Warning */}
                <div style={{ 
                    marginTop: '1.5rem', 
                    padding: '1rem',
                    border: '1px solid hsl(var(--destructive))',
                    fontSize: '0.75rem',
                    textAlign: 'center'
                }}>
                    <p style={{ color: 'hsl(var(--destructive))' }}>
                        WARNING: UNAUTHORIZED ACCESS IS PROHIBITED
                    </p>
                </div>
            </div>
        </div>
    );
}
