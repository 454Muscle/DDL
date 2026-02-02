import { useMemo, useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function useQuery() {
    const { search } = useLocation();
    return useMemo(() => new URLSearchParams(search), [search]);
}

export default function AdminConfirmPasswordChangePage() {
    const query = useQuery();
    const navigate = useNavigate();
    const token = query.get('token') || '';

    const [loading, setLoading] = useState(false);

    const handleConfirm = async () => {
        if (!token) {
            toast.error('Missing token');
            return;
        }
        setLoading(true);
        try {
            await axios.post(`${API}/admin/password/change/confirm`, { token });
            toast.success('Password change confirmed. Please login.');
            navigate('/admin');
        } catch (err) {
            console.error(err);
            toast.error(err.response?.data?.detail || 'Failed to confirm password change');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container" style={{ maxWidth: 520, padding: '2rem 1rem' }}>
            <h1 className="pixel-font" style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>CONFIRM ADMIN PASSWORD CHANGE</h1>
            <p style={{ opacity: 0.7, marginBottom: '1rem', fontSize: '0.875rem' }}>
                Click confirm to finalize the admin password change.
            </p>

            <button className="submit-btn" disabled={loading} onClick={handleConfirm} data-testid="admin-confirm-password-change-btn">
                {loading ? 'CONFIRMING...' : 'CONFIRM PASSWORD CHANGE'}
            </button>

            <p style={{ marginTop: '1rem', fontSize: '0.75rem', opacity: 0.7 }}>
                <Link to="/admin">Back to admin login</Link>
            </p>
        </div>
    );
}
