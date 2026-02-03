<?php
/**
 * Helper Functions
 */

require_once __DIR__ . '/../config/database.php';

/**
 * Get site settings
 */
function getSiteSettings() {
    $db = getDB();
    $stmt = $db->query("SELECT * FROM site_settings WHERE id = 'site_settings'");
    $settings = $stmt->fetch();
    
    if (!$settings) {
        // Create default settings
        $db->exec("INSERT INTO site_settings (id) VALUES ('site_settings')");
        $stmt = $db->query("SELECT * FROM site_settings WHERE id = 'site_settings'");
        $settings = $stmt->fetch();
    }
    
    // Parse JSON fields
    if (isset($settings['sponsored_downloads'])) {
        $settings['sponsored_downloads'] = json_decode($settings['sponsored_downloads'], true) ?? [];
    } else {
        $settings['sponsored_downloads'] = [];
    }
    
    return $settings;
}

/**
 * Update site settings
 */
function updateSiteSettings($data) {
    $db = getDB();
    $settings = getSiteSettings();
    
    $allowedFields = [
        'daily_submission_limit', 'top_downloads_enabled', 'top_downloads_count',
        'sponsored_downloads', 'trending_downloads_enabled', 'trending_downloads_count',
        'site_name', 'site_name_font_family', 'site_name_font_weight', 'site_name_font_color',
        'body_font_family', 'body_font_weight', 'footer_enabled', 'footer_line1_template',
        'footer_line2_template', 'auto_approve_submissions', 'recaptcha_site_key',
        'recaptcha_secret_key', 'recaptcha_enable_submit', 'recaptcha_enable_auth',
        'resend_api_key', 'resend_sender_email', 'admin_email', 'admin_password_hash'
    ];
    
    $updates = [];
    $params = [];
    
    foreach ($allowedFields as $field) {
        if (isset($data[$field])) {
            $value = $data[$field];
            if ($field === 'sponsored_downloads' && is_array($value)) {
                $value = json_encode($value);
            }
            $updates[] = "$field = ?";
            $params[] = $value;
        }
    }
    
    if (!empty($updates)) {
        $sql = "UPDATE site_settings SET " . implode(', ', $updates) . " WHERE id = 'site_settings'";
        $stmt = $db->prepare($sql);
        $stmt->execute($params);
    }
    
    return getSiteSettings();
}

/**
 * Get theme settings
 */
function getThemeSettings() {
    $db = getDB();
    $stmt = $db->query("SELECT * FROM theme_settings WHERE id = 'global_theme'");
    $theme = $stmt->fetch();
    
    if (!$theme) {
        $db->exec("INSERT INTO theme_settings (id) VALUES ('global_theme')");
        $stmt = $db->query("SELECT * FROM theme_settings WHERE id = 'global_theme'");
        $theme = $stmt->fetch();
    }
    
    return $theme;
}

/**
 * Update theme settings
 */
function updateThemeSettings($data) {
    $db = getDB();
    $updates = [];
    $params = [];
    
    if (isset($data['mode']) && in_array($data['mode'], ['dark', 'light'])) {
        $updates[] = "mode = ?";
        $params[] = $data['mode'];
    }
    
    if (isset($data['accent_color'])) {
        $updates[] = "accent_color = ?";
        $params[] = $data['accent_color'];
    }
    
    if (!empty($updates)) {
        $sql = "UPDATE theme_settings SET " . implode(', ', $updates) . " WHERE id = 'global_theme'";
        $stmt = $db->prepare($sql);
        $stmt->execute($params);
    }
    
    return getThemeSettings();
}

/**
 * Parse file size string to bytes
 */
function parseFileSizeToBytes($sizeStr) {
    if (empty($sizeStr)) return null;
    
    $sizeStr = strtoupper(trim($sizeStr));
    
    if (preg_match('/^([\d.]+)\s*GB$/i', $sizeStr, $matches)) {
        return (int)($matches[1] * 1024 * 1024 * 1024);
    } elseif (preg_match('/^([\d.]+)\s*MB$/i', $sizeStr, $matches)) {
        return (int)($matches[1] * 1024 * 1024);
    } elseif (preg_match('/^([\d.]+)\s*KB$/i', $sizeStr, $matches)) {
        return (int)($matches[1] * 1024);
    } elseif (preg_match('/^([\d.]+)\s*B$/i', $sizeStr, $matches)) {
        return (int)$matches[1];
    }
    
    return (int)($sizeStr * 1024 * 1024); // Assume MB
}

/**
 * Format download count
 */
function formatDownloadCount($count) {
    if ($count >= 1000000) {
        return round($count / 1000000, 1) . 'M';
    } elseif ($count >= 1000) {
        return round($count / 1000, 1) . 'K';
    }
    return $count;
}

/**
 * Validate URL
 */
function validateHttpUrl($url) {
    if (empty($url)) {
        return ['valid' => false, 'error' => 'URL is required'];
    }
    
    $url = trim($url);
    if (!preg_match('/^https?:\/\//i', $url)) {
        return ['valid' => false, 'error' => 'URL must start with http:// or https://'];
    }
    
    return ['valid' => true, 'url' => $url];
}

