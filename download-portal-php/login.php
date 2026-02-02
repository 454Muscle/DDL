<?php
/**
 * Download Portal - Login Page
 */
require_once __DIR__ . '/includes/functions.php';
require_once __DIR__ . '/includes/captcha.php';
require_once __DIR__ . '/includes/auth.php';

$settings = getSiteSettings();
$theme = getThemeSettings();
$message = '';
$messageType = '';
$mode = $_GET['mode'] ?? 'login'; // login, register

// Generate captcha for registration
$captcha = null;
if ($mode === 'register') {
    $captcha = generateCaptcha();
}

// Check if already logged in
if (isUserLoggedIn()) {
    header('Location: index.php');
    exit;
}

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'] ?? '';
    $password = $_POST['password'] ?? '';
    
    if ($mode === 'register') {
        // Verify captcha
        $captchaId = $_POST['captcha_id'] ?? '';
        $captchaAnswer = $_POST['captcha_answer'] ?? '';
        
        if (!verifyCaptcha($captchaId, $captchaAnswer)) {
            $message = 'Invalid captcha. Please try again.';
            $messageType = 'error';
            $captcha = generateCaptcha();
        } else {
            $result = registerUser($email, $password);
            
            if ($result['success']) {
                loginUser($result['user_id'], $result['email']);
                header('Location: index.php');
                exit;
            } else {
                $message = $result['error'];
                $messageType = 'error';
            }
            $captcha = generateCaptcha();
        }
    } else {
        $result = authenticateUser($email, $password);
        
        if ($result['success']) {
            loginUser($result['user_id'], $result['email']);
            header('Location: index.php');
            exit;
        } else {
            $message = $result['error'];
            $messageType = 'error';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= $mode === 'register' ? 'Register' : 'Login' ?> - <?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="<?= $theme['mode'] === 'light' ? 'light-theme' : '' ?>">
    <header>
        <div class="container">
            <div class="header-content">
                <a href="index.php" class="logo"><?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></a>
                <nav>
                    <a href="index.php">HOME</a>
                    <a href="submit.php">SUBMIT</a>
                    <a href="login.php" class="active">LOGIN</a>
                    <a href="admin/">ADMIN</a>
                    <button class="theme-toggle" id="themeToggle">☾ DARK</button>
                </nav>
            </div>
        </div>
    </header>

    <main>
        <div class="container">
            <div style="max-width: 500px; margin: 0 auto;">
                <h1 class="section-title"><?= $mode === 'register' ? 'REGISTER' : 'LOGIN' ?></h1>
                
                <?php if ($message): ?>
                    <div class="alert alert-<?= $messageType ?>"><?= htmlspecialchars($message) ?></div>
                <?php endif; ?>
                
                <div class="admin-section">
                    <form method="POST" action="?mode=<?= $mode ?>">
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" name="email" required placeholder="your@email.com">
                        </div>
                        
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" name="password" required minlength="6" placeholder="••••••••">
                        </div>
                        
                        <?php if ($mode === 'register' && $captcha): ?>
                            <div class="captcha-section">
                                <label>Solve to verify you're human:</label>
                                <div class="captcha-challenge"><?= htmlspecialchars($captcha['challenge']) ?></div>
                                <input type="hidden" name="captcha_id" value="<?= htmlspecialchars($captcha['id']) ?>">
                                <input type="number" name="captcha_answer" required placeholder="Your answer" class="search-input" style="max-width: 200px;">
                            </div>
                        <?php endif; ?>
                        
                        <button type="submit" class="btn"><?= $mode === 'register' ? 'REGISTER' : 'LOGIN' ?></button>
                    </form>
                    
                    <div class="mt-20 text-center">
                        <?php if ($mode === 'login'): ?>
                            <p>Don't have an account? <a href="?mode=register" style="color: var(--accent);">Register</a></p>
                            <p class="mt-20"><a href="forgot-password.php" style="color: var(--text-muted);">Forgot password?</a></p>
                        <?php else: ?>
                            <p>Already have an account? <a href="?mode=login" style="color: var(--accent);">Login</a></p>
                        <?php endif; ?>
                    </div>
                </div>
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
