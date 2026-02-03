<?php
/**
 * Download Portal - Homepage
 */

// Check if install.php exists and database is not configured
if (file_exists(__DIR__ . '/install.php')) {
    // Try to connect to database
    try {
        require_once __DIR__ . '/includes/functions.php';
        $db = getDB();
        // Check if tables exist
        $stmt = $db->query("SHOW TABLES LIKE 'site_settings'");
        if ($stmt->rowCount() === 0) {
            header('Location: install.php');
            exit;
        }
    } catch (Exception $e) {
        header('Location: install.php');
        exit;
    }
} else {
    require_once __DIR__ . '/includes/functions.php';
}

$settings = getSiteSettings();
$theme = getThemeSettings();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="<?= ($theme['mode'] ?? 'dark') === 'light' ? 'light-theme' : '' ?>">
    <header>
        <div class="container">
            <div class="header-content">
                <a href="index.php" class="logo"><?= htmlspecialchars($settings['site_name'] ?? 'DOWNLOAD ZONE') ?></a>
                <nav>
                    <a href="index.php" class="active">HOME</a>
                    <a href="submit.php">SUBMIT</a>
                    <a href="login.php">LOGIN</a>
                    <a href="admin/">ADMIN</a>
                    <button class="theme-toggle" id="themeToggle"><?= ($theme['mode'] ?? 'dark') === 'dark' ? '☀ LIGHT' : '☾ DARK' ?></button>
                </nav>
            </div>
        </div>
    </header>

    <main>
        <div class="container">
            <!-- Stats Bar -->
            <div class="stats-bar">
                <div class="stat-item">
                    <div class="stat-value" id="statTotal">0</div>
                    <div class="stat-label">Total Files</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="statGames">0</div>
                    <div class="stat-label">Games</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="statSoftware">0</div>
                    <div class="stat-label">Software</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="statMovies">0</div>
                    <div class="stat-label">Movies</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="statTvShows">0</div>
                    <div class="stat-label">TV Shows</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="statDownloads">0</div>
                    <div class="stat-label">Downloads</div>
                </div>
            </div>

            <!-- Search Section -->
            <div class="search-section">
                <div class="search-bar">
                    <input type="text" id="searchInput" class="search-input" placeholder="Search downloads...">
                    <button id="searchBtn" class="btn">SEARCH</button>
                </div>
                <div class="filters">
                    <select id="typeFilter" class="filter-select">
                        <option value="all">All Types</option>
                        <option value="game">Games</option>
                        <option value="software">Software</option>
                        <option value="movie">Movies</option>
                        <option value="tv_show">TV Shows</option>
                    </select>
                    <select id="sortFilter" class="filter-select">
                        <option value="date_desc">Newest First</option>
                        <option value="date_asc">Oldest First</option>
                        <option value="downloads_desc">Most Downloads</option>
                        <option value="downloads_asc">Least Downloads</option>
                        <option value="name_asc">Name (A-Z)</option>
                        <option value="name_desc">Name (Z-A)</option>
                    </select>
                </div>
            </div>

            <!-- Top Downloads Section -->
            <div class="top-section">
                <h2 class="section-title">TOP DOWNLOADS</h2>
                <div class="downloads-grid" id="topDownloads">
                    <div class="loading">Loading top downloads</div>
                </div>
            </div>

            <!-- Trending Section -->
            <div class="top-section">
                <h2 class="section-title">🔥 TRENDING NOW</h2>
                <div class="downloads-grid" id="trendingDownloads">
                    <div class="loading">Loading trending</div>
                </div>
            </div>

            <!-- All Downloads Section -->
            <div class="top-section">
                <h2 class="section-title">ALL DOWNLOADS</h2>
                <div id="downloadsTableContainer">
                    <table class="downloads-table" id="downloadsTable">
                        <thead>
                            <tr>
                                <th style="width: 40%">Download Name</th>
                                <th style="width: 12%">Date</th>
                                <th style="width: 12%">Type</th>
                                <th style="width: 12%">Size</th>
                                <th style="width: 12%">Site</th>
                                <th style="width: 12%">Downloads</th>
                            </tr>
                        </thead>
                        <tbody id="downloadsTableBody">
                            <tr><td colspan="6" class="loading">Loading downloads</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Pagination -->
            <div class="pagination" id="pagination"></div>
        </div>
    </main>

    <footer>
        <div class="container">
            <div class="footer-content">
                <p id="footerLine1"><?= htmlspecialchars(str_replace(
                    ['{admin_email}'],
                    [$settings['admin_email'] ?? 'admin@example.com'],
                    $settings['footer_line1_template'] ?? ''
                )) ?></p>
                <p id="footerLine2"><?= htmlspecialchars(str_replace(
                    ['{site_name}', '{year}'],
                    [$settings['site_name'] ?? 'DOWNLOAD ZONE', date('Y')],
                    $settings['footer_line2_template'] ?? ''
                )) ?></p>
            </div>
        </div>
    </footer>

    <script src="assets/js/app.js"></script>
</body>
</html>
