<?php
/**
 * Admin API
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';
require_once __DIR__ . '/../includes/auth.php';
require_once __DIR__ . '/../includes/email.php';

setCorsHeaders();
header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

// Public actions (no auth required)
$publicActions = ['login', 'init', 'forgot-password', 'reset-password'];

if (!in_array($action, $publicActions)) {
    // Verify admin is logged in (for API calls, check session or password in request)
    initSession();
    if (!isAdminLoggedIn()) {
        // Allow if password is provided in request
        $data = getJsonInput();
        if (empty($data['admin_password'])) {
            // Check if Authorization header is present
            $headers = getallheaders();
            if (empty($headers['Authorization']) && empty($headers['authorization'])) {
                // For GET requests, allow if session exists
                if ($method !== 'GET' || !isset($_SESSION['admin_auth'])) {
                    // Allow GET requests for certain actions
                    $allowedGetActions = ['submissions', 'downloads', 'sponsored-analytics', 'unseen-count'];
                    if (!in_array($action, $allowedGetActions)) {
                        jsonResponse(['error' => 'Admin authentication required'], 401);
                    }
                }
            }
        }
    }
}

switch ($action) {
    case 'login':
        handleLogin();
        break;
    case 'init':
        handleInit();
        break;
    case 'forgot-password':
        handleForgotPassword();
        break;
    case 'reset-password':
        handleResetPassword();
        break;
    case 'password-change-request':
        handlePasswordChangeRequest();
        break;
    case 'password-change-confirm':
        handlePasswordChangeConfirm();
        break;
    case 'change-password':
        handleChangePassword();
        break;
    case 'email-update':
        handleEmailUpdate();
        break;
    case 'submissions':
        handleSubmissions();
        break;
    case 'approve':
        handleApprove();
        break;
    case 'reject':
        handleReject();
        break;
    case 'delete-submission':
        handleDeleteSubmission();
        break;
    case 'unseen-count':
        handleUnseenCount();
        break;
    case 'downloads':
        handleDownloads();
        break;
    case 'search-downloads':
        handleSearchDownloads();
        break;
    case 'delete-download':
        handleDeleteDownload();
        break;
    case 'sponsored-analytics':
        handleSponsoredAnalytics();
        break;
    case 'sponsored-click':
        handleSponsoredClick();
        break;
    case 'categories':
        handleCategories();
        break;
    case 'resend-test':
        handleResendTest();
        break;
    case 'test-email':
        handleResendTest();
        break;
    case 'resend-settings':
        handleResendSettings();
        break;
    case 'seed':
        handleSeed();
        break;
    default:
        jsonResponse(['error' => 'Invalid action'], 400);
}

function handleLogin() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    
    if (empty($data['password'])) {
        jsonResponse(['error' => 'Password is required'], 400);
    }
    
    $result = authenticateAdmin($data['password']);
    
    if (!$result['success']) {
        jsonResponse(['error' => 'Invalid password'], 401);
    }
    
    loginAdmin();
    
    jsonResponse(['success' => true, 'message' => 'Access granted']);
}

function handleInit() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    
    if (empty($data['email']) || empty($data['password'])) {
        jsonResponse(['error' => 'Email and password are required'], 400);
    }
    
    $result = initializeAdmin($data['email'], $data['password']);
    
    if (!$result['success']) {
        jsonResponse(['error' => $result['error']], 400);
    }
    
    jsonResponse(['success' => true]);
}

function handleForgotPassword() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    $settings = getSiteSettings();
    
    if (empty($settings['admin_email']) || empty($settings['admin_password_hash'])) {
        jsonResponse(['error' => 'Admin is not initialized'], 400);
    }
    
    // Don't reveal if email matches
    if (strtolower($data['email'] ?? '') !== strtolower($settings['admin_email'])) {
        jsonResponse(['success' => true]);
    }
    
    $token = generateToken();
    $db = getDB();
    $expiresAt = date('Y-m-d H:i:s', strtotime('+30 minutes'));
    
    $stmt = $db->prepare("INSERT INTO admin_password_resets (token, expires_at, type) VALUES (?, ?, 'forgot')");
    $stmt->execute([$token, $expiresAt]);
    
    $resetLink = SITE_URL . "/admin/reset-password.php?token=$token";
    sendPasswordResetEmail($settings['admin_email'], $resetLink, 'admin');
    
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
    
    $result = verifyPasswordResetToken($data['token'], 'admin');
    
    if (!$result['valid']) {
        jsonResponse(['error' => $result['error']], 400);
    }
    
    updateSiteSettings(['admin_password_hash' => hashPassword($data['new_password'])]);
    
    jsonResponse(['success' => true]);
}

function handlePasswordChangeRequest() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    $settings = getSiteSettings();
    
    if (empty($settings['admin_email'])) {
        jsonResponse(['error' => 'Admin email is not configured'], 400);
    }
    
    // Verify current password
    $authResult = authenticateAdmin($data['current_password'] ?? '');
    if (!$authResult['success']) {
        jsonResponse(['error' => 'Invalid current password'], 401);
    }
    
    $token = generateToken();
    $newPasswordHash = hashPassword($data['new_password']);
    $db = getDB();
    $expiresAt = date('Y-m-d H:i:s', strtotime('+30 minutes'));
    
    $stmt = $db->prepare("INSERT INTO admin_password_resets (token, new_password_hash, expires_at, type) VALUES (?, ?, ?, 'change')");
    $stmt->execute([$token, $newPasswordHash, $expiresAt]);
    
    $confirmLink = SITE_URL . "/admin/confirm-password-change.php?token=$token";
    
    $html = "
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>Confirm Admin Password Change</h2>
      <p>Click the link below to confirm your admin password change. This link expires in 30 minutes.</p>
      <p><a href='$confirmLink'>Confirm password change</a></p>
    </body></html>";
    
    $sent = sendEmail($settings['admin_email'], "Confirm admin password change", $html);
    
    if (!$sent) {
        jsonResponse(['error' => 'Failed to send confirmation email'], 500);
    }
    
    jsonResponse(['success' => true]);
}

function handlePasswordChangeConfirm() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    
    if (empty($data['token'])) {
        jsonResponse(['error' => 'Token is required'], 400);
    }
    
    $result = verifyPasswordResetToken($data['token'], 'admin');
    
    if (!$result['valid']) {
        jsonResponse(['error' => $result['error']], 400);
    }
    
    if ($result['data']['type'] !== 'change') {
        jsonResponse(['error' => 'Invalid token'], 400);
    }
    
    updateSiteSettings(['admin_password_hash' => $result['data']['new_password_hash']]);
    
    jsonResponse(['success' => true]);
}

function handleEmailUpdate() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    
    // Verify current password
    $authResult = authenticateAdmin($data['current_password'] ?? '');
    if (!$authResult['success']) {
        jsonResponse(['error' => 'Invalid current password'], 401);
    }
    
    if (empty($data['new_email']) || !filter_var($data['new_email'], FILTER_VALIDATE_EMAIL)) {
        jsonResponse(['error' => 'Valid email is required'], 400);
    }
    
    updateSiteSettings(['admin_email' => strtolower($data['new_email'])]);
    
    jsonResponse(['success' => true]);
}

function handleSubmissions() {
    $db = getDB();
    
    $page = max(1, (int)($_GET['page'] ?? 1));
    $limit = min(100, max(1, (int)($_GET['limit'] ?? 20)));
    $offset = ($page - 1) * $limit;
    $status = $_GET['status'] ?? null;
    
    $where = '1=1';
    $params = [];
    
    if ($status && in_array($status, ['pending', 'approved', 'rejected'])) {
        $where .= ' AND status = ?';
        $params[] = $status;
    }
    
    // Get total
    $stmt = $db->prepare("SELECT COUNT(*) FROM submissions WHERE $where");
    $stmt->execute($params);
    $total = $stmt->fetchColumn();
    
    // Get items
    $params[] = $limit;
    $params[] = $offset;
    $stmt = $db->prepare("SELECT * FROM submissions WHERE $where ORDER BY created_at DESC LIMIT ? OFFSET ?");
    $stmt->execute($params);
    $items = $stmt->fetchAll();
    
    // Parse tags
    foreach ($items as &$item) {
        $item['tags'] = json_decode($item['tags'] ?? '[]', true) ?? [];
    }
    
    // Mark pending as seen
    if (!$status || $status === 'pending') {
        $ids = array_column(array_filter($items, fn($i) => $i['status'] === 'pending'), 'id');
        if (!empty($ids)) {
            $placeholders = implode(',', array_fill(0, count($ids), '?'));
            $stmt = $db->prepare("UPDATE submissions SET seen_by_admin = 1 WHERE id IN ($placeholders)");
            $stmt->execute($ids);
        }
    }
    
    $pages = max(1, ceil($total / $limit));
    
    jsonResponse([
        'items' => $items,
        'total' => (int)$total,
        'page' => $page,
        'pages' => $pages
    ]);
}

function handleUnseenCount() {
    $db = getDB();
    $settings = getSiteSettings();
    
    if ($settings['auto_approve_submissions']) {
        jsonResponse(['count' => 0]);
    }
    
    $stmt = $db->query("SELECT COUNT(*) FROM submissions WHERE status = 'pending'");
    $count = $stmt->fetchColumn();
    
    jsonResponse(['count' => (int)$count]);
}

function handleApprove() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $submissionId = $_GET['id'] ?? '';
    
    if (empty($submissionId)) {
        jsonResponse(['error' => 'Submission ID required'], 400);
    }
    
    // Get submission
    $stmt = $db->prepare("SELECT * FROM submissions WHERE id = ?");
    $stmt->execute([$submissionId]);
    $submission = $stmt->fetch();
    
    if (!$submission) {
        jsonResponse(['error' => 'Submission not found'], 404);
    }
    
    // Create download
    $downloadId = generateUUID();
    $stmt = $db->prepare("
        INSERT INTO downloads (
            id, name, download_link, type, submission_date, approved, download_count,
            file_size, file_size_bytes, description, category, tags, site_name, site_url
        ) VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([
        $downloadId,
        $submission['name'],
        $submission['download_link'],
        $submission['type'],
        $submission['submission_date'],
        $submission['file_size'],
        $submission['file_size_bytes'],
        $submission['description'],
        $submission['category'],
        $submission['tags'],
        $submission['site_name'],
        $submission['site_url']
    ]);
    
    // Update submission status
    $stmt = $db->prepare("UPDATE submissions SET status = 'approved' WHERE id = ?");
    $stmt->execute([$submissionId]);
    
    // Send approval email
    if (!empty($submission['submitter_email'])) {
        $submission['tags'] = json_decode($submission['tags'] ?? '[]', true);
        sendApprovalEmail($submission['submitter_email'], $submission);
    }
    
    jsonResponse(['success' => true, 'message' => 'Submission approved']);
}

function handleReject() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $submissionId = $_GET['id'] ?? '';
    
    if (empty($submissionId)) {
        jsonResponse(['error' => 'Submission ID required'], 400);
    }
    
    $stmt = $db->prepare("UPDATE submissions SET status = 'rejected' WHERE id = ?");
    $stmt->execute([$submissionId]);
    
    if ($stmt->rowCount() === 0) {
        jsonResponse(['error' => 'Submission not found'], 404);
    }
    
    jsonResponse(['success' => true, 'message' => 'Submission rejected']);
}

function handleDeleteSubmission() {
    if ($_SERVER['REQUEST_METHOD'] !== 'DELETE' && $_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $submissionId = $_GET['id'] ?? '';
    
    if (empty($submissionId)) {
        jsonResponse(['error' => 'Submission ID required'], 400);
    }
    
    $stmt = $db->prepare("DELETE FROM submissions WHERE id = ?");
    $stmt->execute([$submissionId]);
    
    if ($stmt->rowCount() === 0) {
        jsonResponse(['error' => 'Submission not found'], 404);
    }
    
    jsonResponse(['success' => true]);
}

function handleDownloads() {
    $db = getDB();
    
    $page = max(1, (int)($_GET['page'] ?? 1));
    $limit = min(100, max(1, (int)($_GET['limit'] ?? 20)));
    $offset = ($page - 1) * $limit;
    $search = $_GET['search'] ?? '';
    
    $where = 'approved = 1';
    $params = [];
    
    if ($search) {
        $where .= ' AND name LIKE ?';
        $params[] = "%$search%";
    }
    
    // Get total
    $stmt = $db->prepare("SELECT COUNT(*) FROM downloads WHERE $where");
    $stmt->execute($params);
    $total = $stmt->fetchColumn();
    
    // Get items
    $params[] = $limit;
    $params[] = $offset;
    $stmt = $db->prepare("SELECT * FROM downloads WHERE $where ORDER BY created_at DESC LIMIT ? OFFSET ?");
    $stmt->execute($params);
    $items = $stmt->fetchAll();
    
    foreach ($items as &$item) {
        $item['tags'] = json_decode($item['tags'] ?? '[]', true) ?? [];
    }
    
    $pages = max(1, ceil($total / $limit));
    
    jsonResponse([
        'items' => $items,
        'total' => (int)$total,
        'page' => $page,
        'pages' => $pages
    ]);
}

function handleDeleteDownload() {
    if ($_SERVER['REQUEST_METHOD'] !== 'DELETE' && $_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $downloadId = $_GET['id'] ?? '';
    
    if (empty($downloadId)) {
        jsonResponse(['error' => 'Download ID required'], 400);
    }
    
    $stmt = $db->prepare("DELETE FROM downloads WHERE id = ?");
    $stmt->execute([$downloadId]);
    
    if ($stmt->rowCount() === 0) {
        jsonResponse(['error' => 'Download not found'], 404);
    }
    
    jsonResponse(['success' => true, 'message' => 'Download deleted']);
}

function handleSponsoredAnalytics() {
    $db = getDB();
    $settings = getSiteSettings();
    $sponsored = $settings['sponsored_downloads'] ?? [];
    
    $analytics = [];
    
    foreach ($sponsored as $item) {
        $itemId = $item['id'] ?? '';
        
        // Total clicks
        $stmt = $db->prepare("SELECT COUNT(*) FROM sponsored_clicks WHERE sponsored_id = ?");
        $stmt->execute([$itemId]);
        $totalClicks = $stmt->fetchColumn();
        
        // 24h clicks
        $dayAgo = date('Y-m-d H:i:s', strtotime('-24 hours'));
        $stmt = $db->prepare("SELECT COUNT(*) FROM sponsored_clicks WHERE sponsored_id = ? AND timestamp >= ?");
        $stmt->execute([$itemId, $dayAgo]);
        $clicks24h = $stmt->fetchColumn();
        
        // 7d clicks
        $weekAgo = date('Y-m-d H:i:s', strtotime('-7 days'));
        $stmt = $db->prepare("SELECT COUNT(*) FROM sponsored_clicks WHERE sponsored_id = ? AND timestamp >= ?");
        $stmt->execute([$itemId, $weekAgo]);
        $clicks7d = $stmt->fetchColumn();
        
        $analytics[] = [
            'id' => $itemId,
            'name' => $item['name'] ?? 'Unknown',
            'total_clicks' => (int)$totalClicks,
            'clicks_24h' => (int)$clicks24h,
            'clicks_7d' => (int)$clicks7d
        ];
    }
    
    jsonResponse(['analytics' => $analytics]);
}

function handleSponsoredClick() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $sponsoredId = $_GET['id'] ?? '';
    
    if (empty($sponsoredId)) {
        jsonResponse(['error' => 'Sponsored ID required'], 400);
    }
    
    $stmt = $db->prepare("INSERT INTO sponsored_clicks (sponsored_id) VALUES (?)");
    $stmt->execute([$sponsoredId]);
    
    jsonResponse(['success' => true]);
}

function handleCategories() {
    $db = getDB();
    
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $data = getJsonInput();
        
        if (empty($data['name'])) {
            jsonResponse(['error' => 'Category name is required'], 400);
        }
        
        $type = $data['type'] ?? 'all';
        
        // Check if exists
        $stmt = $db->prepare("SELECT id FROM categories WHERE name = ? AND type = ?");
        $stmt->execute([$data['name'], $type]);
        if ($stmt->fetch()) {
            jsonResponse(['error' => 'Category already exists'], 400);
        }
        
        $id = generateUUID();
        $stmt = $db->prepare("INSERT INTO categories (id, name, type) VALUES (?, ?, ?)");
        $stmt->execute([$id, $data['name'], $type]);
        
        jsonResponse(['id' => $id, 'name' => $data['name'], 'type' => $type]);
    } elseif ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
        $categoryId = $_GET['id'] ?? '';
        
        if (empty($categoryId)) {
            jsonResponse(['error' => 'Category ID required'], 400);
        }
        
        $stmt = $db->prepare("DELETE FROM categories WHERE id = ?");
        $stmt->execute([$categoryId]);
        
        if ($stmt->rowCount() === 0) {
            jsonResponse(['error' => 'Category not found'], 404);
        }
        
        jsonResponse(['success' => true]);
    } else {
        $typeFilter = $_GET['type_filter'] ?? null;
        
        $where = '1=1';
        $params = [];
        
        if ($typeFilter && $typeFilter !== 'all') {
            $where .= ' AND (type = ? OR type = "all")';
            $params[] = $typeFilter;
        }
        
        $stmt = $db->prepare("SELECT * FROM categories WHERE $where ORDER BY name");
        $stmt->execute($params);
        $categories = $stmt->fetchAll();
        
        jsonResponse($categories);
    }
}

function handleResendTest() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $settings = getSiteSettings();
    
    if (empty($settings['admin_email'])) {
        jsonResponse(['error' => 'Admin email is not configured'], 400);
    }
    
    $html = "
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>Resend Test Email</h2>
      <p>This is a test email to confirm your Resend configuration is working.</p>
    </body></html>";
    
    $sent = sendEmail($settings['admin_email'], "Resend test email", $html);
    
    if (!$sent) {
        jsonResponse(['error' => 'Failed to send test email'], 500);
    }
    
    jsonResponse(['success' => true]);
}

function handleResendSettings() {
    if ($_SERVER['REQUEST_METHOD'] !== 'PUT' && $_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    $updates = [];
    
    if (isset($data['resend_api_key'])) {
        $updates['resend_api_key'] = trim($data['resend_api_key']) ?: null;
    }
    
    if (isset($data['resend_sender_email'])) {
        $updates['resend_sender_email'] = trim($data['resend_sender_email']) ?: null;
    }
    
    if (!empty($updates)) {
        updateSiteSettings($updates);
    }
    
    $settings = getSiteSettings();
    $settings['resend_api_key'] = null; // Don't return API key
    $settings['recaptcha_secret_key'] = null;
    
    jsonResponse($settings);
}

function handleSeed() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    
    // Check existing count
    $stmt = $db->query("SELECT COUNT(*) FROM downloads");
    $count = $stmt->fetchColumn();
    
    if ($count >= 5000) {
        jsonResponse(['success' => false, 'message' => "Database already has $count items"]);
    }
    
    // Clear existing data
    $db->exec("DELETE FROM downloads");
    
    $downloads = [];
    $baseDate = strtotime('2024-01-01');
    
    $gamePrefixes = ['Super', 'Mega', 'Ultra', 'Epic', 'Cyber', 'Dark', 'Shadow', 'Crystal', 'Dragon', 'Space'];
    $gameSuffixes = ['Warriors', 'Quest', 'Saga', 'Chronicles', 'Adventures', 'Legends', 'Heroes', 'Knights'];
    $gameCategories = ['Action', 'RPG', 'Strategy', 'FPS', 'Racing', 'Sports'];
    $gameTags = ['multiplayer', 'singleplayer', 'co-op', 'open-world', 'indie', 'AAA', 'remastered', 'GOTY'];
    
    $softwareNames = ['VLC Media Player', 'GIMP Image Editor', 'Audacity Audio Editor', 'LibreOffice Suite', 
        'Firefox Browser', 'Blender 3D', 'Inkscape Vector', 'OBS Studio', 'HandBrake Video', '7-Zip Archiver'];
    $softwareCategories = ['Productivity', 'Development', 'Graphics', 'Utilities'];
    $softwareTags = ['portable', 'open-source', 'freeware', 'cross-platform', 'windows', 'mac', 'linux'];
    
    $movieGenres = ['Action', 'Comedy', 'Drama', 'Sci-Fi', 'Horror', 'Thriller'];
    $movieTags = ['720p', '1080p', '4K', 'HDR', 'BluRay', 'WEB-DL', 'subtitles', 'dual-audio'];
    
    // Generate games (~1500)
    for ($i = 0; $i < 1500; $i++) {
        $prefix = $gamePrefixes[array_rand($gamePrefixes)];
        $suffix = $gameSuffixes[array_rand($gameSuffixes)];
        $version = rand(1, 3) . '.' . rand(0, 9);
        $name = "$prefix $suffix $version";
        
        $daysOffset = rand(0, 365);
        $date = date('Y-m-d', $baseDate + $daysOffset * 86400);
        $sizeGb = rand(5, 100);
        
        $downloads[] = [
            generateUUID(), $name, "https://example.com/games/" . substr(md5(uniqid()), 0, 8),
            'game', $date, 1, date('Y-m-d H:i:s', $baseDate + $daysOffset * 86400),
            rand(0, 50000), "$sizeGb." . rand(0, 9) . " GB", $sizeGb * 1024 * 1024 * 1024,
            "Epic game", $gameCategories[array_rand($gameCategories)],
            json_encode(array_slice($gameTags, 0, rand(2, 4)))
        ];
    }
    
    // Generate software (~1200)
    for ($i = 0; $i < 1200; $i++) {
        $baseName = $softwareNames[array_rand($softwareNames)];
        $version = rand(1, 25) . '.' . rand(0, 9) . '.' . rand(0, 999);
        $name = "$baseName v$version";
        
        $daysOffset = rand(0, 365);
        $date = date('Y-m-d', $baseDate + $daysOffset * 86400);
        $sizeMb = rand(10, 2000);
        
        $downloads[] = [
            generateUUID(), $name, "https://example.com/software/" . substr(md5(uniqid()), 0, 8),
            'software', $date, 1, date('Y-m-d H:i:s', $baseDate + $daysOffset * 86400),
            rand(0, 100000), "$sizeMb MB", $sizeMb * 1024 * 1024,
            "Software application", $softwareCategories[array_rand($softwareCategories)],
            json_encode(array_slice($softwareTags, 0, rand(2, 4)))
        ];
    }
    
    // Generate movies (~1300)
    $movieAdj = ['The', 'A', 'Last', 'Final', 'Dark', 'Eternal', 'Hidden', 'Secret', 'Lost'];
    $movieNouns = ['Knight', 'Storm', 'Journey', 'Mission', 'Dream', 'Night', 'Day', 'Legacy', 'Code'];
    
    for ($i = 0; $i < 1300; $i++) {
        $adj = $movieAdj[array_rand($movieAdj)];
        $noun = $movieNouns[array_rand($movieNouns)];
        $year = rand(2020, 2025);
        $quality = ['720p', '1080p', '2160p 4K', 'BluRay', 'WEB-DL'][rand(0, 4)];
        $name = "$adj $noun ($year) $quality";
        
        $daysOffset = rand(0, 365);
        $date = date('Y-m-d', $baseDate + $daysOffset * 86400);
        $sizeGb = rand(1, 20);
        
        $downloads[] = [
            generateUUID(), $name, "https://example.com/movies/" . substr(md5(uniqid()), 0, 8),
            'movie', $date, 1, date('Y-m-d H:i:s', $baseDate + $daysOffset * 86400),
            rand(0, 75000), "$sizeGb." . rand(0, 9) . " GB", $sizeGb * 1024 * 1024 * 1024,
            "Movie film", $movieGenres[array_rand($movieGenres)],
            json_encode(array_slice($movieTags, 0, rand(2, 4)))
        ];
    }
    
    // Generate TV shows (~1000)
    $tvShows = [['Quantum Detective', 5], ['Starship Voyagers', 7], ['The Last Frontier', 4], ['Midnight City', 6]];
    $tvCategories = ['Drama', 'Comedy', 'Sci-Fi', 'Crime', 'Documentary'];
    $tvTags = ['complete-season', 'ongoing', 'finale', 'premiere', 'HDTV', 'WEB-DL'];
    
    foreach ($tvShows as [$showName, $seasons]) {
        for ($season = 1; $season <= $seasons && count($downloads) < 5000; $season++) {
            $episodes = rand(8, 24);
            for ($episode = 1; $episode <= $episodes && count($downloads) < 5000; $episode++) {
                $quality = ['720p', '1080p', 'WEB-DL', 'HDTV'][rand(0, 3)];
                $name = sprintf("%s S%02dE%02d %s", $showName, $season, $episode, $quality);
                
                $daysOffset = rand(0, 365);
                $date = date('Y-m-d', $baseDate + $daysOffset * 86400);
                $sizeMb = rand(200, 1500);
                
                $downloads[] = [
                    generateUUID(), $name, "https://example.com/tv/" . substr(md5(uniqid()), 0, 8),
                    'tv_show', $date, 1, date('Y-m-d H:i:s', $baseDate + $daysOffset * 86400),
                    rand(0, 30000), "$sizeMb MB", $sizeMb * 1024 * 1024,
                    "Season $season, Episode $episode", $tvCategories[array_rand($tvCategories)],
                    json_encode(array_slice($tvTags, 0, rand(2, 3)))
                ];
            }
        }
    }
    
    // Insert in batches
    $downloads = array_slice($downloads, 0, 5000);
    $stmt = $db->prepare("
        INSERT INTO downloads (id, name, download_link, type, submission_date, approved, created_at,
            download_count, file_size, file_size_bytes, description, category, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ");
    
    foreach ($downloads as $d) {
        $stmt->execute($d);
    }
    
    jsonResponse(['success' => true, 'message' => "Seeded " . count($downloads) . " downloads"]);
}
