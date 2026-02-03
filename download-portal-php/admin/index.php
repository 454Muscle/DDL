<?php
/**
 * Download Portal - Admin Panel
 */
require_once __DIR__ . '/../includes/functions.php';
require_once __DIR__ . '/../includes/auth.php';

initSession();
$settings = getSiteSettings();
$theme = getThemeSettings();
$message = '';
$messageType = '';

// Check if admin needs initialization
$needsInit = empty($settings['admin_password_hash']);

// Handle login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    if ($_POST['action'] === 'login') {
        $password = $_POST['password'] ?? '';
        $result = authenticateAdmin($password);
        
        if ($result['success']) {
            loginAdmin();
            header('Location: index.php');
            exit;
        } else {
            $message = 'Invalid password';
            $messageType = 'error';
        }
    } elseif ($_POST['action'] === 'init') {
        $email = $_POST['email'] ?? '';
        $password = $_POST['password'] ?? '';
        
        if (empty($email) || empty($password)) {
            $message = 'Email and password are required';
            $messageType = 'error';
        } else {
            $result = initializeAdmin($email, $password);
            if ($result['success']) {
                loginAdmin();
                header('Location: index.php');
                exit;
            } else {
                $message = $result['error'];
                $messageType = 'error';
            }
        }
    } elseif ($_POST['action'] === 'logout') {
        logoutAdmin();
        header('Location: index.php');
        exit;
    }
}

// Check if logged in
$isLoggedIn = isAdminLoggedIn();

// Get pending count
$db = getDB();
$pendingCount = $db->query("SELECT COUNT(*) FROM submissions WHERE status = 'pending'")->fetchColumn();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - <?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></title>
    <link rel="stylesheet" href="../assets/css/style.css">
    <style>
        .admin-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .admin-card { background: var(--bg-secondary); border: 1px solid var(--border-color); padding: 20px; }
        .admin-card h3 { color: var(--accent); margin-bottom: 15px; }
        .admin-card h4 { color: var(--text-secondary); font-size: 0.9rem; }
        .submissions-badge { background: var(--error); color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; margin-left: 10px; }
        .sponsored-form { margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border-color); }
        .sponsored-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid var(--border-color); margin-bottom: 10px; background: var(--bg-tertiary); }
        .accent-presets { display: flex; gap: 8px; flex-wrap: wrap; }
        .accent-btn { width: 30px; height: 30px; border: 2px solid var(--border-color); cursor: pointer; transition: transform 0.2s; }
        .accent-btn:hover { transform: scale(1.1); border-color: var(--text-primary); }
        .btn-sm { padding: 6px 12px; font-size: 0.85rem; }
        hr { border: none; border-top: 1px solid var(--border-color); }
    </style>
