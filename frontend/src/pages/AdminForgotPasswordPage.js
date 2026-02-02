import { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminForgotPasswordPage() {
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
            await axios.post(`${API}/admin/forgot-password`, { email });
            toast.success('If initialized and email matches, a reset link has been sent.');
        } catch (err) {
            console.error(err);
            toast.error(err.response?.data?.detail || 'Failed to request reset');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container" style={{ maxWidth: 520, padding: '2rem 1rem' }}>
            <h1 className="pixel-font" style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>ADMIN FORGOT PASSWORD</h1>
            <p style={{ opacity: 0.7, marginBottom: '1rem', fontSize: '0.875rem' }}>
                Enter the admin email. If it matches, we’ll email a magic link to reset the admin password.
            </p>

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label className="form-label">ADMIN EMAIL</label>
                    <input
                        type="email"
                        className="form-input"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="admin@example.com"
                        data-testid="admin-forgot-email-input"
                    />
                </div>

                <button className="submit-btn" type="submit" disabled={loading} data-testid="admin-forgot-submit-btn">
                    {loading ? 'SENDING...' : 'SEND RESET LINK'}
                </button>
            </form>

            <p style={{ marginTop: '1rem', fontSize: '0.75rem', opacity: 0.7 }}>
                <Link to="/admin">Back to admin login</Link>
            </p>
        </div>
    );
}
