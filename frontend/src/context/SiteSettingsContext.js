import { createContext, useContext, useEffect, useState } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SiteSettingsContext = createContext();

export const useSiteSettings = () => {
    const ctx = useContext(SiteSettingsContext);
    if (!ctx) {
        throw new Error('useSiteSettings must be used within SiteSettingsProvider');
    }
    return ctx;
};

export const SiteSettingsProvider = ({ children }) => {
    const [settings, setSettings] = useState(null);

    const fetchSettings = async () => {
        try {
            const res = await axios.get(`${API}/settings`);
            setSettings(res.data);
        } catch (e) {
            console.error('Error fetching site settings', e);
        }
    };

    useEffect(() => {
        fetchSettings();
    }, []);

    useEffect(() => {
        if (!settings) return;
        const root = document.documentElement;

        // Typography (global)
        if (settings.body_font_family) {
            root.style.setProperty('--body-font-family', settings.body_font_family);
        }
        if (settings.body_font_weight) {
            root.style.setProperty('--body-font-weight', settings.body_font_weight);
        }

        // Site name styling
        if (settings.site_name_font_family) {
            root.style.setProperty('--site-name-font-family', settings.site_name_font_family);
        }
        if (settings.site_name_font_weight) {
            root.style.setProperty('--site-name-font-weight', settings.site_name_font_weight);
        }
        if (settings.site_name_font_color) {
            root.style.setProperty('--site-name-font-color', settings.site_name_font_color);
        }

        // Browser tab title
        if (settings.site_name) {
            document.title = settings.site_name;
        }
    }, [settings]);

    return (
        <SiteSettingsContext.Provider value={{ settings, fetchSettings, setSettings }}>
            {children}
        </SiteSettingsContext.Provider>
    );
};
