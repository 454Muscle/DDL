<?php
/**
 * Downloads API
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

setCorsHeaders();
header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? 'list';

switch ($action) {
    case 'list':
        handleList();
        break;
    case 'top':
        handleTop();
        break;
    case 'trending':
        handleTrending();
        break;
    case 'track':
        handleTrack();
        break;
    case 'increment':
        handleIncrement();
        break;
    default:
        jsonResponse(['error' => 'Invalid action'], 400);
}

function handleList() {
    $db = getDB();
    
    $page = max(1, (int)($_GET['page'] ?? 1));
    $limit = min(100, max(1, (int)($_GET['limit'] ?? 50)));
    $offset = ($page - 1) * $limit;
    
    $where = ['approved = 1'];
    $params = [];
    
    // Type filter
    if (!empty($_GET['type_filter']) && $_GET['type_filter'] !== 'all') {
        $where[] = 'type = ?';
        $params[] = $_GET['type_filter'];
    }
    
    // Search
    if (!empty($_GET['search'])) {
        $where[] = 'name LIKE ?';
        $params[] = '%' . $_GET['search'] . '%';
    }
    
    // Category
    if (!empty($_GET['category'])) {
        $where[] = 'category = ?';
        $params[] = $_GET['category'];
    }
    
    // Date range
    if (!empty($_GET['date_from'])) {
        $where[] = 'submission_date >= ?';
        $params[] = $_GET['date_from'];
    }
    if (!empty($_GET['date_to'])) {
        $where[] = 'submission_date <= ?';
        $params[] = $_GET['date_to'];
    }
    
    // File size range
    if (!empty($_GET['size_min'])) {
        $minBytes = parseFileSizeToBytes($_GET['size_min']);
        if ($minBytes) {
            $where[] = 'file_size_bytes >= ?';
            $params[] = $minBytes;
        }
    }
    if (!empty($_GET['size_max'])) {
        $maxBytes = parseFileSizeToBytes($_GET['size_max']);
        if ($maxBytes) {
            $where[] = 'file_size_bytes <= ?';
            $params[] = $maxBytes;
        }
    }
    
    // Tags filter
    if (!empty($_GET['tags'])) {
        $tags = array_map('trim', explode(',', $_GET['tags']));
        foreach ($tags as $tag) {
            $where[] = 'JSON_CONTAINS(tags, ?)';
            $params[] = json_encode($tag);
        }
    }
    
    $whereClause = implode(' AND ', $where);
    
    // Sorting
    $sortBy = $_GET['sort_by'] ?? 'date_desc';
    $orderBy = 'created_at DESC';
    switch ($sortBy) {
        case 'date_asc': $orderBy = 'created_at ASC'; break;
        case 'downloads_desc': $orderBy = 'download_count DESC'; break;
        case 'downloads_asc': $orderBy = 'download_count ASC'; break;
        case 'name_asc': $orderBy = 'name ASC'; break;
        case 'name_desc': $orderBy = 'name DESC'; break;
        case 'size_desc': $orderBy = 'file_size_bytes DESC'; break;
        case 'size_asc': $orderBy = 'file_size_bytes ASC'; break;
    }
    
    // Get total count
    $countSql = "SELECT COUNT(*) FROM downloads WHERE $whereClause";
    $stmt = $db->prepare($countSql);
    $stmt->execute($params);
    $total = $stmt->fetchColumn();
    
    // Get items
    $sql = "SELECT * FROM downloads WHERE $whereClause ORDER BY $orderBy LIMIT $limit OFFSET $offset";
    $stmt = $db->prepare($sql);
    $stmt->execute($params);
    $items = $stmt->fetchAll();
    
    // Parse JSON tags
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

function handleTop() {
    $db = getDB();
    $settings = getSiteSettings();
    
    $enabled = (bool)$settings['top_downloads_enabled'];
    $count = (int)($settings['top_downloads_count'] ?? 5);
    $sponsored = $settings['sponsored_downloads'] ?? [];
    
    if (!$enabled) {
        jsonResponse(['enabled' => false, 'items' => [], 'sponsored' => []]);
    }
    
    $remainingCount = max(0, $count - count($sponsored));
    $top = [];
    
    if ($remainingCount > 0) {
        $stmt = $db->prepare("
            SELECT * FROM downloads 
            WHERE approved = 1 
            ORDER BY download_count DESC 
            LIMIT ?
        ");
        $stmt->execute([$remainingCount]);
        $top = $stmt->fetchAll();
        
        foreach ($top as &$item) {
            $item['tags'] = json_decode($item['tags'] ?? '[]', true) ?? [];
        }
    }
    
    jsonResponse([
        'enabled' => true,
        'sponsored' => array_slice($sponsored, 0, 5),
        'items' => $top,
        'total_slots' => $count
    ]);
}

function handleTrending() {
    $db = getDB();
    $settings = getSiteSettings();
    
    $enabled = (bool)($settings['trending_downloads_enabled'] ?? false);
    $count = (int)($settings['trending_downloads_count'] ?? 5);
    
    if (!$enabled) {
        jsonResponse(['enabled' => false, 'items' => []]);
    }
    
    // Get downloads with activity in the last 7 days
    $sevenDaysAgo = date('Y-m-d H:i:s', strtotime('-7 days'));
    
    $stmt = $db->prepare("
        SELECT da.download_id, COUNT(*) as recent_count
        FROM download_activity da
        WHERE da.timestamp >= ?
        GROUP BY da.download_id
        ORDER BY recent_count DESC
        LIMIT ?
    ");
    $stmt->execute([$sevenDaysAgo, $count]);
    $trendingIds = $stmt->fetchAll(PDO::FETCH_KEY_PAIR);
    
    $trending = [];
    if (!empty($trendingIds)) {
        $placeholders = implode(',', array_fill(0, count($trendingIds), '?'));
        $stmt = $db->prepare("SELECT * FROM downloads WHERE id IN ($placeholders) AND approved = 1");
        $stmt->execute(array_keys($trendingIds));
        $downloads = $stmt->fetchAll();
        
        // Sort by trending order
        $downloadMap = [];
        foreach ($downloads as $d) {
            $d['tags'] = json_decode($d['tags'] ?? '[]', true) ?? [];
            $downloadMap[$d['id']] = $d;
        }
        
        foreach (array_keys($trendingIds) as $id) {
            if (isset($downloadMap[$id])) {
                $trending[] = $downloadMap[$id];
            }
        }
    }
    
    // Fallback to most downloaded if not enough trending
    if (count($trending) < $count) {
        $existingIds = array_column($trending, 'id');
        $remaining = $count - count($trending);
        
        $excludeClause = '';
        $params = [];
        if (!empty($existingIds)) {
            $placeholders = implode(',', array_fill(0, count($existingIds), '?'));
            $excludeClause = "AND id NOT IN ($placeholders)";
            $params = $existingIds;
        }
        $params[] = $remaining;
        
        $stmt = $db->prepare("
            SELECT * FROM downloads 
            WHERE approved = 1 $excludeClause
            ORDER BY download_count DESC 
            LIMIT ?
        ");
        $stmt->execute($params);
        $fallback = $stmt->fetchAll();
        
        foreach ($fallback as &$item) {
            $item['tags'] = json_decode($item['tags'] ?? '[]', true) ?? [];
        }
        
        $trending = array_merge($trending, $fallback);
    }
    
    jsonResponse([
        'enabled' => true,
        'items' => array_slice($trending, 0, $count)
    ]);
}

function handleTrack() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $downloadId = $_GET['id'] ?? '';
    
    if (empty($downloadId)) {
        jsonResponse(['error' => 'Download ID required'], 400);
    }
    
    // Check if download exists
    $stmt = $db->prepare("SELECT id FROM downloads WHERE id = ?");
    $stmt->execute([$downloadId]);
    if (!$stmt->fetch()) {
        jsonResponse(['error' => 'Download not found'], 404);
    }
    
    // Increment download count
    $stmt = $db->prepare("UPDATE downloads SET download_count = download_count + 1 WHERE id = ?");
    $stmt->execute([$downloadId]);
    
    // Record activity for trending
    $stmt = $db->prepare("INSERT INTO download_activity (download_id) VALUES (?)");
    $stmt->execute([$downloadId]);
    
    jsonResponse(['success' => true]);
}

function handleIncrement() {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        jsonResponse(['error' => 'Method not allowed'], 405);
    }
    
    $db = getDB();
    $downloadId = $_GET['id'] ?? '';
    
    if (empty($downloadId)) {
        jsonResponse(['error' => 'Download ID required'], 400);
    }
    
    $stmt = $db->prepare("UPDATE downloads SET download_count = download_count + 1 WHERE id = ?");
    $stmt->execute([$downloadId]);
    
    if ($stmt->rowCount() === 0) {
        jsonResponse(['error' => 'Download not found'], 404);
    }
    
    jsonResponse(['success' => true]);
}