</head>
<body class="<?= $theme['mode'] === 'light' ? 'light-theme' : '' ?>">
    <header>
        <div class="container">
            <div class="header-content">
                <a href="../index.php" class="logo"><?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></a>
                <nav>
                    <a href="../index.php">HOME</a>
                    <?php if ($isLoggedIn): ?>
                        <a href="submissions.php">SUBMISSIONS <?php if ($pendingCount > 0): ?><span class="submissions-badge"><?= $pendingCount ?></span><?php endif; ?></a>
                        <a href="index.php" class="active">DASHBOARD</a>
                        <form method="POST" style="display: inline;">
                            <input type="hidden" name="action" value="logout">
                            <button type="submit" class="btn btn-secondary">LOGOUT</button>
                        </form>
                    <?php endif; ?>
                </nav>
            </div>
        </div>
    </header>

    <main>
        <div class="container">
            <?php if ($message): ?>
                <div class="alert alert-<?= $messageType ?>"><?= htmlspecialchars($message) ?></div>
            <?php endif; ?>

            <?php if ($needsInit): ?>
                <!-- Admin Initialization -->
                <div style="max-width: 500px; margin: 50px auto;">
                    <h1 class="section-title">INITIALIZE ADMIN</h1>
                    <div class="admin-section">
                        <p style="margin-bottom: 20px; color: var(--text-muted);">Set up your admin account to get started.</p>
                        <form method="POST">
                            <input type="hidden" name="action" value="init">
                            <div class="form-group">
                                <label>Admin Email</label>
                                <input type="email" name="email" required placeholder="admin@example.com">
                            </div>
                            <div class="form-group">
                                <label>Admin Password</label>
                                <input type="password" name="password" required minlength="6" placeholder="••••••••">
                            </div>
                            <button type="submit" class="btn">INITIALIZE</button>
                        </form>
                    </div>
                </div>
            <?php elseif (!$isLoggedIn): ?>
                <!-- Login Form -->
                <div style="max-width: 500px; margin: 50px auto;">
                    <h1 class="section-title">ADMIN LOGIN</h1>
                    <div class="admin-section">
                        <form method="POST">
                            <input type="hidden" name="action" value="login">
                            <div class="form-group">
                                <label>Password</label>
                                <input type="password" name="password" required placeholder="••••••••">
                            </div>
                            <button type="submit" class="btn">LOGIN</button>
                        </form>
                    </div>
                </div>
            <?php else: ?>
                <!-- Admin Dashboard -->
                <div class="admin-header">
                    <h1 class="section-title">ADMIN DASHBOARD</h1>
                </div>

                <div class="admin-grid">
                    <!-- Site Settings -->
                    <div class="admin-card">
                        <h3>Site Settings</h3>
                        <form id="siteSettingsForm">
                            <div class="form-group">
                                <label>Site Name</label>
                                <input type="text" name="site_name" value="<?= htmlspecialchars($settings['site_name'] ?? '') ?>">
                            </div>
                            <div class="form-group">
                                <label>Daily Submission Limit (5-100)</label>
                                <input type="number" name="daily_submission_limit" value="<?= $settings['daily_submission_limit'] ?? 10 ?>" min="5" max="100">
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" name="auto_approve_submissions" <?= ($settings['auto_approve_submissions'] ?? false) ? 'checked' : '' ?>>
                                    Auto-approve submissions
                                </label>
                            </div>
                            <button type="submit" class="btn">SAVE SETTINGS</button>
                        </form>
                    </div>

                    <!-- Theme Settings -->
                    <div class="admin-card">
                        <h3>Theme Settings</h3>
                        <form id="themeForm">
                            <div class="form-group">
                                <label>Theme Mode</label>
                                <select name="theme_mode" id="themeModeSelect">
                                    <option value="dark" <?= ($theme['mode'] ?? 'dark') === 'dark' ? 'selected' : '' ?>>Dark</option>
                                    <option value="light" <?= ($theme['mode'] ?? 'dark') === 'light' ? 'selected' : '' ?>>Light</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Accent Color</label>
                                <div class="accent-presets">
                                    <button type="button" class="accent-btn" data-color="#00FF41" style="background:#00FF41" title="Matrix Green"></button>
                                    <button type="button" class="accent-btn" data-color="#FF00FF" style="background:#FF00FF" title="Cyber Magenta"></button>
                                    <button type="button" class="accent-btn" data-color="#00FFFF" style="background:#00FFFF" title="Electric Cyan"></button>
                                    <button type="button" class="accent-btn" data-color="#FFFF00" style="background:#FFFF00" title="Warning Yellow"></button>
                                    <button type="button" class="accent-btn" data-color="#FF6600" style="background:#FF6600" title="Neon Orange"></button>
                                    <button type="button" class="accent-btn" data-color="#0066FF" style="background:#0066FF" title="Classic Blue"></button>
                                </div>
                                <input type="color" name="accent_color" value="<?= htmlspecialchars($theme['accent_color'] ?? '#00FF41') ?>" style="width:100%; height:40px; margin-top:10px;">
                            </div>
                            <button type="submit" class="btn">UPDATE THEME</button>
                        </form>
                    </div>

                    <!-- Site Name Typography -->
                    <div class="admin-card">
                        <h3>Site Name Typography</h3>
                        <form id="siteNameTypographyForm">
                            <div class="form-group">
                                <label>Font Family</label>
                                <select name="site_name_font_family">
                                    <?php 
                                    $fonts = ['Arial', 'Inter', 'Roboto', 'Georgia', 'Times New Roman', 'Courier New', 'JetBrains Mono'];
                                    $currentFont = $settings['site_name_font_family'] ?? 'JetBrains Mono';
                                    foreach ($fonts as $font): ?>
                                        <option value="<?= $font ?>" <?= $currentFont === $font ? 'selected' : '' ?>><?= $font ?></option>
                                    <?php endforeach; ?>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Font Weight</label>
                                <select name="site_name_font_weight">
                                    <?php 
                                    $weights = ['300', '400', '500', '600', '700', '800'];
                                    $currentWeight = $settings['site_name_font_weight'] ?? '700';
                                    foreach ($weights as $weight): ?>
                                        <option value="<?= $weight ?>" <?= $currentWeight === $weight ? 'selected' : '' ?>><?= $weight ?></option>
                                    <?php endforeach; ?>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Font Color</label>
                                <input type="color" name="site_name_font_color" value="<?= htmlspecialchars($settings['site_name_font_color'] ?? '#00FF41') ?>">
                            </div>
                            <button type="submit" class="btn">UPDATE TYPOGRAPHY</button>
                        </form>
                    </div>

                    <!-- Body Typography -->
                    <div class="admin-card">
                        <h3>Body Typography</h3>
                        <form id="bodyTypographyForm">
                            <div class="form-group">
                                <label>Body Font Family</label>
                                <select name="body_font_family">
                                    <?php 
                                    $currentBodyFont = $settings['body_font_family'] ?? 'JetBrains Mono';
                                    foreach ($fonts as $font): ?>
                                        <option value="<?= $font ?>" <?= $currentBodyFont === $font ? 'selected' : '' ?>><?= $font ?></option>
                                    <?php endforeach; ?>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Body Font Weight</label>
                                <select name="body_font_weight">
                                    <?php 
                                    $currentBodyWeight = $settings['body_font_weight'] ?? '400';
                                    foreach ($weights as $weight): ?>
                                        <option value="<?= $weight ?>" <?= $currentBodyWeight === $weight ? 'selected' : '' ?>><?= $weight ?></option>
                                    <?php endforeach; ?>
                                </select>
                            </div>
                            <button type="submit" class="btn">UPDATE BODY FONT</button>
                        </form>
                    </div>

                    <!-- Footer Settings -->
                    <div class="admin-card" style="grid-column: span 2;">
                        <h3>Footer Settings</h3>
                        <form id="footerSettingsForm">
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" name="footer_enabled" <?= ($settings['footer_enabled'] ?? true) ? 'checked' : '' ?>>
                                    Enable Footer
                                </label>
                            </div>
                            <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 15px;">
                                Placeholders: <code>{admin_email}</code>, <code>{site_name}</code>, <code>{year}</code>
                            </p>
                            <div class="form-group">
                                <label>Footer Line 1 Template</label>
                                <input type="text" name="footer_line1_template" value="<?= htmlspecialchars($settings['footer_line1_template'] ?? 'For DMCA copyright complaints send an email to {admin_email}.') ?>">
                            </div>
                            <div class="form-group">
                                <label>Footer Line 2 Template</label>
                                <input type="text" name="footer_line2_template" value="<?= htmlspecialchars($settings['footer_line2_template'] ?? 'Copyright © {site_name} {year}. All rights reserved.') ?>">
                            </div>
                            <button type="submit" class="btn">UPDATE FOOTER</button>
                        </form>
                    </div>

                    <!-- Top Downloads Settings -->
                    <div class="admin-card">
                        <h3>Top Downloads</h3>
                        <form id="topDownloadsForm">
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" name="top_downloads_enabled" <?= ($settings['top_downloads_enabled'] ?? true) ? 'checked' : '' ?>>
                                    Enable Top Downloads
                                </label>
                            </div>
                            <div class="form-group">
                                <label>Number to Show (5-20)</label>
                                <input type="number" name="top_downloads_count" value="<?= $settings['top_downloads_count'] ?? 5 ?>" min="5" max="20">
                            </div>
                            <button type="submit" class="btn">SAVE</button>
                        </form>
                    </div>

                    <!-- Trending Settings -->
                    <div class="admin-card">
                        <h3>Trending Downloads</h3>
                        <form id="trendingForm">
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" name="trending_downloads_enabled" <?= ($settings['trending_downloads_enabled'] ?? false) ? 'checked' : '' ?>>
                                    Enable Trending Section
                                </label>
                            </div>
                            <div class="form-group">
                                <label>Number to Show (5-20)</label>
                                <input type="number" name="trending_downloads_count" value="<?= $settings['trending_downloads_count'] ?? 5 ?>" min="5" max="20">
                            </div>
                            <button type="submit" class="btn">SAVE</button>
                        </form>
                    </div>

                    <!-- Admin Credentials -->
                    <div class="admin-card">
                        <h3>Admin Credentials</h3>
                        <form id="adminEmailForm">
                            <div class="form-group">
                                <label>Admin Email</label>
                                <input type="email" name="admin_email" value="<?= htmlspecialchars($settings['admin_email'] ?? '') ?>">
                            </div>
                            <button type="submit" class="btn btn-secondary">SAVE EMAIL</button>
                        </form>
                        <hr style="margin: 20px 0; border-color: var(--border-color);">
                        <h4 style="margin-bottom: 15px;">Change Password</h4>
                        <form id="changePasswordForm">
                            <div class="form-group">
                                <label>Current Password</label>
                                <input type="password" name="current_password" placeholder="••••••••">
                            </div>
                            <div class="form-group">
                                <label>New Password</label>
                                <input type="password" name="new_password" placeholder="••••••••" minlength="6">
                            </div>
                            <button type="submit" class="btn btn-secondary">CHANGE PASSWORD</button>
                        </form>
                    </div>

                    <!-- Resend Email Settings -->
                    <div class="admin-card">
                        <h3>Resend Email Settings</h3>
                        <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 15px;">
                            Create an API key at <a href="https://resend.com/api-keys" target="_blank" style="color: var(--accent);">resend.com/api-keys</a>
                        </p>
                        <form id="resendForm">
                            <div class="form-group">
                                <label>Resend API Key</label>
                                <input type="password" name="resend_api_key" placeholder="re_...">
                            </div>
                            <div class="form-group">
                                <label>Sender Email (FROM)</label>
                                <input type="email" name="resend_sender_email" value="<?= htmlspecialchars($settings['resend_sender_email'] ?? '') ?>" placeholder="onboarding@resend.dev">
                            </div>
                            <button type="submit" class="btn">UPDATE RESEND</button>
                            <button type="button" class="btn btn-secondary" id="testResendBtn" style="margin-top:10px;">SEND TEST EMAIL</button>
                        </form>
                    </div>

                    <!-- reCAPTCHA Settings -->
                    <div class="admin-card">
                        <h3>reCAPTCHA Settings</h3>
                        <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 15px;">
                            Get keys from <a href="https://www.google.com/recaptcha/admin" target="_blank" style="color: var(--accent);">Google reCAPTCHA Admin</a>
                        </p>
                        <form id="recaptchaForm">
                            <div class="form-group">
                                <label>Site Key</label>
                                <input type="text" name="recaptcha_site_key" value="<?= htmlspecialchars($settings['recaptcha_site_key'] ?? '') ?>">
                            </div>
                            <div class="form-group">
                                <label>Secret Key</label>
                                <input type="password" name="recaptcha_secret_key" placeholder="••••••••">
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" name="recaptcha_enable_submit" <?= ($settings['recaptcha_enable_submit'] ?? false) ? 'checked' : '' ?>>
                                    Enable for Submissions
                                </label>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" name="recaptcha_enable_auth" <?= ($settings['recaptcha_enable_auth'] ?? false) ? 'checked' : '' ?>>
                                    Enable for Auth
                                </label>
                            </div>
                            <button type="submit" class="btn">UPDATE reCAPTCHA</button>
                        </form>
                    </div>

                    <!-- Sponsored Downloads -->
                    <div class="admin-card" style="grid-column: span 2;">
                        <h3>Sponsored Downloads (1-5)</h3>
                        <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 15px;">
                            Sponsored downloads appear first in the Top Downloads section
                        </p>
                        <div id="sponsoredList">
                            <?php 
                            $sponsored = $settings['sponsored_downloads'] ?? [];
                            foreach ($sponsored as $index => $item): ?>
                                <div class="sponsored-item" data-id="<?= htmlspecialchars($item['id'] ?? '') ?>">
                                    <span><strong>#<?= $index + 1 ?></strong> <?= htmlspecialchars($item['name'] ?? 'Unknown') ?> <small>(<?= htmlspecialchars($item['type'] ?? '') ?>)</small></span>
                                    <button class="btn btn-danger btn-sm" onclick="removeSponsored('<?= htmlspecialchars($item['id'] ?? '') ?>')">Remove</button>
                                </div>
                            <?php endforeach; ?>
                        </div>
                        <?php if (count($sponsored) < 5): ?>
                        <div class="sponsored-form">
                            <h4>Add Sponsored Download (<?= count($sponsored) ?>/5)</h4>
                            <form id="addSponsoredForm">
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                    <div class="form-group">
                                        <label>Name *</label>
                                        <input type="text" name="name" placeholder="Download name" required>
                                    </div>
                                    <div class="form-group">
                                        <label>Download Link *</label>
                                        <input type="url" name="download_link" placeholder="https://..." required>
                                    </div>
                                    <div class="form-group">
                                        <label>Type</label>
                                        <select name="type">
                                            <option value="game">Game</option>
                                            <option value="software" selected>Software</option>
                                            <option value="movie">Movie</option>
                                            <option value="tv_show">TV Show</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label>Description</label>
                                        <input type="text" name="description" placeholder="Optional description">
                                    </div>
                                </div>
                                <button type="submit" class="btn" style="margin-top: 15px;">ADD SPONSORED</button>
                            </form>
                        </div>
                        <?php endif; ?>
                    </div>

                    <!-- Manage Downloads -->
                    <div class="admin-card" style="grid-column: span 2;">
                        <h3>Manage Downloads</h3>
                        <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                            <input type="text" id="downloadsSearchInput" class="search-input" placeholder="Search downloads..." style="flex: 1;">
                            <button class="btn" id="downloadsSearchBtn">SEARCH</button>
                        </div>
                        <div id="downloadsManageTable">
                            <p style="color: var(--text-muted);">Enter a search term to find downloads</p>
                        </div>
                    </div>

                    <!-- Quick Actions -->
                    <div class="admin-card">
                        <h3>Quick Actions</h3>
                        <button class="btn mb-20" onclick="seedDatabase()">SEED DATABASE (5000 items)</button>
                        <a href="submissions.php" class="btn btn-secondary">MANAGE SUBMISSIONS</a>
                    </div>

                    <!-- Sponsored Analytics -->
                    <div class="admin-card">
                        <h3>Sponsored Analytics</h3>
                        <div id="sponsoredAnalytics">Loading...</div>
                        <button class="btn btn-secondary" onclick="loadAnalytics()" style="margin-top: 15px;">REFRESH ANALYTICS</button>
                    </div>
                </div>
            <?php endif; ?>
        </div>
    </main>

    <footer>
        <div class="container">
            <div class="footer-content">
                <p>Admin Panel - <?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></p>
            </div>
        </div>
    </footer>

    <?php if ($isLoggedIn): ?>
    <script>
        const API = '../api';
        let sponsoredDownloads = <?= json_encode($settings['sponsored_downloads'] ?? []) ?>;

        // Site Settings Form
        document.getElementById('siteSettingsForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                site_name: formData.get('site_name'),
                daily_submission_limit: parseInt(formData.get('daily_submission_limit')),
                auto_approve_submissions: formData.has('auto_approve_submissions')
            };
            await updateSettings(data);
        });

        // Theme Form
        document.getElementById('themeForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                mode: formData.get('theme_mode'),
                accent_color: formData.get('accent_color')
            };
            try {
                const response = await fetch(`${API}/theme.php`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (result.error) {
                    alert('Error: ' + result.error);
                } else {
                    alert('Theme updated!');
                    location.reload();
                }
            } catch (error) {
                alert('Error updating theme');
            }
        });

        // Accent color preset buttons
        document.querySelectorAll('.accent-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const color = btn.dataset.color;
                document.querySelector('input[name="accent_color"]').value = color;
            });
        });

        // Site Name Typography Form
        document.getElementById('siteNameTypographyForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                site_name_font_family: formData.get('site_name_font_family'),
                site_name_font_weight: formData.get('site_name_font_weight'),
                site_name_font_color: formData.get('site_name_font_color')
            };
            await updateSettings(data);
        });

        // Body Typography Form
        document.getElementById('bodyTypographyForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                body_font_family: formData.get('body_font_family'),
                body_font_weight: formData.get('body_font_weight')
            };
            await updateSettings(data);
        });

        // Footer Settings Form
        document.getElementById('footerSettingsForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                footer_enabled: formData.has('footer_enabled'),
                footer_line1_template: formData.get('footer_line1_template'),
                footer_line2_template: formData.get('footer_line2_template')
            };
            await updateSettings(data);
        });

        // Top Downloads Form
        document.getElementById('topDownloadsForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                top_downloads_enabled: formData.has('top_downloads_enabled'),
                top_downloads_count: parseInt(formData.get('top_downloads_count'))
            };
            await updateSettings(data);
        });

        // Trending Form
        document.getElementById('trendingForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                trending_downloads_enabled: formData.has('trending_downloads_enabled'),
                trending_downloads_count: parseInt(formData.get('trending_downloads_count'))
            };
            await updateSettings(data);
        });

        // Admin Email Form
        document.getElementById('adminEmailForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = { admin_email: formData.get('admin_email') };
            await updateSettings(data);
        });

        // Change Password Form
        document.getElementById('changePasswordForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const currentPassword = formData.get('current_password');
            const newPassword = formData.get('new_password');
            
            if (!currentPassword || !newPassword) {
                alert('Both current and new password are required');
                return;
            }
            if (newPassword.length < 6) {
                alert('New password must be at least 6 characters');
                return;
            }
            
            try {
                const response = await fetch(`${API}/admin.php?action=change-password`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                });
                const result = await response.json();
                if (result.error) {
                    alert('Error: ' + result.error);
                } else {
                    alert('Password changed successfully!');
                    e.target.reset();
                }
            } catch (error) {
                alert('Error changing password');
            }
        });

        // Resend Form
        document.getElementById('resendForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                resend_api_key: formData.get('resend_api_key'),
                resend_sender_email: formData.get('resend_sender_email')
            };
            await updateSettings(data);
        });

        // Test Resend Email
        document.getElementById('testResendBtn')?.addEventListener('click', async () => {
            try {
                const response = await fetch(`${API}/admin.php?action=test-email`, { method: 'POST' });
                const result = await response.json();
                if (result.error) {
                    alert('Error: ' + result.error);
                } else {
                    alert('Test email sent to admin email!');
                }
            } catch (error) {
                alert('Error sending test email');
            }
        });

        // reCAPTCHA Form
        document.getElementById('recaptchaForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                recaptcha_site_key: formData.get('recaptcha_site_key'),
                recaptcha_secret_key: formData.get('recaptcha_secret_key'),
                recaptcha_enable_submit: formData.has('recaptcha_enable_submit'),
                recaptcha_enable_auth: formData.has('recaptcha_enable_auth')
            };
            await updateSettings(data);
        });

        // Add Sponsored Form
        document.getElementById('addSponsoredForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const newItem = {
                id: Date.now().toString(),
                name: formData.get('name'),
                download_link: formData.get('download_link'),
                type: formData.get('type'),
                description: formData.get('description') || ''
            };
            sponsoredDownloads.push(newItem);
            await updateSettings({ sponsored_downloads: sponsoredDownloads });
            location.reload();
        });

        async function updateSettings(data) {
            try {
                const response = await fetch(`${API}/settings.php?action=update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (result.error) {
                    alert('Error: ' + result.error);
                } else {
                    alert('Settings saved!');
                }
            } catch (error) {
                alert('Error saving settings');
            }
        }

        async function removeSponsored(id) {
            if (!confirm('Remove this sponsored download?')) return;
            sponsoredDownloads = sponsoredDownloads.filter(s => s.id !== id);
            await updateSettings({ sponsored_downloads: sponsoredDownloads });
            location.reload();
        }

        async function seedDatabase() {
            if (!confirm('This will seed the database with 5000 sample downloads. Continue?')) return;
            try {
                const response = await fetch(`${API}/admin.php?action=seed`, { method: 'POST' });
                const result = await response.json();
                alert(result.message || 'Database seeded!');
            } catch (error) {
                alert('Error seeding database');
            }
        }

        // Load Sponsored Analytics
        async function loadAnalytics() {
            try {
                const response = await fetch(`${API}/admin.php?action=sponsored-analytics`);
                const data = await response.json();
                const container = document.getElementById('sponsoredAnalytics');
                
                if (!data.analytics?.length) {
                    container.innerHTML = '<p style="color: var(--text-muted);">No sponsored downloads configured</p>';
                    return;
                }
                
                let html = '<table style="width:100%; font-size: 0.85rem;">';
                html += '<tr><th style="text-align:left;">#</th><th style="text-align:left;">Name</th><th>24h</th><th>7d</th><th>Total</th></tr>';
                data.analytics.forEach((item, index) => {
                    html += `<tr>
                        <td style="color: var(--sponsored-border); font-weight: bold;">#${index + 1}</td>
                        <td>${item.name}</td>
                        <td style="text-align:center; color: var(--success);">${item.clicks_24h}</td>
                        <td style="text-align:center; color: #00FFFF;">${item.clicks_7d}</td>
                        <td style="text-align:center; color: #FF00FF;">${item.total_clicks}</td>
                    </tr>`;
                });
                html += '</table>';
                container.innerHTML = html;
            } catch (error) {
                document.getElementById('sponsoredAnalytics').innerHTML = 'Error loading analytics';
            }
        }

        // Downloads Management
        let downloadsPage = 1;
        let downloadsTotalPages = 1;

        document.getElementById('downloadsSearchBtn')?.addEventListener('click', () => {
            downloadsPage = 1;
            searchDownloads();
        });

        document.getElementById('downloadsSearchInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                downloadsPage = 1;
                searchDownloads();
            }
        });

        async function searchDownloads() {
            const search = document.getElementById('downloadsSearchInput')?.value || '';
            const container = document.getElementById('downloadsManageTable');
            
            if (!search.trim()) {
                container.innerHTML = '<p style="color: var(--text-muted);">Enter a search term to find downloads</p>';
                return;
            }
            
            container.innerHTML = '<p class="loading">Searching...</p>';
            
            try {
                const response = await fetch(`${API}/admin.php?action=search-downloads&search=${encodeURIComponent(search)}&page=${downloadsPage}&limit=20`);
                const data = await response.json();
                
                if (data.error) {
                    container.innerHTML = `<p class="alert alert-error">${data.error}</p>`;
                    return;
                }
                
                downloadsTotalPages = data.pages || 1;
                
                if (!data.items?.length) {
                    container.innerHTML = '<p style="color: var(--text-muted);">No downloads found</p>';
                    return;
                }
                
                let html = '<table class="downloads-table">';
                html += '<thead><tr><th>Name</th><th>Type</th><th>Date</th><th>Action</th></tr></thead>';
                html += '<tbody>';
                data.items.forEach(item => {
                    html += `<tr>
                        <td>${escapeHtml(item.name)}</td>
                        <td>${item.type}</td>
                        <td>${item.submission_date || ''}</td>
                        <td><button class="btn btn-danger btn-sm" onclick="deleteDownload('${item.id}')">DELETE</button></td>
                    </tr>`;
                });
                html += '</tbody></table>';
                
                // Pagination
                html += '<div style="display: flex; justify-content: space-between; margin-top: 15px; font-size: 0.85rem;">';
                html += `<button class="btn btn-secondary btn-sm" onclick="prevDownloadsPage()" ${downloadsPage <= 1 ? 'disabled' : ''}>Prev</button>`;
                html += `<span>Page ${downloadsPage} / ${downloadsTotalPages}</span>`;
                html += `<button class="btn btn-secondary btn-sm" onclick="nextDownloadsPage()" ${downloadsPage >= downloadsTotalPages ? 'disabled' : ''}>Next</button>`;
                html += '</div>';
                
                container.innerHTML = html;
            } catch (error) {
                container.innerHTML = '<p class="alert alert-error">Error searching downloads</p>';
            }
        }

        function prevDownloadsPage() {
            if (downloadsPage > 1) {
                downloadsPage--;
                searchDownloads();
            }
        }

        function nextDownloadsPage() {
            if (downloadsPage < downloadsTotalPages) {
                downloadsPage++;
                searchDownloads();
            }
        }

        async function deleteDownload(id) {
            if (!confirm('Delete this download? This cannot be undone.')) return;
            
            try {
                const response = await fetch(`${API}/admin.php?action=delete-download&id=${id}`, { method: 'POST' });
                const result = await response.json();
                if (result.error) {
                    alert('Error: ' + result.error);
                } else {
                    alert('Download deleted!');
                    searchDownloads();
                }
            } catch (error) {
                alert('Error deleting download');
            }
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        loadAnalytics();
    </script>
    <?php endif; ?>
</body>
</html>
