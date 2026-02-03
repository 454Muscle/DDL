<?php
/**
 * Download Portal - Installation Script
 * Run this once to set up the database
 */

$configFile = __DIR__ . '/config/database.php';
$schemaFile = __DIR__ . '/sql/schema.sql';

// Check if already configured
if (file_exists($configFile)) {
    require_once $configFile;
    
    try {
        $pdo = new PDO(
            "mysql:host=" . DB_HOST . ";charset=" . DB_CHARSET,
            DB_USER,
            DB_PASS,
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );
        
        // Check if database exists
        $stmt = $pdo->query("SHOW DATABASES LIKE '" . DB_NAME . "'");
        if ($stmt->rowCount() > 0) {
            // Database exists, check if tables exist
            $pdo->exec("USE " . DB_NAME);
            $stmt = $pdo->query("SHOW TABLES LIKE 'downloads'");
            if ($stmt->rowCount() > 0) {
                echo "<h1>Installation Already Complete</h1>";
                echo "<p>The database is already set up. <a href='index.php'>Go to homepage</a></p>";
                echo "<p style='color: red;'><strong>Security Notice:</strong> Delete this install.php file!</p>";
                exit;
            }
        }
    } catch (PDOException $e) {
        // Continue with installation
    }
}

$error = '';
$success = '';

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $dbHost = $_POST['db_host'] ?? 'localhost';
    $dbName = $_POST['db_name'] ?? 'download_portal';
    $dbUser = $_POST['db_user'] ?? 'root';
    $dbPass = $_POST['db_pass'] ?? '';
    $siteUrl = rtrim($_POST['site_url'] ?? '', '/');
    
    try {
        // Test connection
        $pdo = new PDO(
            "mysql:host=$dbHost;charset=utf8mb4",
            $dbUser,
            $dbPass,
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );
        
        // Create database
        $pdo->exec("CREATE DATABASE IF NOT EXISTS `$dbName` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
        $pdo->exec("USE `$dbName`");
        
        // Run schema
        $schema = file_get_contents($schemaFile);
        // Remove the first two lines (CREATE DATABASE and USE)
        $schema = preg_replace('/^.*?;.*?;/s', '', $schema, 1);
        
        // Split and execute statements
        $statements = array_filter(array_map('trim', explode(';', $schema)));
        foreach ($statements as $stmt) {
            if (!empty($stmt)) {
                $pdo->exec($stmt);
            }
        }
        
        // Update config file
        $configContent = "<?php
/**
 * Database Configuration
 */

define('DB_HOST', '$dbHost');
define('DB_NAME', '$dbName');
define('DB_USER', '$dbUser');
define('DB_PASS', '$dbPass');
define('DB_CHARSET', 'utf8mb4');

// Site URL (no trailing slash)
define('SITE_URL', '$siteUrl');

// Resend API (optional - for email notifications)
define('RESEND_API_KEY', '');
define('SENDER_EMAIL', 'noreply@yourdomain.com');

// Admin password (fallback if not set in database)
define('ADMIN_PASSWORD', 'admin123');

// Session settings
define('SESSION_NAME', 'download_portal_session');

// Timezone
date_default_timezone_set('UTC');

/**
 * Database connection
 */
function getDB() {
    static \$pdo = null;
    
    if (\$pdo === null) {
        \$dsn = \"mysql:host=\" . DB_HOST . \";dbname=\" . DB_NAME . \";charset=\" . DB_CHARSET;
        \$options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ];
        \$pdo = new PDO(\$dsn, DB_USER, DB_PASS, \$options);
    }
    
    return \$pdo;
}

/**
 * Generate UUID v4
 */
function generateUUID() {
    return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        mt_rand(0, 0xffff), mt_rand(0, 0xffff),
        mt_rand(0, 0xffff),
        mt_rand(0, 0x0fff) | 0x4000,
        mt_rand(0, 0x3fff) | 0x8000,
        mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
    );
}

/**
 * JSON response helper
 */
function jsonResponse(\$data, \$statusCode = 200) {
    http_response_code(\$statusCode);
    header('Content-Type: application/json');
    echo json_encode(\$data);
    exit;
}

/**
 * Get client IP address
 */
function getClientIP() {
    if (!empty(\$_SERVER['HTTP_CLIENT_IP'])) {
        return \$_SERVER['HTTP_CLIENT_IP'];
    } elseif (!empty(\$_SERVER['HTTP_X_FORWARDED_FOR'])) {
        return explode(',', \$_SERVER['HTTP_X_FORWARDED_FOR'])[0];
    }
    return \$_SERVER['REMOTE_ADDR'] ?? 'unknown';
}

/**
 * CORS headers
 */
function setCorsHeaders() {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization');
    
    if (\$_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(200);
        exit;
    }
}
";
        
        file_put_contents($configFile, $configContent);
        
        $success = 'Installation complete! <a href="index.php">Go to homepage</a><br><br><strong style="color: red;">IMPORTANT: Delete this install.php file for security!</strong>';
        
    } catch (PDOException $e) {
        $error = 'Database error: ' . $e->getMessage();
    } catch (Exception $e) {
        $error = 'Error: ' . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Install - Download Portal</title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <main>
        <div class="container" style="max-width: 600px; margin: 50px auto;">
            <h1 class="section-title">DOWNLOAD PORTAL INSTALLATION</h1>
            
            <?php if ($error): ?>
                <div class="alert alert-error"><?= $error ?></div>
            <?php endif; ?>
            
            <?php if ($success): ?>
                <div class="alert alert-success"><?= $success ?></div>
            <?php else: ?>
                <div class="admin-section">
                    <h3>Database Configuration</h3>
                    <form method="POST">
                        <div class="form-group">
                            <label>Database Host</label>
                            <input type="text" name="db_host" value="localhost" required>
                        </div>
                        <div class="form-group">
                            <label>Database Name</label>
                            <input type="text" name="db_name" value="download_portal" required>
                        </div>
                        <div class="form-group">
                            <label>Database User</label>
                            <input type="text" name="db_user" value="root" required>
                        </div>
                        <div class="form-group">
                            <label>Database Password</label>
                            <input type="password" name="db_pass" value="">
                        </div>
                        <div class="form-group">
                            <label>Site URL (e.g., https://yourdomain.com/download-portal)</label>
                            <input type="url" name="site_url" value="http://localhost/download-portal-php" required>
                        </div>
                        <button type="submit" class="btn">INSTALL</button>
                    </form>
                </div>
                
                <div class="admin-section mt-20">
                    <h3>Requirements</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin-bottom: 10px;">
                            <?= version_compare(PHP_VERSION, '7.4.0', '>=') ? '✓' : '✗' ?> 
                            PHP 7.4+ (Current: <?= PHP_VERSION ?>)
                        </li>
                        <li style="margin-bottom: 10px;">
                            <?= extension_loaded('pdo_mysql') ? '✓' : '✗' ?> 
                            PDO MySQL Extension
                        </li>
                        <li style="margin-bottom: 10px;">
                            <?= extension_loaded('json') ? '✓' : '✗' ?> 
                            JSON Extension
                        </li>
                        <li style="margin-bottom: 10px;">
                            <?= is_writable(__DIR__ . '/config') ? '✓' : '✗' ?> 
                            Config directory writable
                        </li>
                    </ul>
                </div>
            <?php endif; ?>
        </div>
    </main>
</body>
</html>
