import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { 
    ArrowLeft,
    Check, 
    X, 
    Trash2, 
    RefreshCw,
    ExternalLink,
    Loader2,
    CheckSquare,
    Square
} from 'lucide-react';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "../components/ui/alert-dialog";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusColors = {
    pending: '#FFFF00',
    approved: '#00FF41',
    rejected: '#FF0000'
};

export default function AdminSubmissionsPage() {
    const navigate = useNavigate();
    const [submissions, setSubmissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [statusFilter, setStatusFilter] = useState('pending');
    const [selectedIds, setSelectedIds] = useState([]);
    const [bulkAction, setBulkAction] = useState({ open: false, action: null });
    const [processing, setProcessing] = useState(false);

    useEffect(() => {
        if (!sessionStorage.getItem('admin_auth')) {
            navigate('/admin');
            return;
        }
        fetchSubmissions();
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
            setSelectedIds([]);
        } catch (error) {
            console.error('Error fetching submissions:', error);
            toast.error('Failed to load submissions');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectAll = () => {
        if (selectedIds.length === submissions.length) {
            setSelectedIds([]);
        } else {
            setSelectedIds(submissions.map(s => s.id));
        }
    };

    const handleSelectOne = (id) => {
        if (selectedIds.includes(id)) {
            setSelectedIds(selectedIds.filter(sid => sid !== id));
        } else {
            setSelectedIds([...selectedIds, id]);
        }
    };

    const handleApprove = async (id) => {
        try {
            await axios.post(`${API}/admin/submissions/${id}/approve`);
            toast.success('Submission approved!');
            fetchSubmissions();
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
        try {
            await axios.delete(`${API}/admin/submissions/${id}`);
            toast.success('Submission deleted');
            fetchSubmissions();
        } catch (error) {
            console.error('Delete error:', error);
            toast.error('Failed to delete submission');
        }
    };

    const handleBulkApprove = async () => {
        setProcessing(true);
        let successCount = 0;
        let failCount = 0;
        
        for (const id of selectedIds) {
            try {
                await axios.post(`${API}/admin/submissions/${id}/approve`);
                successCount++;
            } catch (error) {
                failCount++;
            }
        }
        
        setProcessing(false);
        setBulkAction({ open: false, action: null });
        
        if (successCount > 0) {
            toast.success(`${successCount} submission(s) approved`);
        }
        if (failCount > 0) {
            toast.error(`${failCount} submission(s) failed to approve`);
        }
        
        fetchSubmissions();
    };

    const handleBulkDelete = async () => {
        setProcessing(true);
        let successCount = 0;
        let failCount = 0;
        
        for (const id of selectedIds) {
            try {
                await axios.delete(`${API}/admin/submissions/${id}`);
                successCount++;
            } catch (error) {
                failCount++;
            }
        }
        
        setProcessing(false);
        setBulkAction({ open: false, action: null });
        
        if (successCount > 0) {
            toast.success(`${successCount} submission(s) deleted`);
        }
        if (failCount > 0) {
            toast.error(`${failCount} submission(s) failed to delete`);
        }
        
        fetchSubmissions();
    };

    const pendingSubmissions = submissions.filter(s => s.status === 'pending');
    const allSelected = submissions.length > 0 && selectedIds.length === submissions.length;
    const someSelected = selectedIds.length > 0;

    return (
        <div className="admin-container" data-testid="admin-submissions-page">
            {/* Header */}
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '1.5rem',
                flexWrap: 'wrap',
                gap: '1rem'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button 
                        onClick={() => navigate('/admin/dashboard')}
                        className="action-btn"
                        data-testid="back-to-dashboard-btn"
                    >
                        <ArrowLeft size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                        BACK
                    </button>
                    <h1 className="pixel-font neon-glow" style={{ fontSize: '1rem', margin: 0 }}>
                        SUBMISSIONS MANAGEMENT
                    </h1>
                </div>
                <button 
                    onClick={fetchSubmissions}
                    className="action-btn approve"
                    data-testid="refresh-submissions-btn"
                >
                    <RefreshCw size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                    REFRESH
                </button>
            </div>

            {/* Filters and Bulk Actions */}
            <div className="admin-card" style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    {/* Status Filter */}
                    <div className="filter-bar" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                        <span style={{ opacity: 0.7 }}>STATUS:</span>
                        {['all', 'pending', 'approved', 'rejected'].map(status => (
                            <button
                                key={status}
                                className={`filter-btn ${statusFilter === status ? 'active' : ''}`}
                                onClick={() => { setStatusFilter(status); setPage(1); setSelectedIds([]); }}
                                data-testid={`status-filter-${status}`}
                            >
                                {status.toUpperCase()}
                            </button>
                        ))}
                    </div>

                    {/* Bulk Actions */}
                    {someSelected && (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                                onClick={() => setBulkAction({ open: true, action: 'approve' })}
                                className="action-btn approve"
                                disabled={processing}
                                data-testid="bulk-approve-btn"
                            >
                                <Check size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                                APPROVE ({selectedIds.length})
                            </button>
                            <button
                                onClick={() => setBulkAction({ open: true, action: 'delete' })}
                                className="action-btn reject"
                                disabled={processing}
                                data-testid="bulk-delete-btn"
                            >
                                <Trash2 size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                                DELETE ({selectedIds.length})
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Submissions Table */}
            <div className="admin-card">
                {loading ? (
                    <div className="loading-state" style={{ padding: '2rem', textAlign: 'center' }}>
                        <Loader2 className="animate-spin" size={24} style={{ display: 'inline', marginRight: '0.5rem' }} />
                        <span>LOADING...</span>
                    </div>
                ) : submissions.length === 0 ? (
                    <div className="empty-state" style={{ padding: '2rem', textAlign: 'center', opacity: 0.7 }}>
                        <p>NO SUBMISSIONS FOUND</p>
                    </div>
                ) : (
                    <>
                        <table className="downloads-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '40px' }}>
                                        <button 
                                            onClick={handleSelectAll}
                                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
                                            data-testid="select-all-btn"
                                        >
                                            {allSelected ? <CheckSquare size={18} /> : <Square size={18} />}
                                        </button>
                                    </th>
                                    <th>Name</th>
                                    <th>Type</th>
                                    <th>Size</th>
                                    <th>Site</th>
                                    <th>Status</th>
                                    <th>Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {submissions.map((sub, index) => (
                                    <tr 
                                        key={sub.id} 
                                        data-testid={`submission-row-${index}`}
                                        style={{ 
                                            background: selectedIds.includes(sub.id) ? 'rgba(0, 255, 65, 0.1)' : 'transparent'
                                        }}
                                    >
                                        <td>
                                            <button 
                                                onClick={() => handleSelectOne(sub.id)}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
                                                data-testid={`select-${index}`}
                                            >
                                                {selectedIds.includes(sub.id) ? <CheckSquare size={18} /> : <Square size={18} />}
                                            </button>
                                        </td>
                                        <td>
                                            <a 
                                                href={sub.download_link} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                style={{ display: 'block' }}
                                            >
                                                {sub.name}
                                            </a>
                                            {sub.description && (
                                                <span style={{ display: 'block', fontSize: '0.75rem', opacity: 0.6 }}>
                                                    {sub.description}
                                                </span>
                                            )}
                                        </td>
                                        <td><span className={`type-badge type-${sub.type}`}>{sub.type}</span></td>
                                        <td style={{ fontSize: '0.875rem' }}>{sub.file_size || '-'}</td>
                                        <td>
                                            {sub.site_name ? (
                                                <a href={sub.site_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.75rem' }}>
                                                    {sub.site_name}
                                                </a>
                                            ) : '-'}
                                        </td>
                                        <td>
                                            <span style={{ color: statusColors[sub.status] || '#fff' }}>
                                                {sub.status.toUpperCase()}
                                            </span>
                                        </td>
                                        <td style={{ fontSize: '0.875rem' }}>{sub.submission_date}</td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '0.25rem' }}>
                                                {sub.status === 'pending' && (
                                                    <>
                                                        <button 
                                                            onClick={() => handleApprove(sub.id)} 
                                                            className="action-btn approve" 
                                                            title="Approve"
                                                            data-testid={`approve-btn-${index}`}
                                                        >
                                                            <Check size={14} />
                                                        </button>
                                                        <button 
                                                            onClick={() => handleReject(sub.id)} 
                                                            className="action-btn" 
                                                            title="Reject"
                                                            style={{ background: '#FF6600' }}
                                                            data-testid={`reject-btn-${index}`}
                                                        >
                                                            <X size={14} />
                                                        </button>
                                                    </>
                                                )}
                                                <button 
                                                    onClick={() => handleDelete(sub.id)} 
                                                    className="action-btn reject" 
                                                    title="Delete"
                                                    data-testid={`delete-btn-${index}`}
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="pagination" style={{ marginTop: '1rem' }}>
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
                    </>
                )}
            </div>

            {/* Bulk Action Confirmation Dialog */}
            <AlertDialog open={bulkAction.open} onOpenChange={(open) => setBulkAction({ ...bulkAction, open })}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>
                            {bulkAction.action === 'approve' ? 'Approve Submissions?' : 'Delete Submissions?'}
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            {bulkAction.action === 'approve' 
                                ? `This will approve ${selectedIds.length} submission(s) and add them to the downloads list.`
                                : `This will permanently delete ${selectedIds.length} submission(s). This cannot be undone.`
                            }
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={processing}>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={bulkAction.action === 'approve' ? handleBulkApprove : handleBulkDelete}
                            disabled={processing}
                            style={{ 
                                background: bulkAction.action === 'approve' ? '#00FF41' : '#FF0000',
                                color: '#000'
                            }}
                        >
                            {processing ? (
                                <>
                                    <Loader2 className="animate-spin" size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                                    Processing...
                                </>
                            ) : (
                                bulkAction.action === 'approve' ? 'Approve All' : 'Delete All'
                            )}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
