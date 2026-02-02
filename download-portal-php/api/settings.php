<?php
/**
 * Settings API
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

setCorsHeaders();
header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? 'get';

switch ($action) {
    case 'get':
        handleGetSettings();
        break;
    case 'update':
        handleUpdateSettings();
        break;
    case 'recaptcha':
        handleRecaptchaSettings();
        break;
    case 'stats':
        handleStats();
        break;
    default:
        jsonResponse(['error' => 'Invalid action'], 400);
}

function handleGetSettings() {
    $settings = getSiteSettings();
    
    // Remove sensitive fields
    unset($settings['resend_api_key']);
    unset($settings['recaptcha_secret_key']);
    unset($settings['admin_password_hash']);
    
    jsonResponse($settings);
}

function handleUpdateSettings() {
    if ($_SERVER['REQUEST_METHOD'] !== 'PUT' && $_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $data = getJsonInput();
    $settings = updateSiteSettings($data);
    
    // Remove sensitive fields from response
    unset($settings['resend_api_key']);
    unset($settings['recaptcha_secret_key']);
    unset($settings['admin_password_hash']);
    
    jsonResponse($settings);
}

function handleRecaptchaSettings() {
    $settings = getSiteSettings();
    
    jsonResponse([
        'site_key' => $settings['recaptcha_site_key'] ?? null,
        'enable_submit' => (bool)($settings['recaptcha_enable_submit'] ?? false),
        'enable_auth' => (bool)($settings['recaptcha_enable_auth'] ?? false)
    ]);
}

function handleStats() {
    $db = getDB();
    
    $total = $db->query("SELECT COUNT(*) FROM downloads WHERE approved = 1")->fetchColumn();
    $games = $db->query("SELECT COUNT(*) FROM downloads WHERE approved = 1 AND type = 'game'")->fetchColumn();
    $software = $db->query("SELECT COUNT(*) FROM downloads WHERE approved = 1 AND type = 'software'")->fetchColumn();
    $movies = $db->query("SELECT COUNT(*) FROM downloads WHERE approved = 1 AND type = 'movie'")->fetchColumn();
    $tvShows = $db->query("SELECT COUNT(*) FROM downloads WHERE approved = 1 AND type = 'tv_show'")->fetchColumn();
    
    $totalDownloads = $db->query("SELECT COALESCE(SUM(download_count), 0) FROM downloads WHERE approved = 1")->fetchColumn();
    
    jsonResponse([
        'total' => (int)$total,
        'games' => (int)$games,
        'software' => (int)$software,
        'movies' => (int)$movies,
        'tv_shows' => (int)$tvShows,
        'total_downloads' => (int)$totalDownloads
    ]);
}
