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
        .submissions-badge { background: var(--error); color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; margin-left: 10px; }
        .sponsored-form { margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border-color); }
        .sponsored-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid var(--border-color); margin-bottom: 10px; }
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
                                <label>Daily Submission Limit</label>
                                <input type="number" name="daily_submission_limit" value="<?= $settings['daily_submission_limit'] ?? 10 ?>" min="5" max="100">
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" name="auto_approve_submissions" <?= $settings['auto_approve_submissions'] ? 'checked' : '' ?>>
                                    Auto-approve submissions
                                </label>
                            </div>
                            <button type="submit" class="btn">SAVE SETTINGS</button>
                        </form>
                    </div>

                    <!-- Top Downloads Settings -->
                    <div class="admin-card">
                        <h3>Top Downloads</h3>
                        <form id="topDownloadsForm">
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" name="top_downloads_enabled" <?= $settings['top_downloads_enabled'] ? 'checked' : '' ?>>
                                    Enable Top Downloads
                                </label>
                            </div>
                            <div class="form-group">
                                <label>Number to Show</label>
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
                                    <input type="checkbox" name="trending_downloads_enabled" <?= $settings['trending_downloads_enabled'] ? 'checked' : '' ?>>
                                    Enable Trending Section
                                </label>
                            </div>
                            <div class="form-group">
                                <label>Number to Show</label>
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
                            <button type="submit" class="btn btn-secondary">UPDATE EMAIL</button>
                        </form>
                    </div>

                    <!-- Sponsored Downloads -->
                    <div class="admin-card" style="grid-column: span 2;">
                        <h3>Sponsored Downloads</h3>
                        <div id="sponsoredList">
                            <?php 
                            $sponsored = $settings['sponsored_downloads'] ?? [];
                            foreach ($sponsored as $item): ?>
                                <div class="sponsored-item" data-id="<?= htmlspecialchars($item['id'] ?? '') ?>">
                                    <span><?= htmlspecialchars($item['name'] ?? 'Unknown') ?></span>
                                    <button class="btn btn-danger btn-sm" onclick="removeSponsored('<?= htmlspecialchars($item['id'] ?? '') ?>')">Remove</button>
                                </div>
                            <?php endforeach; ?>
                        </div>
                        <div class="sponsored-form">
                            <h4>Add Sponsored Download</h4>
                            <form id="addSponsoredForm">
                                <div class="form-group">
                                    <input type="text" name="name" placeholder="Name" required>
                                </div>
                                <div class="form-group">
                                    <input type="url" name="download_link" placeholder="Download URL" required>
                                </div>
                                <div class="form-group">
                                    <select name="type" required>
                                        <option value="game">Game</option>
                                        <option value="software">Software</option>
                                        <option value="movie">Movie</option>
                                        <option value="tv_show">TV Show</option>
                                    </select>
                                </div>
                                <button type="submit" class="btn">ADD SPONSORED</button>
                            </form>
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

        // Add Sponsored Form
        document.getElementById('addSponsoredForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const newItem = {
                id: Date.now().toString(),
                name: formData.get('name'),
                download_link: formData.get('download_link'),
                type: formData.get('type')
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
                
                let html = '<table style="width:100%;">';
                html += '<tr><th>Name</th><th>24h</th><th>7d</th><th>Total</th></tr>';
                data.analytics.forEach(item => {
                    html += `<tr>
                        <td>${item.name}</td>
                        <td>${item.clicks_24h}</td>
                        <td>${item.clicks_7d}</td>
                        <td>${item.total_clicks}</td>
                    </tr>`;
                });
                html += '</table>';
                container.innerHTML = html;
            } catch (error) {
                document.getElementById('sponsoredAnalytics').innerHTML = 'Error loading analytics';
            }
        }
        
        loadAnalytics();
    </script>
    <?php endif; ?>
</body>
</html>
