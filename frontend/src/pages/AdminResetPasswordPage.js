import { useMemo, useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function useQuery() {
    const { search } = useLocation();
    return useMemo(() => new URLSearchParams(search), [search]);
}

export default function AdminResetPasswordPage() {
    const query = useQuery();
    const navigate = useNavigate();
    const token = query.get('token') || '';

    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!token) {
            toast.error('Missing token');
            return;
        }
        if (!password || password.length < 6) {
            toast.error('Password must be at least 6 characters');
            return;
        }
        setLoading(true);
        try {
            await axios.post(`${API}/admin/reset-password`, { token, new_password: password });
            toast.success('Admin password updated. Please login.');
            navigate('/admin');
        } catch (err) {
            console.error(err);
            toast.error(err.response?.data?.detail || 'Failed to reset password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container" style={{ maxWidth: 520, padding: '2rem 1rem' }}>
            <h1 className="pixel-font" style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>ADMIN RESET PASSWORD</h1>
            <p style={{ opacity: 0.7, marginBottom: '1rem', fontSize: '0.875rem' }}>
                Set a new admin password.
            </p>

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label className="form-label">NEW PASSWORD</label>
                    <input
                        type="password"
                        className="form-input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        data-testid="admin-reset-password-input"
                    />
                </div>

                <button className="submit-btn" type="submit" disabled={loading} data-testid="admin-reset-submit-btn">
                    {loading ? 'UPDATING...' : 'UPDATE ADMIN PASSWORD'}
                </button>
            </form>

            <p style={{ marginTop: '1rem', fontSize: '0.75rem', opacity: 0.7 }}>
                <Link to="/admin">Back to admin login</Link>
            </p>
        </div>
    );
}