/**
 * Hash password
 */
function hashPassword($password) {
    return password_hash($password, PASSWORD_DEFAULT);
}

/**
 * Verify password
 */
function verifyPassword($password, $hash) {
    // Support both new bcrypt and legacy sha256 hashes
    if (password_verify($password, $hash)) {
        return true;
    }
    // Legacy sha256 support
    if (hash('sha256', $password) === $hash) {
        return true;
    }
    return false;
}

/**
 * Generate secure token
 */
function generateToken($length = 32) {
    return bin2hex(random_bytes($length));
}

/**
 * Sanitize input
 */
function sanitize($input) {
    if (is_array($input)) {
        return array_map('sanitize', $input);
    }
    return htmlspecialchars(trim($input), ENT_QUOTES, 'UTF-8');
}

/**
 * Get JSON input
 */
function getJsonInput() {
    $input = file_get_contents('php://input');
    return json_decode($input, true) ?? [];
}

/**
 * Check rate limit
 */
function checkRateLimit($ip, $limit) {
    $db = getDB();
    $today = date('Y-m-d');
    
    $stmt = $db->prepare("SELECT count FROM rate_limits WHERE ip_address = ? AND date = ?");
    $stmt->execute([$ip, $today]);
    $row = $stmt->fetch();
    
    $count = $row ? $row['count'] : 0;
    
    return [
        'allowed' => $count < $limit,
        'used' => $count,
        'remaining' => max(0, $limit - $count)
    ];
}

/**
 * Increment rate limit
 */
function incrementRateLimit($ip, $increment = 1) {
    $db = getDB();
    $today = date('Y-m-d');
    
    $stmt = $db->prepare("
        INSERT INTO rate_limits (ip_address, date, count) VALUES (?, ?, ?)
        ON DUPLICATE KEY UPDATE count = count + ?
    ");
    $stmt->execute([$ip, $today, $increment, $increment]);
}

/**
 * Clean expired captchas
 */
function cleanExpiredCaptchas() {
    $db = getDB();
    $db->exec("DELETE FROM captchas WHERE expires_at < NOW()");
}

/**
 * Parse tags from JSON or comma-separated string
 */
function parseTags($tags) {
    if (is_array($tags)) {
        return $tags;
    }
    if (is_string($tags)) {
        $decoded = json_decode($tags, true);
        if (is_array($decoded)) {
            return $decoded;
        }
        return array_filter(array_map('trim', explode(',', $tags)));
    }
    return [];
}

/**
 * Generate UUID v4
 */
function generateUUID() {
    $data = random_bytes(16);
    $data[6] = chr(ord($data[6]) & 0x0f | 0x40); // Version 4
    $data[8] = chr(ord($data[8]) & 0x3f | 0x80); // Variant RFC 4122
    return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
}

/**
 * Get client IP address
 */
function getClientIP() {
    if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $ips = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
        return trim($ips[0]);
    }
    if (!empty($_SERVER['HTTP_X_REAL_IP'])) {
        return $_SERVER['HTTP_X_REAL_IP'];
    }
    return $_SERVER['REMOTE_ADDR'] ?? 'anonymous';
}

/**
 * Verify captcha or reCAPTCHA
 */
function verifyCaptchaOrRecaptcha($data, $settings, $context = 'submit') {
    $enableKey = $context === 'submit' ? 'recaptcha_enable_submit' : 'recaptcha_enable_auth';
    
    if (!empty($settings[$enableKey])) {
        // reCAPTCHA enabled
        if (empty($settings['recaptcha_site_key']) || empty($settings['recaptcha_secret_key'])) {
            return ['valid' => false, 'error' => 'reCAPTCHA is enabled but not configured'];
        }
        
        $token = $data['recaptcha_token'] ?? '';
        if (empty($token)) {
            return ['valid' => false, 'error' => 'reCAPTCHA token is required'];
        }
        
        // Verify with Google
        $url = 'https://www.google.com/recaptcha/api/siteverify';
        $postData = [
            'secret' => $settings['recaptcha_secret_key'],
            'response' => $token,
            'remoteip' => getClientIP()
        ];
        
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($postData));
        $response = curl_exec($ch);
        curl_close($ch);
        
        $result = json_decode($response, true);
        if (!$result || empty($result['success'])) {
            return ['valid' => false, 'error' => 'Invalid reCAPTCHA. Please try again.'];
        }
        
        return ['valid' => true];
    } else {
        // Simple captcha
        $captchaId = $data['captcha_id'] ?? '';
        $captchaAnswer = $data['captcha_answer'] ?? null;
        
        if (empty($captchaId) || $captchaAnswer === null) {
            return ['valid' => false, 'error' => 'Captcha is required'];
        }
        
        if (!verifyCaptcha($captchaId, $captchaAnswer)) {
            return ['valid' => false, 'error' => 'Invalid captcha. Please try again.'];
        }
        
        return ['valid' => true];
    }
}
