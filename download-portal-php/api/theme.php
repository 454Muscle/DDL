<?php
/**
 * Theme API
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

setCorsHeaders();
header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    jsonResponse(getThemeSettings());
} elseif ($method === 'PUT' || $method === 'POST') {
    $data = getJsonInput();
    jsonResponse(updateThemeSettings($data));
} else {
    jsonResponse(['error' => 'Method not allowed'], 405);
}
