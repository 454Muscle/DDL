import { useMemo } from 'react';
import { useSiteSettings } from '../context/SiteSettingsContext';

function renderTemplate(template, vars) {
    if (!template) return '';
    let out = template;
    Object.keys(vars).forEach((k) => {
        out = out.replaceAll(`{${k}}`, vars[k] || '');
    });
    // trim and collapse if placeholders missing
    return out.replace(/\s+/g, ' ').trim();
}

export default function Footer() {
    const { settings } = useSiteSettings();

    const lines = useMemo(() => {
        if (!settings || !settings.footer_enabled) return [];
        const vars = {
            admin_email: settings.admin_email || '',
            site_name: settings.site_name || '',
            year: String(new Date().getFullYear()),
        };

        const line1 = renderTemplate(settings.footer_line1_template, vars);
        const line2 = renderTemplate(settings.footer_line2_template, vars);

        const out = [];
        if (line1 && !line1.includes('{') && vars.admin_email) out.push(line1);
        else if (line1 && vars.admin_email) out.push(line1);

        if (line2 && vars.site_name) out.push(line2);

        // Hide lines if required values missing
        return out;
    }, [settings]);

    if (!lines.length) return null;

    return (
        <footer style={{
            marginTop: '2rem',
            padding: '1.25rem 1rem',
            borderTop: '1px solid hsl(var(--border))',
            textAlign: 'center',
            fontSize: '0.75rem',
            opacity: 0.75,
        }} data-testid="site-footer">
            {lines.map((l, idx) => (
                <div key={idx}>{l}</div>
            ))}
        </footer>
    );
}
