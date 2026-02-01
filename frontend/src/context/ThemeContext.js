import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ThemeContext = createContext();

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within ThemeProvider');
    }
    return context;
};

export const ThemeProvider = ({ children }) => {
    const [theme, setTheme] = useState({
        mode: 'dark',
        accent_color: '#00FF41'
    });
    const [loading, setLoading] = useState(true);

    const fetchTheme = async () => {
        try {
            const response = await axios.get(`${API}/theme`);
            setTheme(response.data);
        } catch (error) {
            console.error('Error fetching theme:', error);
        } finally {
            setLoading(false);
        }
    };

    const updateTheme = async (updates) => {
        try {
            const response = await axios.put(`${API}/theme`, updates);
            setTheme(response.data);
            return response.data;
        } catch (error) {
            console.error('Error updating theme:', error);
            throw error;
        }
    };

    useEffect(() => {
        fetchTheme();
    }, []);

    useEffect(() => {
        // Apply theme to document
        const root = document.documentElement;
        
        if (theme.mode === 'light') {
            document.body.classList.add('light-theme');
            document.body.classList.remove('crt-effect');
        } else {
            document.body.classList.remove('light-theme');
            document.body.classList.add('crt-effect');
        }

        // Apply accent color as CSS variable
        root.style.setProperty('--accent-color', theme.accent_color);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, updateTheme, loading, fetchTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};
