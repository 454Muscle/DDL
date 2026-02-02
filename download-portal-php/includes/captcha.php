<?php
/**
 * Captcha Functions
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/functions.php';

/**
 * Generate math captcha
 */
function generateCaptcha() {
    cleanExpiredCaptchas();
    
    $db = getDB();
    
    $num1 = rand(1, 20);
    $num2 = rand(1, 20);
    
    $operators = [
        ['+', $num1 + $num2],
        ['-', abs($num1 - $num2)],
        ['×', ($num1 < 10 && $num2 < 10) ? $num1 * $num2 : $num1 + $num2]
    ];
    
    $selected = $operators[array_rand($operators)];
    $operator = $selected[0];
    $answer = $selected[1];
    
    // Make subtraction always positive
    if ($operator === '-' && $num1 < $num2) {
        list($num1, $num2) = [$num2, $num1];
        $answer = $num1 - $num2;
    }
    
    $id = generateUUID();
    $expiresAt = date('Y-m-d H:i:s', strtotime('+5 minutes'));
    
    $stmt = $db->prepare("
        INSERT INTO captchas (id, num1, num2, operator, answer, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([$id, $num1, $num2, $operator, $answer, $expiresAt]);
    
    return [
        'id' => $id,
        'challenge' => "$num1 $operator $num2 = ?",
        'expires_at' => $expiresAt
    ];
}

/**
 * Verify math captcha
 */
function verifyCaptcha($captchaId, $answer) {
    if (empty($captchaId) || !is_numeric($answer)) {
        return false;
    }
    
    $db = getDB();
    
    $stmt = $db->prepare("SELECT * FROM captchas WHERE id = ? AND expires_at > NOW()");
    $stmt->execute([$captchaId]);
    $captcha = $stmt->fetch();
    
    if (!$captcha) {
        return false;
    }
    
    // Delete the captcha (one-time use)
    $stmt = $db->prepare("DELETE FROM captchas WHERE id = ?");
    $stmt->execute([$captchaId]);
    
    return (int)$answer === (int)$captcha['answer'];
}

/**
 * Verify Google reCAPTCHA v2
 */
function verifyRecaptcha($token, $secretKey) {
    if (empty($token) || empty($secretKey)) {
        return false;
    }
    
    $url = 'https://www.google.com/recaptcha/api/siteverify';
    $data = [
        'secret' => $secretKey,
        'response' => $token,
        'remoteip' => getClientIP()
    ];
    
    $options = [
        'http' => [
            'header' => "Content-type: application/x-www-form-urlencoded\r\n",
            'method' => 'POST',
            'content' => http_build_query($data)
        ]
    ];
    
    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    
    if ($result === false) {
        return false;
    }
    
    $response = json_decode($result, true);
    return $response['success'] ?? false;
}

/**
 * Verify captcha based on settings
 */
function verifyCaptchaOrRecaptcha($data, $settings, $type = 'submit') {
    $enableKey = ($type === 'auth') ? 'recaptcha_enable_auth' : 'recaptcha_enable_submit';
    
    if ($settings[$enableKey]) {
        // reCAPTCHA enabled
        if (empty($settings['recaptcha_site_key']) || empty($settings['recaptcha_secret_key'])) {
            return ['valid' => false, 'error' => 'reCAPTCHA is enabled but not configured'];
        }
        
        $token = $data['recaptcha_token'] ?? '';
        if (!verifyRecaptcha($token, $settings['recaptcha_secret_key'])) {
            return ['valid' => false, 'error' => 'Invalid reCAPTCHA. Please try again.'];
        }
    } else {
        // Math captcha
        $captchaId = $data['captcha_id'] ?? '';
        $captchaAnswer = $data['captcha_answer'] ?? '';
        
        if (!verifyCaptcha($captchaId, $captchaAnswer)) {
            return ['valid' => false, 'error' => 'Invalid captcha. Please try again.'];
        }
    }
    
    return ['valid' => true];
}
