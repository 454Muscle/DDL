<?php
/**
 * Authentication API
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';
require_once __DIR__ . '/../includes/captcha.php';
require_once __DIR__ . '/../includes/auth.php';
require_once __DIR__ . '/../includes/email.php';

setCorsHeaders();
header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

switch ($action) {
    case 'register':
        handleRegister();
        break;
    case 'login':
        handleLogin();
        break;
    case 'logout':
        handleLogout();
        break;
    case 'user':
        handleGetUser();
        break;
    case 'forgot-password':
        handleForgotPassword();
        break;
    case 'reset-password':
        handleResetPassword();
        break;
    default:
        jsonResponse(['error' => 'Invalid action'], 400);
}

function handleRegister() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    $settings = getSiteSettings();
    
    // Verify captcha
    $captchaResult = verifyCaptchaOrRecaptcha($data, $settings, 'auth');
    if (!$captchaResult['valid']) {
        jsonResponse(['error' => $captchaResult['error']], 400);
    }
    
    // Validate input
    if (empty($data['email']) || empty($data['password'])) {
        jsonResponse(['error' => 'Email and password are required'], 400);
    }
    
    if (!filter_var($data['email'], FILTER_VALIDATE_EMAIL)) {
        jsonResponse(['error' => 'Invalid email format'], 400);
    }
    
    if (strlen($data['password']) < 6) {
        jsonResponse(['error' => 'Password must be at least 6 characters'], 400);
    }
    
    $result = registerUser($data['email'], $data['password']);
    
    if (!$result['success']) {
        jsonResponse(['error' => $result['error']], 400);
    }
    
    // Auto-login after registration
    loginUser($result['user_id'], $result['email']);
    
    jsonResponse([
        'success' => true,
        'message' => 'Registration successful',
        'user_id' => $result['user_id'],
        'email' => $result['email']
    ]);
}

function handleLogin() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    $settings = getSiteSettings();
    
    // Verify reCAPTCHA if enabled
    if ($settings['recaptcha_enable_auth']) {
        $captchaResult = verifyCaptchaOrRecaptcha($data, $settings, 'auth');
        if (!$captchaResult['valid']) {
            jsonResponse(['error' => $captchaResult['error']], 400);
        }
    }
    
    // Validate input
    if (empty($data['email']) || empty($data['password'])) {
        jsonResponse(['error' => 'Email and password are required'], 400);
    }
    
    $result = authenticateUser($data['email'], $data['password']);
    
    if (!$result['success']) {
        jsonResponse(['error' => $result['error']], 401);
    }
    
    loginUser($result['user_id'], $result['email']);
    
    jsonResponse([
        'success' => true,
        'user_id' => $result['user_id'],
        'email' => $result['email']
    ]);
}

function handleLogout() {
    logoutUser();
    jsonResponse(['success' => true]);
}

function handleGetUser() {
    $userId = $_GET['id'] ?? '';
    
    if (empty($userId)) {
        // Get current user
        $user = getCurrentUser();
        if (!$user) {
            jsonResponse(['error' => 'Not logged in'], 401);
        }
        jsonResponse($user);
    }
    
    $db = getDB();
    $stmt = $db->prepare("SELECT id, email, created_at, is_verified FROM users WHERE id = ?");
    $stmt->execute([$userId]);
    $user = $stmt->fetch();
    
    if (!$user) {
        jsonResponse(['error' => 'User not found'], 404);
    }
    
    jsonResponse($user);
}

function handleForgotPassword() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    
    if (empty($data['email'])) {
        jsonResponse(['error' => 'Email is required'], 400);
    }
    
    $db = getDB();
    $stmt = $db->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->execute([strtolower($data['email'])]);
    $user = $stmt->fetch();
    
    // Always return success (don't reveal if email exists)
    if (!$user) {
        jsonResponse(['success' => true]);
    }
    
    $token = createPasswordResetToken('user', $user['id']);
    $resetLink = SITE_URL . "/reset-password.php?token=$token";
    
    sendPasswordResetEmail($data['email'], $resetLink, 'user');
    
    jsonResponse(['success' => true]);
}

function handleResetPassword() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    
    if (empty($data['token']) || empty($data['new_password'])) {
        jsonResponse(['error' => 'Token and new password are required'], 400);
    }
    
    $result = verifyPasswordResetToken($data['token'], 'user');
    
    if (!$result['valid']) {
        jsonResponse(['error' => $result['error']], 400);
    }
    
    // Update password
    $db = getDB();
    $stmt = $db->prepare("UPDATE users SET password_hash = ? WHERE id = ?");
    $stmt->execute([hashPassword($data['new_password']), $result['data']['user_id']]);
    
    jsonResponse(['success' => true]);
}
