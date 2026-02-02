<?php
/**
 * Submissions API
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';
require_once __DIR__ . '/../includes/captcha.php';
require_once __DIR__ . '/../includes/email.php';

setCorsHeaders();
header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? 'create';

switch ($action) {
    case 'create':
        handleCreate();
        break;
    case 'bulk':
        handleBulkCreate();
        break;
    case 'remaining':
        handleRemaining();
        break;
    case 'captcha':
        handleCaptcha();
        break;
    default:
        jsonResponse(['error' => 'Invalid action'], 400);
}

function handleCaptcha() {
    jsonResponse(generateCaptcha());
}

function handleRemaining() {
    $settings = getSiteSettings();
    $dailyLimit = (int)($settings['daily_submission_limit'] ?? 10);
    
    $ip = getClientIP();
    $rateLimit = checkRateLimit($ip, $dailyLimit);
    
    jsonResponse([
        'daily_limit' => $dailyLimit,
        'used' => $rateLimit['used'],
        'remaining' => $rateLimit['remaining']
    ]);
}

function handleCreate() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $data = getJsonInput();
    $settings = getSiteSettings();
    
    // Verify captcha
    $captchaResult = verifyCaptchaOrRecaptcha($data, $settings, 'submit');
    if (!$captchaResult['valid']) {
        jsonResponse(['error' => $captchaResult['error']], 400);
    }
    
    // Check rate limit
    $dailyLimit = (int)($settings['daily_submission_limit'] ?? 10);
    $ip = getClientIP();
    $rateLimit = checkRateLimit($ip, $dailyLimit);
    
    if (!$rateLimit['allowed']) {
        jsonResponse(['error' => "Daily submission limit ($dailyLimit) reached. Try again tomorrow."], 429);
    }
    
    // Validate required fields
    $required = ['name', 'download_link', 'type', 'site_name', 'site_url'];
    foreach ($required as $field) {
        if (empty($data[$field])) {
            jsonResponse(['error' => "Field '$field' is required"], 400);
        }
    }
    
    // Validate URL
    $urlResult = validateHttpUrl($data['site_url']);
    if (!$urlResult['valid']) {
        jsonResponse(['error' => $urlResult['error']], 400);
    }
    
    // Validate type
    $validTypes = ['game', 'software', 'movie', 'tv_show'];
    if (!in_array($data['type'], $validTypes)) {
        jsonResponse(['error' => 'Invalid type'], 400);
    }
    
    // Parse file size
    $fileSizeBytes = null;
    if (!empty($data['file_size'])) {
        $fileSizeBytes = parseFileSizeToBytes($data['file_size']);
    }
    
    // Create submission
    $id = generateUUID();
    $today = date('Y-m-d');
    $tags = json_encode($data['tags'] ?? []);
    
    $stmt = $db->prepare("
        INSERT INTO submissions (
            id, name, download_link, type, submission_date, file_size, file_size_bytes,
            description, category, tags, site_name, site_url, submitter_email
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([
        $id,
        $data['name'],
        $data['download_link'],
        $data['type'],
        $today,
        $data['file_size'] ?? null,
        $fileSizeBytes,
        $data['description'] ?? null,
        $data['category'] ?? null,
        $tags,
        $data['site_name'],
        $urlResult['url'],
        $data['submitter_email'] ?? null
    ]);
    
    // Update rate limit
    incrementRateLimit($ip);
    
    // Get the created submission
    $stmt = $db->prepare("SELECT * FROM submissions WHERE id = ?");
    $stmt->execute([$id]);
    $submission = $stmt->fetch();
    $submission['tags'] = json_decode($submission['tags'] ?? '[]', true);
    
    // Send emails
    if (!empty($data['submitter_email'])) {
        sendSubmissionEmail($data['submitter_email'], $submission);
    }
    sendAdminSubmissionNotification([$submission]);
    
    // Auto-approve if enabled
    if ($settings['auto_approve_submissions']) {
        autoApproveSubmission($submission);
    }
    
    jsonResponse($submission);
}

function handleBulkCreate() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $data = getJsonInput();
    $settings = getSiteSettings();
    
    if (empty($data['items']) || !is_array($data['items'])) {
        jsonResponse(['error' => 'No items provided'], 400);
    }
    
    $itemCount = count($data['items']);
    
    // Check rate limit
    $dailyLimit = (int)($settings['daily_submission_limit'] ?? 10);
    $ip = getClientIP();
    $rateLimit = checkRateLimit($ip, $dailyLimit);
    
    if ($rateLimit['used'] + $itemCount > $dailyLimit) {
        jsonResponse(['error' => "Daily submission limit ($dailyLimit) exceeded"], 429);
    }
    
    // Verify captcha (once for entire batch)
    $captchaResult = verifyCaptchaOrRecaptcha($data, $settings, 'submit');
    if (!$captchaResult['valid']) {
        jsonResponse(['error' => $captchaResult['error']], 400);
    }
    
    // Update rate limit
    incrementRateLimit($ip, $itemCount);
    
    $today = date('Y-m-d');
    $createdDocs = [];
    $bulkEmail = $data['submitter_email'] ?? '';
    
    foreach ($data['items'] as $item) {
        // Validate required fields
        if (empty($item['name']) || empty($item['download_link']) || empty($item['type']) || 
            empty($item['site_name']) || empty($item['site_url'])) {
            continue; // Skip invalid items
        }
        
        $urlResult = validateHttpUrl($item['site_url']);
        if (!$urlResult['valid']) {
            continue;
        }
        
        $id = generateUUID();
        $fileSizeBytes = !empty($item['file_size']) ? parseFileSizeToBytes($item['file_size']) : null;
        $tags = json_encode($item['tags'] ?? []);
        $email = $bulkEmail ?: ($item['submitter_email'] ?? null);
        
        $stmt = $db->prepare("
            INSERT INTO submissions (
                id, name, download_link, type, submission_date, file_size, file_size_bytes,
                description, category, tags, site_name, site_url, submitter_email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ");
        $stmt->execute([
            $id,
            $item['name'],
            $item['download_link'],
            $item['type'],
            $today,
            $item['file_size'] ?? null,
            $fileSizeBytes,
            $item['description'] ?? null,
            $item['category'] ?? null,
            $tags,
            $item['site_name'],
            $urlResult['url'],
            $email
        ]);
        
        $createdDocs[] = [
            'id' => $id,
            'name' => $item['name'],
            'type' => $item['type'],
            'submission_date' => $today
        ];
    }
    
    // Send emails
    if (!empty($bulkEmail) && !empty($createdDocs)) {
        // Send bulk confirmation (simplified)
        sendAdminSubmissionNotification($createdDocs);
    }
    
    // Auto-approve if enabled
    if ($settings['auto_approve_submissions']) {
        foreach ($createdDocs as $doc) {
            $stmt = $db->prepare("SELECT * FROM submissions WHERE id = ?");
            $stmt->execute([$doc['id']]);
            $submission = $stmt->fetch();
            if ($submission) {
                autoApproveSubmission($submission);
            }
        }
    }
    
    jsonResponse(['success' => true, 'count' => count($createdDocs)]);
}

function autoApproveSubmission($submission) {
    $db = getDB();
    
    // Create download entry
    $downloadId = generateUUID();
    $tags = is_array($submission['tags']) ? json_encode($submission['tags']) : $submission['tags'];
    
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
        $tags,
        $submission['site_name'],
        $submission['site_url']
    ]);
    
    // Update submission status
    $stmt = $db->prepare("UPDATE submissions SET status = 'approved', seen_by_admin = 1 WHERE id = ?");
    $stmt->execute([$submission['id']]);
}
