import { useMemo } from 'react';
import { useSiteSettings } from '../context/SiteSettingsContext';

function hasPlaceholder(template, key) {
    return (template || '').includes(`{${key}}`);
}

function renderTemplate(template, vars) {
    if (!template) return '';
    let out = template;
    Object.keys(vars).forEach((k) => {
        out = out.replaceAll(`{${k}}`, vars[k] || '');
    });
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

        const t1 = settings.footer_line1_template;
        const t2 = settings.footer_line2_template;

        // Hide lines if required placeholder values are missing
        if (hasPlaceholder(t1, 'admin_email') && !vars.admin_email) {
            // hide
        }

        const out = [];
        if (!(hasPlaceholder(t1, 'admin_email') && !vars.admin_email)) {
            const l1 = renderTemplate(t1, vars);
            if (l1) out.push(l1);
        }

        if (!(hasPlaceholder(t2, 'site_name') && !vars.site_name)) {
            const l2 = renderTemplate(t2, vars);
            if (l2) out.push(l2);
        }

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
