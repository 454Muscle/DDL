<?php
/**
 * Download Portal - Submit Page
 */
require_once __DIR__ . '/includes/functions.php';
require_once __DIR__ . '/includes/captcha.php';

$settings = getSiteSettings();
$theme = getThemeSettings();
$captcha = generateCaptcha();
$message = '';
$messageType = '';

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = [
        'name' => $_POST['name'] ?? '',
        'download_link' => $_POST['download_link'] ?? '',
        'type' => $_POST['type'] ?? '',
        'site_name' => $_POST['site_name'] ?? '',
        'site_url' => $_POST['site_url'] ?? '',
        'file_size' => $_POST['file_size'] ?? '',
        'description' => $_POST['description'] ?? '',
        'category' => $_POST['category'] ?? '',
        'tags' => $_POST['tags'] ?? '',
        'submitter_email' => $_POST['submitter_email'] ?? '',
        'captcha_id' => $_POST['captcha_id'] ?? '',
        'captcha_answer' => $_POST['captcha_answer'] ?? ''
    ];
    
    // Verify captcha
    if (!verifyCaptcha($data['captcha_id'], $data['captcha_answer'])) {
        $message = 'Invalid captcha. Please try again.';
        $messageType = 'error';
        $captcha = generateCaptcha();
    } else {
        // Check rate limit
        $ip = getClientIP();
        $dailyLimit = $settings['daily_submission_limit'] ?? 10;
        $rateLimit = checkRateLimit($ip, $dailyLimit);
        
        if (!$rateLimit['allowed']) {
            $message = "Daily submission limit ($dailyLimit) reached. Try again tomorrow.";
            $messageType = 'error';
        } else {
            // Validate URL
            $urlResult = validateHttpUrl($data['site_url']);
            if (!$urlResult['valid']) {
                $message = $urlResult['error'];
                $messageType = 'error';
            } else {
                // Create submission
                $db = getDB();
                $id = generateUUID();
                $today = date('Y-m-d');
                $fileSizeBytes = parseFileSizeToBytes($data['file_size']);
                $tags = json_encode(array_filter(array_map('trim', explode(',', $data['tags']))));
                
                $stmt = $db->prepare("
                    INSERT INTO submissions (
                        id, name, download_link, type, submission_date, file_size, file_size_bytes,
                        description, category, tags, site_name, site_url, submitter_email
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ");
                $stmt->execute([
                    $id, $data['name'], $data['download_link'], $data['type'], $today,
                    $data['file_size'], $fileSizeBytes, $data['description'], $data['category'],
                    $tags, $data['site_name'], $urlResult['url'], $data['submitter_email']
                ]);
                
                incrementRateLimit($ip);
                
                $message = 'Submission received! It will be reviewed by an admin.';
                $messageType = 'success';
                
                // Reset form
                $data = [];
            }
        }
        
        $captcha = generateCaptcha();
    }
}

// Get categories
$db = getDB();
$categories = $db->query("SELECT DISTINCT name FROM categories ORDER BY name")->fetchAll(PDO::FETCH_COLUMN);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submit - <?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="<?= $theme['mode'] === 'light' ? 'light-theme' : '' ?>">
    <header>
        <div class="container">
            <div class="header-content">
                <a href="index.php" class="logo"><?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></a>
                <nav>
                    <a href="index.php">HOME</a>
                    <a href="submit.php" class="active">SUBMIT</a>
                    <a href="login.php">LOGIN</a>
                    <a href="admin/">ADMIN</a>
                    <button class="theme-toggle" id="themeToggle">☾ DARK</button>
                </nav>
            </div>
        </div>
    </header>

    <main>
        <div class="container">
            <h1 class="section-title">SUBMIT NEW DOWNLOAD</h1>
            
            <?php if ($message): ?>
                <div class="alert alert-<?= $messageType ?>"><?= htmlspecialchars($message) ?></div>
            <?php endif; ?>
            
            <div class="admin-section">
                <form method="POST" action="">
                    <div class="form-group">
                        <label>Name *</label>
                        <input type="text" name="name" required value="<?= htmlspecialchars($data['name'] ?? '') ?>" placeholder="e.g., Super Game v1.0">
                    </div>
                    
                    <div class="form-group">
                        <label>Download Link *</label>
                        <input type="url" name="download_link" required value="<?= htmlspecialchars($data['download_link'] ?? '') ?>" placeholder="https://...">
                    </div>
                    
                    <div class="form-group">
                        <label>Type *</label>
                        <select name="type" required>
                            <option value="">Select type...</option>
                            <option value="game" <?= ($data['type'] ?? '') === 'game' ? 'selected' : '' ?>>Game</option>
                            <option value="software" <?= ($data['type'] ?? '') === 'software' ? 'selected' : '' ?>>Software</option>
                            <option value="movie" <?= ($data['type'] ?? '') === 'movie' ? 'selected' : '' ?>>Movie</option>
                            <option value="tv_show" <?= ($data['type'] ?? '') === 'tv_show' ? 'selected' : '' ?>>TV Show</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Site Name * (max 15 chars)</label>
                        <input type="text" name="site_name" required maxlength="15" value="<?= htmlspecialchars($data['site_name'] ?? '') ?>" placeholder="e.g., MySite">
                    </div>
                    
                    <div class="form-group">
                        <label>Site URL *</label>
                        <input type="url" name="site_url" required value="<?= htmlspecialchars($data['site_url'] ?? '') ?>" placeholder="https://mysite.com">
                    </div>
                    
                    <div class="form-group">
                        <label>File Size</label>
                        <input type="text" name="file_size" value="<?= htmlspecialchars($data['file_size'] ?? '') ?>" placeholder="e.g., 5.2 GB">
                    </div>
                    
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category">
                            <option value="">Select category...</option>
                            <?php foreach ($categories as $cat): ?>
                                <option value="<?= htmlspecialchars($cat) ?>" <?= ($data['category'] ?? '') === $cat ? 'selected' : '' ?>><?= htmlspecialchars($cat) ?></option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Tags (comma separated)</label>
                        <input type="text" name="tags" value="<?= htmlspecialchars($data['tags'] ?? '') ?>" placeholder="e.g., action, multiplayer, HD">
                    </div>
                    
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" placeholder="Brief description..."><?= htmlspecialchars($data['description'] ?? '') ?></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Your Email (for notifications)</label>
                        <input type="email" name="submitter_email" value="<?= htmlspecialchars($data['submitter_email'] ?? '') ?>" placeholder="your@email.com">
                    </div>
                    
                    <!-- Captcha -->
                    <div class="captcha-section">
                        <label>Solve to verify you're human:</label>
                        <div class="captcha-challenge"><?= htmlspecialchars($captcha['challenge']) ?></div>
                        <input type="hidden" name="captcha_id" value="<?= htmlspecialchars($captcha['id']) ?>">
                        <input type="number" name="captcha_answer" required placeholder="Your answer" class="search-input" style="max-width: 200px;">
                    </div>
                    
                    <button type="submit" class="btn">SUBMIT</button>
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
        document.getElementById('themeToggle')?.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            const btn = document.getElementById('themeToggle');
            btn.textContent = document.body.classList.contains('light-theme') ? '☀ LIGHT' : '☾ DARK';
        });
    </script>
</body>
</html>
