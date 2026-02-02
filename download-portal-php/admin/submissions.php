<?php
/**
 * Download Portal - Admin Submissions Page
 */
require_once __DIR__ . '/../includes/functions.php';
require_once __DIR__ . '/../includes/auth.php';
require_once __DIR__ . '/../includes/email.php';

initSession();
if (!isAdminLoggedIn()) {
    header('Location: index.php');
    exit;
}

$settings = getSiteSettings();
$theme = getThemeSettings();
$db = getDB();

// Handle actions
$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    $id = $_POST['id'] ?? '';
    
    if ($action === 'approve' && $id) {
        // Get submission
        $stmt = $db->prepare("SELECT * FROM submissions WHERE id = ?");
        $stmt->execute([$id]);
        $submission = $stmt->fetch();
        
        if ($submission) {
            // Create download
            $downloadId = generateUUID();
            $stmt = $db->prepare("
                INSERT INTO downloads (id, name, download_link, type, submission_date, approved, file_size, file_size_bytes, description, category, tags, site_name, site_url)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
            ");
            $stmt->execute([
                $downloadId, $submission['name'], $submission['download_link'], $submission['type'],
                $submission['submission_date'], $submission['file_size'], $submission['file_size_bytes'],
                $submission['description'], $submission['category'], $submission['tags'],
                $submission['site_name'], $submission['site_url']
            ]);
            
            // Update submission status
            $stmt = $db->prepare("UPDATE submissions SET status = 'approved' WHERE id = ?");
            $stmt->execute([$id]);
            
            // Send email
            if ($submission['submitter_email']) {
                $submission['tags'] = json_decode($submission['tags'] ?? '[]', true);
                sendApprovalEmail($submission['submitter_email'], $submission);
            }
            
            $message = 'Submission approved!';
            $messageType = 'success';
        }
    } elseif ($action === 'reject' && $id) {
        $stmt = $db->prepare("UPDATE submissions SET status = 'rejected' WHERE id = ?");
        $stmt->execute([$id]);
        $message = 'Submission rejected';
        $messageType = 'warning';
    } elseif ($action === 'delete' && $id) {
        $stmt = $db->prepare("DELETE FROM submissions WHERE id = ?");
        $stmt->execute([$id]);
        $message = 'Submission deleted';
        $messageType = 'success';
    }
}

// Get submissions
$status = $_GET['status'] ?? '';
$page = max(1, (int)($_GET['page'] ?? 1));
$limit = 20;
$offset = ($page - 1) * $limit;

$where = '1=1';
$params = [];
if ($status && in_array($status, ['pending', 'approved', 'rejected'])) {
    $where .= ' AND status = ?';
    $params[] = $status;
}

$countStmt = $db->prepare("SELECT COUNT(*) FROM submissions WHERE $where");
$countStmt->execute($params);
$total = $countStmt->fetchColumn();
$totalPages = max(1, ceil($total / $limit));

$params[] = $limit;
$params[] = $offset;
$stmt = $db->prepare("SELECT * FROM submissions WHERE $where ORDER BY created_at DESC LIMIT ? OFFSET ?");
$stmt->execute($params);
$submissions = $stmt->fetchAll();

// Get counts
$pendingCount = $db->query("SELECT COUNT(*) FROM submissions WHERE status = 'pending'")->fetchColumn();
$approvedCount = $db->query("SELECT COUNT(*) FROM submissions WHERE status = 'approved'")->fetchColumn();
$rejectedCount = $db->query("SELECT COUNT(*) FROM submissions WHERE status = 'rejected'")->fetchColumn();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submissions - Admin</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body class="<?= $theme['mode'] === 'light' ? 'light-theme' : '' ?>">
    <header>
        <div class="container">
            <div class="header-content">
                <a href="../index.php" class="logo"><?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></a>
                <nav>
                    <a href="../index.php">HOME</a>
                    <a href="submissions.php" class="active">SUBMISSIONS</a>
                    <a href="index.php">DASHBOARD</a>
                </nav>
            </div>
        </div>
    </header>

    <main>
        <div class="container">
            <h1 class="section-title">MANAGE SUBMISSIONS</h1>
            
            <?php if ($message): ?>
                <div class="alert alert-<?= $messageType ?>"><?= htmlspecialchars($message) ?></div>
            <?php endif; ?>
            
            <!-- Filters -->
            <div class="filters mb-20">
                <a href="?status=" class="btn <?= !$status ? '' : 'btn-secondary' ?>">ALL (<?= $total ?>)</a>
                <a href="?status=pending" class="btn <?= $status === 'pending' ? '' : 'btn-secondary' ?>">PENDING (<?= $pendingCount ?>)</a>
                <a href="?status=approved" class="btn <?= $status === 'approved' ? '' : 'btn-secondary' ?>">APPROVED (<?= $approvedCount ?>)</a>
                <a href="?status=rejected" class="btn <?= $status === 'rejected' ? '' : 'btn-secondary' ?>">REJECTED (<?= $rejectedCount ?>)</a>
            </div>
            
            <!-- Submissions Table -->
            <div style="overflow-x: auto;">
                <table class="downloads-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Site</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($submissions as $sub): ?>
                            <tr>
                                <td>
                                    <strong><?= htmlspecialchars($sub['name']) ?></strong>
                                    <?php if ($sub['submitter_email']): ?>
                                        <br><small style="color: var(--text-muted);"><?= htmlspecialchars($sub['submitter_email']) ?></small>
                                    <?php endif; ?>
                                </td>
                                <td><span class="download-type"><?= htmlspecialchars($sub['type']) ?></span></td>
                                <td>
                                    <?php if ($sub['site_name']): ?>
                                        <a href="<?= htmlspecialchars($sub['site_url']) ?>" target="_blank" style="color: var(--accent);">
                                            <?= htmlspecialchars($sub['site_name']) ?>
                                        </a>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <span class="badge badge-<?= $sub['status'] ?>"><?= strtoupper($sub['status']) ?></span>
                                </td>
                                <td><?= htmlspecialchars($sub['submission_date']) ?></td>
                                <td>
                                    <form method="POST" style="display: inline;">
                                        <input type="hidden" name="id" value="<?= $sub['id'] ?>">
                                        <?php if ($sub['status'] === 'pending'): ?>
                                            <button type="submit" name="action" value="approve" class="btn" style="padding: 5px 10px;">✓</button>
                                            <button type="submit" name="action" value="reject" class="btn btn-secondary" style="padding: 5px 10px;">✗</button>
                                        <?php endif; ?>
                                        <button type="submit" name="action" value="delete" class="btn btn-danger" style="padding: 5px 10px;" onclick="return confirm('Delete this submission?')">🗑</button>
                                    </form>
                                    <a href="<?= htmlspecialchars($sub['download_link']) ?>" target="_blank" class="btn btn-secondary" style="padding: 5px 10px;">↗</a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                        <?php if (empty($submissions)): ?>
                            <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No submissions found</td></tr>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
            
            <!-- Pagination -->
            <?php if ($totalPages > 1): ?>
                <div class="pagination">
                    <?php if ($page > 1): ?>
                        <a href="?status=<?= $status ?>&page=<?= $page - 1 ?>" class="btn btn-secondary">← PREV</a>
                    <?php endif; ?>
                    
                    <span class="page-info">Page <?= $page ?> of <?= $totalPages ?></span>
                    
                    <?php if ($page < $totalPages): ?>
                        <a href="?status=<?= $status ?>&page=<?= $page + 1 ?>" class="btn btn-secondary">NEXT →</a>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
        </div>
    </main>
</body>
</html>
