import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { Download, Upload, Shield, Sun, Moon } from 'lucide-react';

export const Header = () => {
    const location = useLocation();
    const { theme, updateTheme } = useTheme();

    const isActive = (path) => location.pathname === path;

    const toggleTheme = async () => {
        const newMode = theme.mode === 'dark' ? 'light' : 'dark';
        try {
            await updateTheme({ mode: newMode });
        } catch (error) {
            console.error('Theme toggle error:', error);
        }
    };

    return (
        <header className="nav-header">
            <div style={{ 
                maxWidth: '1400px', 
                margin: '0 auto',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '1rem'
            }}>
                {/* Logo/Title */}
                <Link 
                    to="/" 
                    style={{ textDecoration: 'none' }}
                    data-testid="header-logo"
                >
                    <h1 className="pixel-font neon-glow" style={{ 
                        fontSize: '0.875rem',
                        margin: 0,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}>
                        <Download size={20} />
                        DOWNLOAD ZONE
                    </h1>
                </Link>

                {/* Navigation */}
                <nav style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <Link 
                        to="/" 
                        className={`nav-link ${isActive('/') ? 'active' : ''}`}
                        data-testid="nav-home"
                    >
                        <Download size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                        DOWNLOADS
                    </Link>
                    <Link 
                        to="/submit" 
                        className={`nav-link ${isActive('/submit') ? 'active' : ''}`}
                        data-testid="nav-submit"
                    >
                        <Upload size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                        SUBMIT
                    </Link>
                    <Link 
                        to="/admin" 
                        className={`nav-link ${isActive('/admin') || isActive('/admin/dashboard') ? 'active' : ''}`}
                        data-testid="nav-admin"
                    >
                        <Shield size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
                        ADMIN
                    </Link>
                    
                    {/* Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        className="nav-link"
                        style={{ 
                            background: 'transparent',
                            cursor: 'pointer',
                            border: '1px solid hsl(var(--border))'
                        }}
                        data-testid="theme-toggle"
                        title={`Switch to ${theme.mode === 'dark' ? 'light' : 'dark'} mode`}
                    >
                        {theme.mode === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                    </button>
                </nav>
            </div>
        </header>
    );
};
