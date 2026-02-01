import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Terminal, Send, ArrowLeft, HelpCircle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const typeOptions = [
    { value: 'game', label: 'Game' },
    { value: 'software', label: 'Software' },
    { value: 'movie', label: 'Movie' },
    { value: 'tv_show', label: 'TV Show' }
];

export default function SubmitPage() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        name: '',
        download_link: '',
        type: 'game',
        file_size: '',
        description: ''
    });
    const [submitting, setSubmitting] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
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

        setSubmitting(true);
        try {
            const payload = {
                name: formData.name,
                download_link: formData.download_link,
                type: formData.type
            };
            // Only include optional fields if they have values
            if (formData.file_size.trim()) {
                payload.file_size = formData.file_size.trim();
            }
            if (formData.description.trim()) {
                payload.description = formData.description.trim();
            }
            
            await axios.post(`${API}/submissions`, payload);
            toast.success('TRANSMISSION COMPLETE: Submission sent for approval');
            setFormData({ name: '', download_link: '', type: 'game', file_size: '', description: '' });
            setTimeout(() => navigate('/'), 2000);
        } catch (error) {
            console.error('Submission error:', error);
            toast.error('TRANSMISSION FAILED: Could not submit');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="main-content" data-testid="submit-page">
            <div className="retro-form">
                {/* Terminal Header */}
                <div style={{ 
                    borderBottom: '1px solid hsl(var(--border))', 
                    paddingBottom: '1rem', 
                    marginBottom: '1.5rem' 
                }}>
                    <h1 className="pixel-font neon-glow" style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>
                        <Terminal size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
                        SUBMIT NEW FILE
                    </h1>
                    <p style={{ fontSize: '0.875rem', opacity: 0.7 }}>
                        {'>'} Enter file details below. Max 10 submissions per day.
                    </p>
                    <p className="blink" style={{ fontSize: '0.875rem' }}>_</p>
                </div>

                <form onSubmit={handleSubmit}>
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
                            data-testid="submit-link-input"
                        />
                    </div>

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
                            data-testid="submit-type-select"
                        >
                            {typeOptions.map(option => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
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
                                data-testid="submit-size-input"
                            />
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
                                data-testid="submit-description-input"
                            />
                        </div>
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
                            disabled={submitting}
                            style={{ flex: 2 }}
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

                {/* ASCII Art Footer */}
                <div style={{ 
                    marginTop: '2rem', 
                    paddingTop: '1rem', 
                    borderTop: '1px solid hsl(var(--border))',
                    fontSize: '0.75rem',
                    opacity: 0.5,
                    textAlign: 'center'
                }}>
                    <pre style={{ fontFamily: 'inherit' }}>
{`╔════════════════════════════════╗
║  SUBMISSIONS REQUIRE APPROVAL  ║
╚════════════════════════════════╝`}
                    </pre>
                </div>
            </div>
        </div>
    );
}
