-- Download Portal Database Schema
-- MySQL/MariaDB

CREATE DATABASE IF NOT EXISTS download_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE download_portal;

-- Downloads table
CREATE TABLE downloads (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    download_link TEXT NOT NULL,
    type ENUM('game', 'software', 'movie', 'tv_show') NOT NULL,
    submission_date DATE NOT NULL,
    approved TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    download_count INT DEFAULT 0,
    file_size VARCHAR(50),
    file_size_bytes BIGINT,
    description TEXT,
    category VARCHAR(100),
    tags JSON,
    site_name VARCHAR(100),
    site_url VARCHAR(500),
    INDEX idx_type (type),
    INDEX idx_approved (approved),
    INDEX idx_category (category),
    INDEX idx_download_count (download_count),
    INDEX idx_created_at (created_at),
    FULLTEXT idx_name (name)
) ENGINE=InnoDB;

-- Submissions table
CREATE TABLE submissions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    download_link TEXT NOT NULL,
    type ENUM('game', 'software', 'movie', 'tv_show') NOT NULL,
    submission_date DATE NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    seen_by_admin TINYINT(1) DEFAULT 0,
    file_size VARCHAR(50),
    file_size_bytes BIGINT,
    description TEXT,
    category VARCHAR(100),
    tags JSON,
    site_name VARCHAR(100),
    site_url VARCHAR(500),
    submitter_email VARCHAR(255),
    submitter_user_id VARCHAR(36),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_verified TINYINT(1) DEFAULT 0,
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- Categories table
CREATE TABLE categories (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) DEFAULT 'all',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_category (name, type)
) ENGINE=InnoDB;

-- Captchas table
CREATE TABLE captchas (
    id VARCHAR(36) PRIMARY KEY,
    num1 INT NOT NULL,
    num2 INT NOT NULL,
    operator VARCHAR(5) NOT NULL,
    answer INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB;

-- Rate limits table
CREATE TABLE rate_limits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    date DATE NOT NULL,
    count INT DEFAULT 0,
    UNIQUE KEY unique_ip_date (ip_address, date)
) ENGINE=InnoDB;

-- Theme settings table
CREATE TABLE theme_settings (
    id VARCHAR(50) PRIMARY KEY DEFAULT 'global_theme',
    mode ENUM('dark', 'light') DEFAULT 'dark',
    accent_color VARCHAR(20) DEFAULT '#00FF41'
) ENGINE=InnoDB;

-- Site settings table
CREATE TABLE site_settings (
    id VARCHAR(50) PRIMARY KEY DEFAULT 'site_settings',
    daily_submission_limit INT DEFAULT 10,
    top_downloads_enabled TINYINT(1) DEFAULT 1,
    top_downloads_count INT DEFAULT 5,
    sponsored_downloads JSON,
    trending_downloads_enabled TINYINT(1) DEFAULT 0,
    trending_downloads_count INT DEFAULT 5,
    site_name VARCHAR(255) DEFAULT 'DOWNLOAD ZONE',
    site_name_font_family VARCHAR(100) DEFAULT 'JetBrains Mono',
    site_name_font_weight VARCHAR(10) DEFAULT '700',
    site_name_font_color VARCHAR(20) DEFAULT '#00FF41',
    body_font_family VARCHAR(100) DEFAULT 'JetBrains Mono',
    body_font_weight VARCHAR(10) DEFAULT '400',
    footer_enabled TINYINT(1) DEFAULT 1,
    footer_line1_template TEXT,
    footer_line2_template TEXT,
    auto_approve_submissions TINYINT(1) DEFAULT 0,
    recaptcha_site_key VARCHAR(255),
    recaptcha_secret_key VARCHAR(255),
    recaptcha_enable_submit TINYINT(1) DEFAULT 0,
    recaptcha_enable_auth TINYINT(1) DEFAULT 0,
    resend_api_key VARCHAR(255),
    resend_sender_email VARCHAR(255),
    admin_email VARCHAR(255),
    admin_password_hash VARCHAR(255)
) ENGINE=InnoDB;

-- Download activity table (for trending)
CREATE TABLE download_activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    download_id VARCHAR(36) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_download_id (download_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- Sponsored clicks table
CREATE TABLE sponsored_clicks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sponsored_id VARCHAR(36) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sponsored_id (sponsored_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- Password resets table (admin)
CREATE TABLE admin_password_resets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(100) NOT NULL UNIQUE,
    new_password_hash VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    type ENUM('change', 'forgot') DEFAULT 'forgot',
    INDEX idx_token (token),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB;

-- Password resets table (users)
CREATE TABLE user_password_resets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(100) NOT NULL UNIQUE,
    user_id VARCHAR(36) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    INDEX idx_token (token),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB;

-- Insert default settings
INSERT INTO theme_settings (id, mode, accent_color) VALUES ('global_theme', 'dark', '#00FF41');

INSERT INTO site_settings (id, footer_line1_template, footer_line2_template) VALUES (
    'site_settings',
    'For DMCA copyright complaints send an email to {admin_email}.',
    'Copyright © {site_name} {year}. All rights reserved.'
);

-- Insert default categories
INSERT INTO categories (id, name, type) VALUES
(UUID(), 'Action', 'game'), (UUID(), 'RPG', 'game'), (UUID(), 'Strategy', 'game'),
(UUID(), 'FPS', 'game'), (UUID(), 'Racing', 'game'), (UUID(), 'Sports', 'game'),
(UUID(), 'Productivity', 'software'), (UUID(), 'Development', 'software'),
(UUID(), 'Graphics', 'software'), (UUID(), 'Utilities', 'software'),
(UUID(), 'Action', 'movie'), (UUID(), 'Comedy', 'movie'), (UUID(), 'Drama', 'movie'),
(UUID(), 'Sci-Fi', 'movie'), (UUID(), 'Horror', 'movie'), (UUID(), 'Thriller', 'movie'),
(UUID(), 'Drama', 'tv_show'), (UUID(), 'Comedy', 'tv_show'), (UUID(), 'Sci-Fi', 'tv_show'),
(UUID(), 'Crime', 'tv_show'), (UUID(), 'Documentary', 'tv_show');
