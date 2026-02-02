<?php
/**
 * Authentication Functions
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/functions.php';

/**
 * Start session if not started
 */
function initSession() {
    if (session_status() === PHP_SESSION_NONE) {
        session_name(SESSION_NAME);
        session_start();
    }
}

/**
 * Check if user is logged in
 */
function isUserLoggedIn() {
    initSession();
    return isset($_SESSION['user_id']);
}

/**
 * Check if admin is logged in
 */
function isAdminLoggedIn() {
    initSession();
    return isset($_SESSION['admin_auth']) && $_SESSION['admin_auth'] === true;
}

/**
 * Login user
 */
function loginUser($userId, $email) {
    initSession();
    $_SESSION['user_id'] = $userId;
    $_SESSION['user_email'] = $email;
}

/**
 * Login admin
 */
function loginAdmin() {
    initSession();
    $_SESSION['admin_auth'] = true;
}

/**
 * Logout user
 */
function logoutUser() {
    initSession();
    unset($_SESSION['user_id']);
    unset($_SESSION['user_email']);
}

/**
 * Logout admin
 */
function logoutAdmin() {
    initSession();
    unset($_SESSION['admin_auth']);
}

/**
 * Get current user
 */
function getCurrentUser() {
    initSession();
    if (!isset($_SESSION['user_id'])) {
        return null;
    }
    
    $db = getDB();
    $stmt = $db->prepare("SELECT id, email, created_at, is_verified FROM users WHERE id = ?");
    $stmt->execute([$_SESSION['user_id']]);
    return $stmt->fetch();
}

/**
 * Register new user
 */
function registerUser($email, $password) {
    $db = getDB();
    
    // Check if email exists
    $stmt = $db->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->execute([strtolower($email)]);
    if ($stmt->fetch()) {
        return ['success' => false, 'error' => 'Email already registered'];
    }
    
    $id = generateUUID();
    $passwordHash = hashPassword($password);
    
    $stmt = $db->prepare("
        INSERT INTO users (id, email, password_hash, is_verified)
        VALUES (?, ?, ?, 1)
    ");
    $stmt->execute([$id, strtolower($email), $passwordHash]);
    
    return [
        'success' => true,
        'user_id' => $id,
        'email' => strtolower($email)
    ];
}

/**
 * Authenticate user
 */
function authenticateUser($email, $password) {
    $db = getDB();
    
    $stmt = $db->prepare("SELECT * FROM users WHERE email = ?");
    $stmt->execute([strtolower($email)]);
    $user = $stmt->fetch();
    
    if (!$user) {
        return ['success' => false, 'error' => 'Invalid email or password'];
    }
    
    if (!verifyPassword($password, $user['password_hash'])) {
        return ['success' => false, 'error' => 'Invalid email or password'];
    }
    
    return [
        'success' => true,
        'user_id' => $user['id'],
        'email' => $user['email']
    ];
}

/**
 * Authenticate admin
 */
function authenticateAdmin($password) {
    $settings = getSiteSettings();
    
    // Check DB password first
    if (!empty($settings['admin_password_hash'])) {
        if (verifyPassword($password, $settings['admin_password_hash'])) {
            return ['success' => true];
        }
    }
    
    // Fallback to config password
    if ($password === ADMIN_PASSWORD) {
        return ['success' => true];
    }
    
    return ['success' => false, 'error' => 'Invalid password'];
}

/**
 * Initialize admin (first-time setup)
 */
function initializeAdmin($email, $password) {
    $settings = getSiteSettings();
    
    if (!empty($settings['admin_password_hash'])) {
        return ['success' => false, 'error' => 'Admin is already initialized'];
    }
    
    updateSiteSettings([
        'admin_email' => strtolower($email),
        'admin_password_hash' => hashPassword($password)
    ]);
    
    return ['success' => true];
}

/**
 * Create password reset token
 */
function createPasswordResetToken($type, $userId = null, $newPasswordHash = null) {
    $db = getDB();
    $token = generateToken();
    $expiresAt = date('Y-m-d H:i:s', strtotime('+30 minutes'));
    
    if ($type === 'admin') {
        $stmt = $db->prepare("
            INSERT INTO admin_password_resets (token, new_password_hash, expires_at, type)
            VALUES (?, ?, ?, ?)
        ");
        $stmt->execute([$token, $newPasswordHash, $expiresAt, 'change']);
    } else {
        $stmt = $db->prepare("
            INSERT INTO user_password_resets (token, user_id, expires_at)
            VALUES (?, ?, ?)
        ");
        $stmt->execute([$token, $userId, $expiresAt]);
    }
    
    return $token;
}

/**
 * Verify and use password reset token
 */
function verifyPasswordResetToken($token, $type) {
    $db = getDB();
    
    if ($type === 'admin') {
        $stmt = $db->prepare("SELECT * FROM admin_password_resets WHERE token = ? AND expires_at > NOW()");
        $stmt->execute([$token]);
        $reset = $stmt->fetch();
        
        if (!$reset) {
            return ['valid' => false, 'error' => 'Invalid or expired token'];
        }
        
        // Delete token
        $stmt = $db->prepare("DELETE FROM admin_password_resets WHERE token = ?");
        $stmt->execute([$token]);
        
        return ['valid' => true, 'data' => $reset];
    } else {
        $stmt = $db->prepare("SELECT * FROM user_password_resets WHERE token = ? AND expires_at > NOW()");
        $stmt->execute([$token]);
        $reset = $stmt->fetch();
        
        if (!$reset) {
            return ['valid' => false, 'error' => 'Invalid or expired token'];
        }
        
        // Delete token
        $stmt = $db->prepare("DELETE FROM user_password_resets WHERE token = ?");
        $stmt->execute([$token]);
        
        return ['valid' => true, 'data' => $reset];
    }
}
