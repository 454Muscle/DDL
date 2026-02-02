import { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!email.trim()) {
            toast.error('Email is required');
            return;
        }
        setLoading(true);
        try {
            await axios.post(`${API}/auth/forgot-password`, { email });
            toast.success('If that email exists, a reset link has been sent.');
        } catch (err) {
            console.error(err);
            toast.error('Failed to request reset');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container" style={{ maxWidth: 520, padding: '2rem 1rem' }}>
            <h1 className="pixel-font" style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>FORGOT PASSWORD</h1>
            <p style={{ opacity: 0.7, marginBottom: '1rem', fontSize: '0.875rem' }}>
                Enter your account email. If it exists, we’ll email you a magic link to reset your password.
            </p>

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label className="form-label">EMAIL</label>
                    <input
                        type="email"
                        className="form-input"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        data-testid="forgot-email-input"
                    />
                </div>

                <button className="submit-btn" type="submit" disabled={loading} data-testid="forgot-submit-btn">
                    {loading ? 'SENDING...' : 'SEND RESET LINK'}
                </button>
            </form>

            <p style={{ marginTop: '1rem', fontSize: '0.75rem', opacity: 0.7 }}>
                <Link to="/auth">Back to login</Link>
            </p>
        </div>
    );
}
