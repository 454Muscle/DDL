<?php
/**
 * Download Portal - Submit Page
 */

// Check if we need to redirect to installer
if (file_exists(__DIR__ . '/install.php')) {
    require_once __DIR__ . '/config/database.php';
    try {
        $db = getDB();
        $stmt = $db->query("SHOW TABLES LIKE 'site_settings'");
        if ($stmt->rowCount() === 0) {
            header('Location: install.php');
            exit;
        }
    } catch (Exception $e) {
        header('Location: install.php');
        exit;
    }
}

require_once __DIR__ . '/includes/functions.php';
require_once __DIR__ . '/includes/captcha.php';

$settings = getSiteSettings();
$theme = getThemeSettings();
$captcha = generateCaptcha();

// Get rate limit info
$ip = getClientIP();
$dailyLimit = (int)($settings['daily_submission_limit'] ?? 10);
$rateLimit = checkRateLimit($ip, $dailyLimit);

// Get categories
$db = getDB();
$categories = $db->query("SELECT DISTINCT name, type FROM categories ORDER BY name")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submit - <?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></title>
    <link rel="stylesheet" href="assets/css/style.css">
    <style>
        .rate-limit-bar {
            padding: 12px 15px;
            margin-bottom: 20px;
            border: 1px solid;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .rate-limit-bar.ok { border-color: var(--success); background: rgba(0, 255, 65, 0.1); }
        .rate-limit-bar.warning { border-color: var(--warning); background: rgba(255, 170, 0, 0.1); }
        .rate-limit-bar.error { border-color: var(--error); background: rgba(255, 68, 68, 0.1); }
        .mode-toggle { display: flex; gap: 10px; margin-bottom: 20px; }
        .mode-btn { padding: 10px 20px; background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-primary); cursor: pointer; }
        .mode-btn.active { background: var(--accent); color: var(--bg-primary); border-color: var(--accent); }
        .batch-item { border: 1px solid var(--border-color); padding: 20px; margin-bottom: 15px; position: relative; }
        .batch-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color); }
        .batch-item-number { color: var(--accent); font-weight: bold; }
        .remove-item-btn { background: var(--error); color: white; border: none; padding: 5px 15px; cursor: pointer; font-size: 0.85rem; }
        .remove-item-btn:hover { opacity: 0.8; }
        .remove-item-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .add-item-btn { margin-bottom: 20px; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        @media (max-width: 768px) { .form-row { grid-template-columns: 1fr; } }
        .batch-info { font-size: 0.85rem; color: var(--text-muted); margin-top: 5px; }
    </style>
</head>
<body class="<?= ($theme['mode'] ?? 'dark') === 'light' ? 'light-theme' : '' ?>">
    <header>
        <div class="container">
            <div class="header-content">
                <a href="index.php" class="logo"><?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></a>
                <nav>
                    <a href="index.php">HOME</a>
                    <a href="submit.php" class="active">SUBMIT</a>
                    <a href="login.php">LOGIN</a>
                    <a href="admin/">ADMIN</a>
                    <button class="theme-toggle" id="themeToggle"><?= ($theme['mode'] ?? 'dark') === 'dark' ? '☀ LIGHT' : '☾ DARK' ?></button>
                </nav>
            </div>
        </div>
    </header>

    <main>
        <div class="container">
            <h1 class="section-title">SUBMIT NEW DOWNLOAD</h1>
            
            <!-- Rate Limit Info -->
            <div class="rate-limit-bar <?= $rateLimit['remaining'] <= 0 ? 'error' : ($rateLimit['remaining'] <= 3 ? 'warning' : 'ok') ?>" id="rateLimitBar">
                <span>
                    DAILY SUBMISSIONS: <strong id="rateLimitUsed"><?= $rateLimit['used'] ?></strong> / <strong><?= $dailyLimit ?></strong>
                    &nbsp;|&nbsp;
                    REMAINING: <strong id="rateLimitRemaining" style="color: <?= $rateLimit['remaining'] <= 0 ? 'var(--error)' : 'var(--success)' ?>"><?= $rateLimit['remaining'] ?></strong>
                </span>
            </div>
            
            <!-- Mode Toggle -->
            <div class="mode-toggle">
                <button type="button" class="mode-btn active" id="singleModeBtn">SINGLE SUBMIT</button>
                <button type="button" class="mode-btn" id="multiModeBtn">SUBMIT MULTIPLE</button>
            </div>
            
            <!-- Alert Container -->
            <div id="alertContainer"></div>
            
            <div class="admin-section">
                <!-- Single Submit Form -->
                <form id="singleForm" style="display: block;">
                    <div class="form-group">
                        <label>Name *</label>
                        <input type="text" name="name" required placeholder="e.g., Super Game v1.0">
                    </div>
                    
                    <div class="form-group">
                        <label>Download Link *</label>
                        <input type="url" name="download_link" required placeholder="https://...">
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Site Name * (max 15 chars)</label>
                            <input type="text" name="site_name" required maxlength="15" placeholder="e.g., MySite">
                        </div>
                        <div class="form-group">
                            <label>Site URL *</label>
                            <input type="url" name="site_url" required placeholder="https://mysite.com">
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Type *</label>
                            <select name="type" required onchange="updateCategories(this.value, 'singleCategory')">
                                <option value="">Select type...</option>
                                <option value="game">Game</option>
                                <option value="software">Software</option>
                                <option value="movie">Movie</option>
                                <option value="tv_show">TV Show</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Category</label>
                            <select name="category" id="singleCategory">
                                <option value="">Select category...</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>File Size</label>
                            <input type="text" name="file_size" placeholder="e.g., 5.2 GB">
                        </div>
                        <div class="form-group">
                            <label>Your Email (for notifications)</label>
                            <input type="email" name="submitter_email" placeholder="your@email.com">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Tags (comma separated)</label>
                        <input type="text" name="tags" placeholder="e.g., action, multiplayer, HD">
                    </div>
                    
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" placeholder="Brief description..."></textarea>
                    </div>
                    
                    <!-- Captcha -->
                    <div class="captcha-section">
                        <label>Solve to verify you're human:</label>
                        <div class="captcha-challenge" id="singleCaptchaChallenge"><?= htmlspecialchars($captcha['challenge']) ?></div>
                        <input type="hidden" name="captcha_id" id="singleCaptchaId" value="<?= htmlspecialchars($captcha['id']) ?>">
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <input type="number" name="captcha_answer" required placeholder="Your answer" class="search-input" style="max-width: 200px;">
                            <button type="button" class="btn btn-secondary" onclick="refreshCaptcha('single')">↻ REFRESH</button>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn" id="singleSubmitBtn" <?= $rateLimit['remaining'] <= 0 ? 'disabled' : '' ?>>SUBMIT</button>
                </form>
                
                <!-- Multi Submit Form -->
                <form id="multiForm" style="display: none;">
                    <div id="batchItemsContainer">
                        <!-- Items will be added here dynamically -->
                    </div>
                    
                    <button type="button" class="btn btn-secondary add-item-btn" onclick="addBatchItem()" id="addItemBtn">+ ADD ANOTHER ITEM</button>
                    
                    <div class="form-group">
                        <label>Your Email (for all items)</label>
                        <input type="email" name="submitter_email" id="multiSubmitterEmail" placeholder="your@email.com">
                    </div>
                    
                    <!-- Captcha for batch -->
                    <div class="captcha-section">
                        <label>Solve to verify you're human:</label>
                        <div class="captcha-challenge" id="multiCaptchaChallenge"><?= htmlspecialchars($captcha['challenge']) ?></div>
                        <input type="hidden" name="captcha_id" id="multiCaptchaId" value="<?= htmlspecialchars($captcha['id']) ?>">
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <input type="number" name="captcha_answer" id="multiCaptchaAnswer" required placeholder="Your answer" class="search-input" style="max-width: 200px;">
                            <button type="button" class="btn btn-secondary" onclick="refreshCaptcha('multi')">↻ REFRESH</button>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn" id="multiSubmitBtn" <?= $rateLimit['remaining'] <= 0 ? 'disabled' : '' ?>>SUBMIT ALL ITEMS</button>
                </form>
            </div>
        </div>
    </main>

    <footer>
        <div class="container">
            <div class="footer-content">
                <p><?= htmlspecialchars(str_replace('{admin_email}', $settings['admin_email'] ?? '', $settings['footer_line1_template'] ?? '')) ?></p>
                <p><?= htmlspecialchars(str_replace(['{site_name}', '{year}'], [$settings['site_name'] ?? 'DOWNLOAD ZONE', date('Y')], $settings['footer_line2_template'] ?? '')) ?></p>
            </div>
        </div>
    </footer>

    <script>
        const API = 'api';
        const categories = <?= json_encode($categories ?: []) ?>;
        let currentMode = 'single';
        let batchItems = [];
        let rateLimit = {
            daily_limit: <?= $dailyLimit ?>,
            used: <?= (int)$rateLimit['used'] ?>,
            remaining: <?= (int)$rateLimit['remaining'] ?>
        };
        
        // Utility functions (defined first)
        function showAlert(message, type) {
            const container = document.getElementById('alertContainer');
            if (container) {
                container.innerHTML = '<div class="alert alert-' + type + '">' + escapeHtml(message) + '</div>';
                setTimeout(function() { container.innerHTML = ''; }, 5000);
            }
        }
        
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function setMode(mode) {
            currentMode = mode;
            var singleBtn = document.getElementById('singleModeBtn');
            var multiBtn = document.getElementById('multiModeBtn');
            var singleForm = document.getElementById('singleForm');
            var multiForm = document.getElementById('multiForm');
            
            if (singleBtn) singleBtn.classList.toggle('active', mode === 'single');
            if (multiBtn) multiBtn.classList.toggle('active', mode === 'multi');
            if (singleForm) singleForm.style.display = mode === 'single' ? 'block' : 'none';
            if (multiForm) multiForm.style.display = mode === 'multi' ? 'block' : 'none';
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            // Mode toggle buttons
            var singleBtn = document.getElementById('singleModeBtn');
            var multiBtn = document.getElementById('multiModeBtn');
            
            if (singleBtn) {
                singleBtn.addEventListener('click', function() {
                    setMode('single');
                });
            }
            if (multiBtn) {
                multiBtn.addEventListener('click', function() {
                    setMode('multi');
                });
            }
            
            // Add first item for multi mode (even if rate limit is 0, show the form)
            try {
                addBatchItem(true);
            } catch (e) {
                console.error('Error adding batch item:', e);
            }
            
            // Single form submit
            var singleForm = document.getElementById('singleForm');
            if (singleForm) {
                singleForm.addEventListener('submit', handleSingleSubmit);
            }
            
            // Multi form submit
            var multiForm = document.getElementById('multiForm');
            if (multiForm) {
                multiForm.addEventListener('submit', handleMultiSubmit);
            }
        });
        
        function updateCategories(type, selectId) {
            const select = document.getElementById(selectId);
            if (!select) return;
            select.innerHTML = '<option value="">Select category...</option>';
            
            if (!categories || !Array.isArray(categories)) return;
            
            categories.filter(c => c.type === type || c.type === 'all').forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.name;
                option.textContent = cat.name;
                select.appendChild(option);
            });
        }
        
        function addBatchItem(isFirst = false) {
            // Allow first item even if rate limit is 0 (so user sees the form)
            if (!isFirst && batchItems.length >= rateLimit.remaining) {
                showAlert('Cannot add more items than remaining submissions today', 'error');
                return;
            }
            
            const index = batchItems.length;
            batchItems.push({
                name: '', download_link: '', type: 'game', site_name: '', site_url: '',
                file_size: '', description: '', category: '', tags: ''
            });
            
            const container = document.getElementById('batchItemsContainer');
            const itemDiv = document.createElement('div');
            itemDiv.className = 'batch-item';
            itemDiv.id = `batchItem${index}`;
            itemDiv.innerHTML = `
                <div class="batch-item-header">
                    <span class="batch-item-number">ITEM #${index + 1}</span>
                    <button type="button" class="remove-item-btn" onclick="removeBatchItem(${index})" ${batchItems.length <= 1 ? 'disabled' : ''}>REMOVE</button>
                </div>
                
                <div class="form-group">
                    <label>Name *</label>
                    <input type="text" data-field="name" data-index="${index}" required placeholder="e.g., Super Game v1.0">
                </div>
                
                <div class="form-group">
                    <label>Download Link *</label>
                    <input type="url" data-field="download_link" data-index="${index}" required placeholder="https://...">
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Site Name *</label>
                        <input type="text" data-field="site_name" data-index="${index}" required maxlength="15" placeholder="e.g., MySite">
                    </div>
                    <div class="form-group">
                        <label>Site URL *</label>
                        <input type="url" data-field="site_url" data-index="${index}" required placeholder="https://mysite.com">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Type *</label>
                        <select data-field="type" data-index="${index}" onchange="updateCategories(this.value, 'batchCategory${index}')">
                            <option value="game">Game</option>
                            <option value="software">Software</option>
                            <option value="movie">Movie</option>
                            <option value="tv_show">TV Show</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select data-field="category" data-index="${index}" id="batchCategory${index}">
                            <option value="">Select category...</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>File Size</label>
                        <input type="text" data-field="file_size" data-index="${index}" placeholder="e.g., 5.2 GB">
                    </div>
                    <div class="form-group">
                        <label>Tags</label>
                        <input type="text" data-field="tags" data-index="${index}" placeholder="action, HD">
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Description</label>
                    <textarea data-field="description" data-index="${index}" placeholder="Brief description..."></textarea>
                </div>
            `;
            container.appendChild(itemDiv);
            
            // Update batch info
            updateBatchInfo();
            updateCategories('game', `batchCategory${index}`);
        }
        
        function removeBatchItem(index) {
            if (batchItems.length <= 1) return;
            
            batchItems.splice(index, 1);
            
            // Rebuild the container
            const container = document.getElementById('batchItemsContainer');
            container.innerHTML = '';
            const items = [...batchItems];
            batchItems = [];
            items.forEach(() => addBatchItem());
        }
        
        function updateBatchInfo() {
            const remaining = rateLimit.remaining - batchItems.length;
            document.getElementById('addItemBtn').disabled = batchItems.length >= rateLimit.remaining;
            
            // Update remove buttons
            document.querySelectorAll('.remove-item-btn').forEach(btn => {
                btn.disabled = batchItems.length <= 1;
            });
        }
        
        function getBatchData() {
            const items = [];
            for (let i = 0; i < batchItems.length; i++) {
                const item = {};
                document.querySelectorAll(`[data-index="${i}"]`).forEach(el => {
                    const field = el.dataset.field;
                    let value = el.value;
                    if (field === 'tags' && value) {
                        value = value.split(',').map(t => t.trim()).filter(t => t);
                    }
                    item[field] = value;
                });
                items.push(item);
            }
            return items;
        }
        
        async function handleSingleSubmit(e) {
            e.preventDefault();
            
            if (rateLimit.remaining <= 0) {
                showAlert('Daily submission limit reached', 'error');
                return;
            }
            
            const form = e.target;
            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => {
                if (key === 'tags' && value) {
                    data[key] = value.split(',').map(t => t.trim()).filter(t => t);
                } else {
                    data[key] = value;
                }
            });
            
            // Validate
            if (!data.name || !data.download_link || !data.type || !data.site_name || !data.site_url) {
                showAlert('Please fill in all required fields', 'error');
                return;
            }
            
            if (!data.captcha_answer) {
                showAlert('Please solve the captcha', 'error');
                return;
            }
            
            data.captcha_answer = parseInt(data.captcha_answer);
            
            document.getElementById('singleSubmitBtn').disabled = true;
            document.getElementById('singleSubmitBtn').textContent = 'SUBMITTING...';
            
            try {
                const response = await fetch(`${API}/submissions.php?action=create`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.error) {
                    showAlert(result.error, 'error');
                    refreshCaptcha('single');
                } else {
                    showAlert('Submission received! It will be reviewed by an admin.', 'success');
                    form.reset();
                    refreshCaptcha('single');
                    updateRateLimit();
                    setTimeout(() => { window.location.href = 'index.php'; }, 2000);
                }
            } catch (error) {
                showAlert('Error submitting. Please try again.', 'error');
                refreshCaptcha('single');
            } finally {
                document.getElementById('singleSubmitBtn').disabled = false;
                document.getElementById('singleSubmitBtn').textContent = 'SUBMIT';
            }
        }
        
        async function handleMultiSubmit(e) {
            e.preventDefault();
            
            const items = getBatchData();
            
            if (items.length === 0) {
                showAlert('No items to submit', 'error');
                return;
            }
            
            if (items.length > rateLimit.remaining) {
                showAlert('Too many items for remaining submissions today', 'error');
                return;
            }
            
            // Validate all items
            for (let i = 0; i < items.length; i++) {
                const item = items[i];
                if (!item.name || !item.download_link || !item.site_name || !item.site_url) {
                    showAlert(`Please fill in all required fields for Item #${i + 1}`, 'error');
                    return;
                }
            }
            
            const captchaId = document.getElementById('multiCaptchaId').value;
            const captchaAnswer = document.getElementById('multiCaptchaAnswer').value;
            
            if (!captchaAnswer) {
                showAlert('Please solve the captcha', 'error');
                return;
            }
            
            const payload = {
                items: items,
                submitter_email: document.getElementById('multiSubmitterEmail').value,
                captcha_id: captchaId,
                captcha_answer: parseInt(captchaAnswer)
            };
            
            document.getElementById('multiSubmitBtn').disabled = true;
            document.getElementById('multiSubmitBtn').textContent = 'SUBMITTING...';
            
            try {
                const response = await fetch(`${API}/submissions.php?action=bulk`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                
                if (result.error) {
                    showAlert(result.error, 'error');
                    refreshCaptcha('multi');
                } else {
                    showAlert(`${result.count} item(s) submitted successfully!`, 'success');
                    // Reset
                    document.getElementById('batchItemsContainer').innerHTML = '';
                    batchItems = [];
                    addBatchItem();
                    document.getElementById('multiSubmitterEmail').value = '';
                    document.getElementById('multiCaptchaAnswer').value = '';
                    refreshCaptcha('multi');
                    updateRateLimit();
                    setTimeout(() => { window.location.href = 'index.php'; }, 2000);
                }
            } catch (error) {
                showAlert('Error submitting. Please try again.', 'error');
                refreshCaptcha('multi');
            } finally {
                document.getElementById('multiSubmitBtn').disabled = false;
                document.getElementById('multiSubmitBtn').textContent = 'SUBMIT ALL ITEMS';
            }
        }
        
        async function refreshCaptcha(mode) {
            try {
                const response = await fetch(`${API}/submissions.php?action=captcha`);
                const data = await response.json();
                
                if (mode === 'single') {
                    document.getElementById('singleCaptchaChallenge').textContent = data.challenge;
                    document.getElementById('singleCaptchaId').value = data.id;
                } else {
                    document.getElementById('multiCaptchaChallenge').textContent = data.challenge;
                    document.getElementById('multiCaptchaId').value = data.id;
                }
            } catch (error) {
                console.error('Error refreshing captcha:', error);
            }
        }
        
        async function updateRateLimit() {
            try {
                const response = await fetch(`${API}/submissions.php?action=remaining`);
                const data = await response.json();
                rateLimit = data;
                
                document.getElementById('rateLimitUsed').textContent = data.used;
                document.getElementById('rateLimitRemaining').textContent = data.remaining;
                document.getElementById('rateLimitRemaining').style.color = data.remaining <= 0 ? 'var(--error)' : 'var(--success)';
                
                const bar = document.getElementById('rateLimitBar');
                bar.classList.remove('ok', 'warning', 'error');
                if (data.remaining <= 0) bar.classList.add('error');
                else if (data.remaining <= 3) bar.classList.add('warning');
                else bar.classList.add('ok');
                
                document.getElementById('singleSubmitBtn').disabled = data.remaining <= 0;
                document.getElementById('multiSubmitBtn').disabled = data.remaining <= 0;
                
                updateBatchInfo();
            } catch (error) {
                console.error('Error updating rate limit:', error);
            }
        }
        
        function showAlert(message, type) {
            const container = document.getElementById('alertContainer');
            container.innerHTML = `<div class="alert alert-${type}">${escapeHtml(message)}</div>`;
            setTimeout(() => { container.innerHTML = ''; }, 5000);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Theme toggle
        document.getElementById('themeToggle')?.addEventListener('click', async () => {
            document.body.classList.toggle('light-theme');
            const btn = document.getElementById('themeToggle');
            const newMode = document.body.classList.contains('light-theme') ? 'light' : 'dark';
            btn.textContent = newMode === 'dark' ? '☀ LIGHT' : '☾ DARK';
            
            // Save to server
            try {
                await fetch('api/theme.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: newMode })
                });
            } catch (error) {
                console.error('Failed to save theme:', error);
            }
        });
        });
    </script>
</body>
</html>
